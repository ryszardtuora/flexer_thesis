import random
import re
import spacy
from collections import Counter

nlp = spacy.load("pl_nask")
from morf import Morfeusz
nlp.remove_pipe("morfeusz")
nlp.add_pipe("morfeusz_custom")
morf = nlp.get_pipe("morfeusz_custom")

gap_finder = re.compile(r"#([^#:]+)(:[^#]+)?#")
gender_finder = re.compile(r"(?<=:)(m1|m2|m3|f|n)(?=:|\b)")
NOUNS = ["sweter", "bluza", "koszulka", "kimono"]
ADJS = ["czarny", "ekologiczny", "wykonany z wełny"]
PREPS = ["od znanego projektanta", "w stylu sportowym", "na co dzień"]
NUMS = ["trzy", "dwa"]

gap_to_examples = {"NOUN": NOUNS, "ADJ": ADJS, "PREP": PREPS, "NUM": NUMS}
product_phrase = "#NOUN# #PREP:gen# #PREP#"
product_phrase = "#ADJ# #NOUN# #PREP#"

def fill_template(input_template):
    matches = list(gap_finder.finditer(input_template))
    gap_types = Counter([m.groups()[0] for m in matches])
    fillings = {gap_type: random.sample(gap_to_examples[gap_type], k) for gap_type, k in gap_types.items()}
    filled_template = input_template
    for m in matches[::-1]:
        start, end = m.span()
        gap_type, inflection_pattern = m.groups()
        filling = fillings[gap_type].pop()
        if inflection_pattern:
            filling = morf.flex(nlp(filling), inflection_pattern.strip(":"))
        filled_template = filled_template[:start] + filling + filled_template[end:]
    return filled_template

for i in range(20):
    base = fill_template("#NOUN#")
    gender = gender_finder.search(nlp(base)[0].tag_).group(0)
    intermediate_template = fill_template(f"#ADJ:{gender}# {base} #PREP#")
    inflected_template = morf.flex(nlp(intermediate_template), "pl")
    intermediate_template = fill_template(f"#NUM# {inflected_template}")
    inflected_argument = morf.flex(nlp(intermediate_template), "loc")
    output = f"Myślę o {inflected_argument}"
    print(output)


def fill_single_template(template, filling):
    gap = gap_finder.search(template)
    target_feats = gap.groups()[1].strip(":")
    start, end = gap.span()
    doc = nlp(filling)
    inflected_filling = morf.flex(doc, target_feats)
    filled_template = template[:start] + inflected_filling + template[end:]
    return filled_template

doc = nlp("Na co dzień jeżdżę samochodem.")
gap_index = -2
tag = doc[gap_index].tag_
pos, feats = tag.split(":", 1)
template = doc[:gap_index].text + f" #{feats}#" + doc[gap_index + 1:].text
fillings = ["motor", "samochód po dziadku", "powóz konnnym", "biały sedan", "miejski autobus lub tramwaj"]
for filling in fillings:
    print(fill_single_template(template, filling))

