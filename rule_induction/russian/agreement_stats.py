import os
import pandas
import json
import conllu
from collections import defaultdict
from tqdm import tqdm


with open("ru_morph.json") as f:
    morph = json.load(f)
attr2vals = morph["ATTR2VALS"]
val2attr = morph["VAL2ATTR"]

max_docs = 1000000
def generate_tables(docs):
    dictinitializer = lambda : defaultdict(lambda : 0)
    agreement_table = defaultdict(dictinitializer)
    cooccurence_table = defaultdict(dictinitializer)
    doc_counter = 0
    for doc in tqdm(docs):
        doc_counter +=1
        if doc_counter > max_docs:
            break
        toks_dict = {tok["id"]: tok for tok in doc}
        # calculating the child-head agreement statistics
        for tok in doc:
            deprel = tok["deprel"]
            if deprel == "root": # root has no head to agree with
                continue
            feats = tok["feats"]
            if feats is None:
                continue
            head_position = tok["head"]
            head_feats = toks_dict[head_position]["feats"]
            if head_feats is None:
                continue
            for attr, feat in feats.items():
                possible_vals = attr2vals[attr]
                if any([hf in possible_vals for hf in head_feats.values()]):# we take into account only those pairs, in which both elements do have a value for a given attribute
                    cooccurence_table[deprel][attr] += 1
                    if feat in head_feats.values():
                        agreement_table[deprel][attr] += 1
    breakpoint()
    return agreement_table, cooccurence_table

def generate_table():
    with open("nerus_lenta.conllu") as f:
        doc_generator = conllu.parse_incr(f)
        agreement_table, cooccurence_table = generate_tables(doc_generator)

    def calculate_agreement(deprel, attribute):
        cooccurence = cooccurence_table[deprel][attribute]
        agreement = agreement_table[deprel][attribute]
        agreement_percentage = round((agreement * 100) / cooccurence, 2)
        return agreement_percentage

    data_table = {
                  deprel: {
                           attribute: calculate_agreement(deprel, attribute)
                           for attribute in agreement_table[deprel]
                          }
                  for deprel in agreement_table
                 }
    return data_table

def process_table(data_table):
    df = pandas.DataFrame(data_table).T.sort_index()
    df.to_csv("agreement_stats.csv", sep="\t")
    THRESHOLD = 95
    selected = df[df>THRESHOLD].T.to_dict()
    rules = {deprel:[] for deprel in selected}
    for deprel in selected:
        for attr in selected[deprel]:
            if selected[deprel][attr] > THRESHOLD:
                rules[deprel].append(attr)

    rules = {k:v for k,v in rules.items() if v != []}
    with open("rules_induced.json", "w") as f:
        json.dump(rules, f, indent=2)


if __name__ == "__main__":
    data_table = generate_table()
    process_table(data_table)
    

