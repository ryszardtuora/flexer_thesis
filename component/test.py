import unittest
import spacy
import morfeusz2
from functools import lru_cache
nlp = spacy.load("pl_nask")

from morf import Morfeusz
nlp.remove_pipe("morfeusz")
nlp.add_pipe("morfeusz_custom")
morfeusz = nlp.get_pipe("morfeusz_custom")
flexer = morfeusz._flexer


@lru_cache(100)
def process_phrase(string):
    doc = nlp(string)
    return doc

def verify_inflection(test_instance, base, morphology, gold):
    doc = process_phrase(base)
    out = morfeusz.flex(doc, morphology)
    try:
        test_instance.assertEqual(out, gold)
    except AssertionError:
        for tok in doc:
            print(f"{tok.i}\t{tok.orth_}\t{tok.tag_}\t{tok.dep_}\t{tok.head.i}")
        print("\n\n")
        raise AssertionError 


class TestNamedEntityInflections(unittest.TestCase):
    NER_tests = [("Uniwersytet Papieski", "gen", "Uniwersytetu Papieskiego"),
                 ("Uniwersytet Papieski im. Jana Pawła II", "gen", "Uniwersytetu Papieskiego im. Jana Pawła II"),
                 ("Maciej Kowalski", "dat:pl", "Maciejom Kowalskim"),
                 ("Anna Komorowska-Zielińska", "gen", "Anny Komorowskiej-Zielińskiej"),
                 ("Kalwaria Zebrzydowska", "dat", "Kalwarii Zebrzydowskiej"),
                 ("Królowa Elżbieta II", "inst", "Królową Elżbietą II"),
                 ("Królowa Elżbieta druga", "inst", "Królową Elżbietą drugą"),
                 ("PZPR", "dat", "PZPR-owi"),
                 ("PZPR", "nom", "PZPR"),
                 ("Góry Błękitne", "gen", "Gór Błękitnych"),
                 ("siódmy stycznia", "inst", "siódmym stycznia"),
                 ("godzina piętnasta", "pl:dat", "godzinom piętnastym"),
                 ("Polskie Górnictwo Gazowe i Naftownictwo", "inst", "Polskim Górnictwem Gazowym i Naftownictwem"),
                 ("Wydział Dziennikarstwa i Nauk Politycznych UW", "dat", "Wydziałowi Dziennikarstwa i Nauk Politycznych UW"),
                 ("Wojewódzki Ośrodek Ruchu Drogowego", "pl:gen", "Wojewódzkich Ośrodków Ruchu Drogowego")
                 ]
    def test_NER(self):
        for NER_test in self.NER_tests:
            with self.subTest(NER_test):
                verify_inflection(self, *NER_test)


class TestNominalPhraseInflections(unittest.TestCase):
    nominal_tests = [("swoje własne dzieci", "gen:sg", "swego własnego dziecka"),
                     ("biała flaga z papieru", "gen:pl", "białych flag z papieru"),
                     ("biała jak sól, flaga z szorstkiego płótna", "pl:dat", "białym jak sól, flagom z szorstkiego płótna")
                     ]

    def test_nominal(self):
        for nominal_test in self.nominal_tests:
            with self.subTest(nominal_test):
                verify_inflection(self, *nominal_test)


class TestNumeralPhrases(unittest.TestCase):
    numeral_tests = [("połowa kilograma", "gen", "połowy kilograma"),
                     ("dwoje dzieci", "inst", "dwoma dziećmi"),
                     ("troje oczu", "inst", "trzema oczami"),
                     ("czworo młodych uszu", "loc", "czworgu młodych uszach"),
                     ("dziesięcioro skrzypiec", "loc", "dziesięciu skrzypcach"),
                     ("3 świnie", "loc", "3 świniach"),
                     ("cztery ściany", "dat", "czterem ścianom"),
                     ("trzy i pół tysiąca", "gen", "trzech i pół tysiąca"),
                     ("drzewa i dwoje małych dzieci", "dat", "drzewom i dwojgu małym dzieciom"),
                     ("trzy małe świnki", "dat", "trzem małym świnkom"),
                     ("sześć kwadratów i trójkątów", "loc", "sześciu kwadratach i trójkątach"),
                     ("sześć małych i złotych łańcuszków", "dat", "sześciu małym i złotym łańcuszkom"),
                     ("sto psów", "dat", "stu psom"),
                     ("milion złotych", "inst", "milionem złotych"),
                     ("jeden głupi wyraz", "loc", "jednym głupim wyrazie"),
                     ("pięciu łysych mężczyzn", "inst", "pięcioma łysymi mężczyznami")
            ]

    def test_numeral(self):
        for numeral_test in self.numeral_tests:
            with self.subTest(numeral_test):
                verify_inflection(self, *numeral_test)



class TestAdjectivalPhrases(unittest.TestCase):
    adjectival_tests = [("wysokiemu i czarno-zielonemu", "gen:pl", "wysokich i czarno-zielonych"),
                        ("biały jak kreda", "com", "bielszy jak kreda"),
                        ("biały i gładki", "sup:f", "najbielsza i najgładsza"),
            ]

    def test_adjectival(self):
        for adjectival_test in self.adjectival_tests:
            with self.subTest(adjectival_test):
                verify_inflection(self, *adjectival_test)


class TestCoordinations(unittest.TestCase):
    coordination_tests = [("pieprz, sól i mąka", "gen", "pieprzu, soli i mąki"),
                          ("kraina mlekiem i miodem płynąca", "pl:dat", "krainom mlekiem i miodem płynącym"),
                          ("czarny chleb i czarna kawa", "inst", "czarnym chlebem i czarną kawą"),
            ]

    def test_coordination(self):
        for coordination_test in self.coordination_tests:
            with self.subTest(coordination_test):
                verify_inflection(self, *coordination_test)



class TestPOSBoundaryInflections(unittest.TestCase):
    transgressive_tests = [("patrzeć", "ger", "patrzenie"),
                           ("zabijać", "ger:dat", "zabijaniu"),
                           ("zabijać", "ppas", "zabijany"),
                           ("zabijacie", "impt", "zabijajcie"),
                           ("zabijać", "impt:pl:pri", "zabijajmy"),
                           ("zabijać", "ppas:neg", "niezabijany"),
                           ("profesorowie", "depr", "profesory"),
                           ("biały", "adja", "biało"),
                           ("biały", "adjp", "biała"),
                           ]

    def test_transgressive(self):
        for transgressive_test in self.transgressive_tests:
            with self.subTest(transgressive_test):
                verify_inflection(self, *transgressive_test)


class TestIndividualWordInflections(unittest.TestCase):
    noun_tests = [("pies", "gen", "psa"),
                  ("człowiek", "pl", "ludzie"),
                  ("sitko", "inst", "sitkiem"),
                  ("widły", "acc", "widły"),
                  ("widły", "pl:inst", "widłami"),
                  ("czeluść", "dat", "czeluści"),
                  ("świece", "dat:sg", "świecy"),
                  ("psom", "sg", "psu"),
                 ]

    adj_tests = [("piękny", "gen", "pięknego"),
                 ("zły", "pl", "źli"),
                 ("zwykły", "f", "zwykła"),
                 ("zwykłego", "f", "zwykłej"),
                 ("jasny", "f:pl:gen", "jasnych"),
                 ("ciemny", "f:pl:acc", "ciemne"),
                 ("białych", "sg:m3:acc", "biały"),
                 ("biała", "pl:m1", "biali"),
                 ("biała", "pl:m3", "białe"),
                 ("biała", "sup", "najbielsza"),
                ]

    participle_tests = [("biegnący", "pl:gen", "biegnących"),
                        ("stojący", "f:neg:pl:dat", "niestojącym"),
                        ("stojący", "f:neg:pl:dat", "niestojącym"),
                        ]

    gerund_tests = [("widzenie", "pl", "widzenia"),
                    ("widzenie", "neg", "niewidzenie"),
                    ("oddychanie", "dat", "oddychaniu"),
                    ]

    verb_tests = [
                  ("widzę", "pl", "widzimy"),
                  ("widzę", "ter", "widzi"),
                  ("widzę", "sec:pl", "widzicie"),
                  ("leczy", "pl", "leczą"),
                  ("leczy", "pl:sec", "leczycie"),
                  ("leczył", "f", "leczyła"),
                  ]

    def test_noun(self):
        for noun_test in self.noun_tests:
            with self.subTest(noun_test):
                verify_inflection(self, *noun_test)

    def test_adj(self):
        for adj_test in self.adj_tests:
            with self.subTest(adj_test):
                verify_inflection(self, *adj_test)

    def test_participle(self):
        for participle_test in self.participle_tests:
            with self.subTest(participle_test):
                verify_inflection(self, *participle_test)

    def test_gerund(self):
        for gerund_test in self.gerund_tests:
            with self.subTest(gerund_test):
                verify_inflection(self, *gerund_test)

    def test_verb(self):
        for verb_test in self.verb_tests:
            with self.subTest(verb_test):
                verify_inflection(self, *verb_test)



if __name__ == '__main__':
    unittest.main()
