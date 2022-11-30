import spacy
import json
from pathlib import Path
from spacy.tokens import Token
from spacy.tokens import Span
from pseudomorph import PseudoMorph


class Morfeusz():
    def __init__(self):
        self._flexer = Flexer(self)
        self.morf = PseudoMorph()


    def tag_distance(self, tag1, tag2):
        feats1 = set(tag1)
        feats2 = set(tag2)
        dist = len(feats1.symmetric_difference(feats2))
        return dist


    def generate(self, lemma):
        generated = self.morf.generate(lemma)
        processed = [{"form": g[0], "full_tag": g[2]} for g in generated]
        return processed


    def flex(self, to_inflect, target_feats):
        if isinstance(to_inflect, Token):
            return self._flexer.flex_token(to_inflect, target_feats).strip()

        try:
            _ = to_inflect[0]
        except TypeError:
            raise TypeError("Supplied argument must be either a span, token, or a list of tokens.")

        if isinstance(to_inflect, Span):
            to_inflect = list(to_inflect)
        if not all([isinstance(tok, Token) for tok in to_inflect]):
            raise TypeError("Supplied argument must be either a span, token, or a list of tokens.")

        inflected = self._flexer.flex_tokens(to_inflect, target_feats).strip()
        return inflected


    def lemmatize(self, to_lemmatize):
        try:
            _ = to_lemmatize[0]
        except TypeError:
            raise TypeError("Supplied argument must be either a span, token, or a list of tokens.")

        if isinstance(to_lemmatize, Span):
            to_lemmatize = list(to_lemmatize)

        if not all([isinstance(tok, Token) for tok in to_lemmatize]):
            raise ValueError("Supplied argument must be either a span, token, or a list of tokens.")

        lemmatized = self._flexer.lemmatize_tokens(to_lemmatize).strip()
        return lemmatized



MORPHOLOGY_FILE = "ru_morph.json"
# we use rules induced from PDB as opposed to NKJP, as these seem more reasonable

class Flexer():
    def __init__(self, morf_component):
        self.morf_component = morf_component
        data = self.load_morphology()
        self.default_vals = data["DEFAULT_VALS"]
        self.attr2feats = data["ATTR2FEATS"]
        self.val2attr = data["VAL2ATTR"]
        self.pos2lemma_tags = data["POS2LEMMA_TAGS"]
        self.force_feats = data["FORCE_FEATS"]
        # a list of deprels with inverted dependency structure (i.e. governing children)
        self.accomodation_rules = data["ACCOMODATION_RULES"]
        # A deprel -> agreement attrs dict

    def load_morphology(self):
        data_path = "ru_morph.json"
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        return data


    def get_case_fun(self, token_string):
        if token_string.isupper():
            def case_fun(s):
                split_string = s.split("-", 1)
                first_part = split_string[0]
                return "-".join([first_part.upper()] + split_string[1:])

        elif token_string.islower():
            case_fun = lambda s: s.lower()
        elif token_string.istitle():
            case_fun = lambda s: s.capitalize()
        else:
            case_fun = lambda s: s
        return case_fun


    def tag_to_feats(self, tag_string, keep_pos=False, enrich=False):
        split_tag = tag_string.split("|")
        if enrich:
            filled_attrs = [self.val2attr[val] for val in split_tag[1:]]
            unfilled_attrs = [attr for attr in self.attr2feats if attr not in filled_attrs]
            split_tag = split_tag + [self.default_vals[attr] for attr in unfilled_attrs if self.default_vals[attr]]
        if not keep_pos:
            split_tag = split_tag[1:]
        return set(split_tag)


    def dict_flex(self, lemma, current_tag, target_feats):
        target_feat_set = set(target_feats.split("|"))
        lexeme = self.morf_component.generate(lemma)
        current_feats = self.tag_to_feats(current_tag, keep_pos=True, enrich=True)
        candidates = []
        for form in lexeme:
            form["feats"] = self.tag_to_feats(form["full_tag"], keep_pos=True, enrich=True)
            if target_feat_set.issubset(form["feats"]):
                form["score"] = len(current_feats.symmetric_difference(form["feats"]))
                candidates.append(form)
        if not candidates:
            return None
        ranking = sorted(candidates, key=lambda form:form["score"])
        inflected_form = ranking[0]["form"]
        return inflected_form


    def token_to_tag(self, token):
        pos = token.pos_
        feats = str(token.morph)
        tag = "|".join([pos, feats])
        return tag


    def flex_token(self, token, target_feats):
        token_string = token.orth_
        case_fun = self.get_case_fun(token_string)

        if target_feats in ["", None]:
            inflected_form = token.orth_
        else:
            lemma = token.lemma_
            current_tag = self.token_to_tag(token)
            inflected_form = self.dict_flex(lemma, current_tag, target_feats)
            if inflected_form is None:
                inflected_form = token.orth_

        inflected = case_fun(inflected_form) + token.whitespace_
        return inflected


    def filter_accomodable_feats(self, child, target_child_feats):
        if not target_child_feats:
            return ""
        target_child_feats = target_child_feats.split("|")
        child_deprel = child.dep_
        if child_deprel in self.accomodation_rules:
            accomodable_attrs = self.accomodation_rules[child_deprel]
        else:
            accomodable_attrs = []
        accomodable_feats = [feat for feat in target_child_feats if self.val2attr[feat] in accomodable_attrs]
        if child_deprel in self.force_feats:
            forced_attrs = self.force_feats[child_deprel].keys()
            accomodable_feats = [feat for feat in accomodable_feats if self.val2attr[feat] not in forced_attrs]
            for attr in forced_attrs:
                accomodable_feats.append(self.force_feats[child_deprel][attr])
        return "|".join(accomodable_feats)


    def flex_subtree(self, head, target_feats):
        ind_to_inflected = {}
        children_to_inflect = list(head.children)
        inflected_head = self.flex_token(head, target_feats)
        ind_to_inflected[head.i] = inflected_head
        for child in children_to_inflect:
            accomodable_feats = self.filter_accomodable_feats(child, target_feats)
            inflected_subtree = self.flex_subtree(child, accomodable_feats)
            ind_to_inflected.update(inflected_subtree)
        return ind_to_inflected


    def flex_tokens(self, tokens, target_feats):
        ind_to_inflected = {}
        independent_subtrees = [tok for tok in tokens if tok.head not in tokens or tok.head == tok]
        for independent_head in independent_subtrees:
            ind_to_inflected.update(self.flex_subtree(independent_head, target_feats))
        token_inds = [tok.i for tok in tokens]
        inflected_seq = sorted([(i, tok) for i, tok in ind_to_inflected.items() if i in token_inds])
        # we restrict the inflected tokens, to ones in the original list
        inflected_string = "".join([tok for i, tok in inflected_seq])
        return inflected_string


    def get_lemma_alterations(self, head):
        lemma = head.lemma_
        tag = self.token_to_tag(head)
        split_tag = tag.split("|")
        pos = split_tag[0]
        feats = set(split_tag)
        if pos not in self.pos2lemma_tags:
            return ""
        lemma_tags = [lt.split("|") for lt in self.pos2lemma_tags[pos]]
        ranking = [(lt, len(feats.symmetric_difference(set(lt)))) for lt in lemma_tags]
        top_lemma_tag = sorted(ranking, key=lambda x: x[1])[0][0]
        alterations = [feat for feat in top_lemma_tag if feat not in feats]
        print(head, alterations)
        return "|".join(alterations)


    def lemmatize_subtree(self, head):
        # The algorithm recurrently goes through each child and inflects it into the pattern
        # corresponding to the base form of the head of the phrase.
        ind_to_lemmatized = {}
        children_to_lemmatize = list(head.children)
        target_feats = self.get_lemma_alterations(head)
        lemmatized_head = self.flex_token(head, target_feats)
        ind_to_lemmatized[head.i] = lemmatized_head
        for child in children_to_lemmatize:
            accomodable_feats = self.filter_accomodable_feats(child, target_feats)
            lemmatized_subtree = self.flex_subtree(child, accomodable_feats)
            ind_to_lemmatized.update(lemmatized_subtree)
        return ind_to_lemmatized


    def lemmatize_tokens(self, tokens):
        ind_to_lemmatized = {}
        independent_subtrees = [tok for tok in tokens if tok.head not in tokens or tok.head == tok]
        for independent_head in independent_subtrees:
            ind_to_lemmatized.update(self.lemmatize_subtree(independent_head))
        token_inds = [tok.i for tok in tokens]
        lemmatized_seq = sorted([(i, tok) for i, tok in ind_to_lemmatized.items() if i in token_inds])
        # we restrict the lemmatized tokens, to ones in the original list
        lemmatized_string = "".join([tok for i, tok in lemmatized_seq])
        return lemmatized_string


