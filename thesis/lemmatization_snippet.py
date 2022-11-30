def lemmatize_subtree(head):
    ind_to_lemmatized = {}
    children_to_lemmatize = list(head.children)
    target_feats = self.get_lemma_alterations(head)# recording all the morphological features that need to be changed to convert the input form into the lemma
    ind_to_lemmatized[head.i] = lemmatized_head
    lemmatized_head = self.flex_token(head, target_feats)
    for child in children_to_lemmatize:
        accommodable_feats = filter_accommodable_feats(child, target_feats)
        lemmatized_subtree = flex_subtree(child, accommodable_feats)
        ind_to_lemmatized.update(lemmatized_subtree)
    return ind_to_lemmatized
