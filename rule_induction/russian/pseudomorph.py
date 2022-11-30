import pandas
from tqdm import tqdm

class PseudoMorph():
    def __init__(self):
        df = pandas.read_csv("ru.tab", sep="\t", header=None)
        self.lemma_to_forms = {lemma: [] for lemma in df[1].value_counts().keys()}
        for row in tqdm(df.iloc):
            self.lemma_to_forms[row[1]].append((row[0], row[2], row[3]))

    def generate(self, lemma):
        if lemma in self.lemma_to_forms:
            forms = self.lemma_to_forms[lemma]
            out = []
            for form, pos, feats in forms:
                full_tag = "|".join([pos, feats])
                out.append((form, lemma, full_tag))
            return out
        else:
            return []



