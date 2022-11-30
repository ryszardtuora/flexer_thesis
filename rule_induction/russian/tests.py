import spacy
from morf import Morfeusz

nlp = spacy.load("ru_core_news_lg")
morf = Morfeusz()

examples = [
            ("абсолютным падежом", "абсолютный падеж", "Case=Ins|Number=Sing"),
            ("активному словарному запасу", "активный словарный запас", "Case=Dat|Number=Sing"),
            ("антенне радиолокационного дальномера", "антенна радиолокационного дальномера", "Case=Loc|Number=Sing"),
            ("браков по договорённости", "брак по договорённости", "Case=Gen|Number=Plur"),
            ("бурями в стакане воды", "буря в стакане воды", "Case=Ins|Number=Plur"),
            ("физике элементарных частиц", "физика элементарных частиц", "Case=Loc|Number=Sing"),
            ("гражданской войне в США", "гражданская война в США", "Case=Dat|Number=Sing"),
            ("книгами за семью печатями", "книга за семью печатями", "Case=Ins|Number=Plur"),
            ("компенсационного натяжного колеса", "компенсационное натяжное колесо", "Case=Gen|Number=Sing"),
            ("многоразовым транспортным космическим кораблям", "многоразовый транспортный космический корабль", "Case=Dat|Number=Plur"),
            ("натяжном колесе гусеницы", "натяжное колесо гусеницы", "Case=Loc|Number=Sing"),
            ]

for form, base, tag in examples:
    out = morf.flex(nlp(base), tag)
    print(base, tag, form, out, form == out)
