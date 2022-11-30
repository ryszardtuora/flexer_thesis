def flex_subtree(head, target_feats):
    ind_to_inflected = {} # the output is stored in a dict with token positions as keys
    children_to_inflect = list(head.children) # using the dependency tree annotated by spaCy
    inflected_head = flex_token(head, target_feats) # a wrapper for one of the single-word inflection methods
    ind_to_inflected[head.i] = inflected_head
    for child in children_to_inflect:
        accommodable_feats = filter_accommodable_feats(child, target_feats) # filtering the features by the rules induced
        inflected_subtree = flex_subtree(child, accommodable_feats) #recurrence
        ind_to_inflected.update(inflected_subtree)
    return ind_to_inflected
