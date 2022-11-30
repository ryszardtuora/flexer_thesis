import os
import pandas
import json
import conllu
from collections import defaultdict


attr2vals = {
    "person": ['ter', 'sec', 'pri'],
    "case": ['nom', 'acc','dat', 'gen', 'inst', 'loc', 'voc'],
    "gender": ['f', 'm1', 'm2', 'm3', 'n'],
    "negation": ['aff', 'neg'],
    "number": ['sg', 'pl'],
    "degree": ['pos', 'com', 'sup'],
    "aspect": ['perf', 'imperf'],
    "prepositionality": ['npraep', 'praep'],
    "accomodability": ['congr', 'rec'],
    "accentibility": ['akc', 'nakc'],
    "agglutination": ['agl', 'nagl'],
    "vocality": ['nwok', 'wok'],
    "fullstoppedness": ['npun', 'pun'],
    "collectivity": ['col', 'ncol', 'pt'],
}

val2attr = {}
for attr in attr2vals:
    for val in attr2vals[attr]:
        val2attr[val]=attr

def get_docs():
    docs = []
    PDB_FOLDER = "UD_Polish-PDB-master"
    conllufiles = [f for f in os.listdir(PDB_FOLDER) if f.endswith(".conllu")]
    for conllufile in conllufiles:
        conllupath = os.path.join(PDB_FOLDER, conllufile)
        with open(conllupath, encoding="utf-8") as f:
            txt = f.read()
        docs.extend(conllu.parse(txt))
    return docs

def generate_tables(docs):
    dictinitializer = lambda : defaultdict(lambda : 0)
    agreement_table = defaultdict(dictinitializer)
    cooccurence_table = defaultdict(dictinitializer)
    for doc in docs:
        # clearing multitoken annotations
        to_clear = []
        for tok in doc:
            if type(tok["id"]) != int:
                to_clear.append(tok)
            if tok["xpos"]:
                tok["xpos"] = tok["xpos"].replace(":pt", ":col") # pt is equivalent to col for purposes of accomodation
        for tok in to_clear:
            doc.remove(tok)
        toks_dict = {tok["id"]: tok for tok in doc}
        # calculating the child-head agreement statistics
        for tok in doc:
            deprel = tok["deprel"]
            if deprel == "root": # root has no head to agree with
                continue
            feats = tok["xpos"].split(":")[1:]
            head_position = tok["head"]
            head_feats = toks_dict[head_position]["xpos"].split(":")[1:]
            for feat in feats:
                if feat in ["nol"]: # nol is not supported by morfeusz
                    continue
                attr = val2attr[feat] # translating values into attributes for which they are defined
                possible_vals = attr2vals[attr]
                if any([hf in possible_vals for hf in head_feats]):# we take into account only those pairs, in which both elements do have a value for a given attribute
                    cooccurence_table[deprel][attr] += 1
                    if feat in head_feats:
                        agreement_table[deprel][attr] += 1
    return agreement_table, cooccurence_table

def generate_table():
    docs = get_docs()
    agreement_table, cooccurence_table = generate_tables(docs)

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
    

