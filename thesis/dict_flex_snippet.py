def tag_to_feats(tag_string, keep_pos=False, enrich=False):
    split_tag = tag_string.split(":")
    if enrich:
        # finding unfilled attributes and assigning default values to them, based on the dict objects representing the tagset
        filled_attrs = [VAL2ATTR[val] for val in split_tag[1:]]
        unfilled_attrs = [attr for attr in ATTR2FEATS if attr not in filled_attrs]
        split_tag = split_tag + [DEFAULT_VALS[attr] for attr in unfilled_attrs]
    if not keep_pos:
        split_tag = split_tag[1:]
    return set(split_tag)

def dict_flex(lemma, current_tag, target_feats):
    target_feat_set = set(target_feats.split(":"))
    lexeme = morf.generate(lemma) # generating all forms of the lexeme using Morfeusz2
    current_feats = tag_to_feats(current_tag, keep_pos=True,
                                 enrich=True)
    candidates = []
    for form in lexeme:
        form["feats"] = tag_to_feats(form["full_tag"],
                                     keep_pos=True,
                                     enrich=True)
        if target_feat_set.issubset(form["feats"]):
            form["score"] = len(current_feats.symmetric_difference(form["feats"]))
            candidates.append(form)
    if not candidates:
        return None # no satisfactory form found
    ranking = sorted(candidates, key=lambda form:form["score"])
    inflected_form = ranking[0]["form"]
    return inflected_form

dict_flex("dobremu", "adj:dat:sg:m1", "pl:acc") # -> dobrych
