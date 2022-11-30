def fill_single_template(template, filling):
    gap = gap_finder.search(template)
    target_feats = gap.groups()[1].strip(":")
    start, end = gap.span()
    doc = nlp(filling)
    inflected_filling = morf.flex(doc, target_feats)
    filled_template = template[:start] + inflected_filling + template[end:]
    return filled_template
    
doc = nlp("Na co dzień jeżdżę samochodem.")
gap_index = -2 # the gap token can be singled out using different means, e.g. its deprel
tag = doc[gap_index].tag_
pos, feats = tag.split(":", 1)
template = doc[:gap_index].text + f" #{feats}#" + doc[gap_index + 1:].text
fillings = ["motor", "samochód po dziadku", "powóz konnnym", "biały sedan", "miejski autobus lub tramwaj"]
for filling in fillings:
    print(fill_single_template(template, filling))

"Na co dzień jeżdżę motorem."
"Na co dzień jeżdżę samochodem po dziadku."
"Na co dzień jeżdżę powozem konnnym."
"Na co dzień jeżdżę białym sedanem."
"Na co dzień jeżdżę miejskim autobusem lub tramwajem."
