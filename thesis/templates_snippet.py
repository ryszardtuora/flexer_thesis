import random
import re
import spacy
from collections import Counter

nlp = spacy.load("pl_nask")
morf = nlp.get_pipe("morfeusz")
gap_finder = re.compile(r"#([^#:]+)(:[^#]+)?#")
gender_finder = re.compile(r"(?<=:)(m1|m2|m3|f|n)(?=:|\b)")
NOUNS = ["sweter", "bluza", "koszulka", "kimono"]
ADJS = ["czarny", "ekologiczny", "wykonany z wełny"]
PREPS = ["od znanego projektanta", "w stylu sportowym", "na co dzień"]
NUMS = ["trzy", "dwa"]
gap_to_examples = {"NOUN": NOUNS, "ADJ": ADJS, "PREP": PREPS, "NUM": NUMS}

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
