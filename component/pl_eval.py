import random
import json
from tqdm import tqdm
from collections import Counter
from pandas import DataFrame

import spacy
import morfeusz2
nlp = spacy.load("pl_nask")

from morf import Morfeusz
nlp.remove_pipe("morfeusz")
nlp.add_pipe("morfeusz_custom")
morfeusz = nlp.get_pipe("morfeusz_custom")
flexer = morfeusz._flexer


random.seed(42)

def load_data(phrases_file, inflection_dict=None):
    data = []
    with open(phrases_file) as f:
        lines = f.read()
    for line in lines.split("\n")[:-1]:
        form, lemma, full_tag = line.split("\t")
        split_tag = full_tag.split(":", 1)
        pos_tag = split_tag[0]
        if len(split_tag)>1:
            feats = split_tag[1]
        else:
            feats = ""
        base_words = lemma.split(" ")
        if inflection_dict is None or all([inflection_dict.analyse(bw) for bw in base_words]):
            data.append((form, lemma, pos_tag, feats))
    random.shuffle(data)
    return data

def evaluate_flexer(data):
  output = []
  base_docs = nlp.pipe([d[1] for d in data])
  for (orth, base, pos, morph), doc in tqdm(zip(data, base_docs)):
    base_tokens = nlp(base)
    flexed = morfeusz.flex(base_tokens, morph).lower()
    concat_inflected = " ".join([morfeusz.flex(tok, morph).lower() for tok in base_tokens])
    row = {}
    row["base"] = base
    row["structure"] = ",".join([t.tag_ for t in base_tokens])
    row["orth"] = orth
    row["target"] = morph
    row["length"] = len(base_tokens)
    row["flexed"] = flexed
    row["exact"] = flexed == orth.lower()
    row["permuted"] = set(flexed.split()) == set(orth.lower().split())
    row["baseline"] = set(base.lower().split()) == set(orth.lower().split())
    row["concat_inflected"] = set(concat_inflected.split()) == set(orth.lower().split())
    output.append(row)
  return output

def evaluate_lemmatizer(data):
  output = []
  base_docs = nlp.pipe([d[1] for d in data])
  orth_docs = nlp.pipe([d[0] for d in data])
  docs = zip(base_docs, orth_docs)
  for (orth, base, pos, morph), (base_tokens, orth_tokens) in tqdm(zip(data, docs)):
    #base_tokens = nlp(base)
    #orth_tokens = nlp(orth)

    # filtering deviant cases
    head_tok = [tok for tok in base_tokens if tok.dep_ == "ROOT"][0]
    # base plural
    if "pl" in head_tok.tag_.split(":"):
        continue

    # lemmatization into an infinitive
    #if head_tok.tag_.split(":")[0] in ["ppas", "pact", "pcon", "pant", "ger"]:
    #    continue

    lemmatized = morfeusz.lemmatize(orth_tokens).lower()
    lemmatized_concat = " ".join([t.lemma_ for t in orth_tokens]).lower()
    row = {}
    row["base"] = base
    #row["structure"] = ",".join([f"{t.pos_tag}:{t.feats}" for t in base_tokens])
    row["orth"] = orth
    row["length"] = len(base_tokens)
    row["lemmatized"] = lemmatized
    row["exact"] = lemmatized == base.lower()
    row["permuted"] = set(lemmatized.split()) == set(base.lower().split())
    # concatenation-of-lemmas baseline
    row["concat_exact"] = lemmatized_concat == base.lower()
    row["concat_permuted"] = set(lemmatized_concat.split()) == set(base.lower().split())
    output.append(row)
  return output

data = load_data("pl_phrases.tab")
test_ex = data
print(len(data))


test_ex = data

flex_output = evaluate_flexer(test_ex)
flex_df = DataFrame(flex_output)
flex_df.to_csv("pl_flex_out_dict.tsv", sep="\t")
print("Inflection: ", sum(flex_df["permuted"])/len(flex_df) * 100)

lem_output = evaluate_lemmatizer(test_ex)
lem_df = DataFrame(lem_output)
lem_df.to_csv("pl_lem_out_dict.tsv", sep="\t")
print("Lemmatization: ", sum(lem_df["permuted"])/len(lem_df) * 100)
print("Lemmatization baseline:", sum(lem_df["concat_permuted"])/len(lem_df) * 100)
