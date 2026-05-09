import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def normalize(word: str) -> str:
    return morph.parse(word)[0].normal_form


def normalize_text(text: str) -> list[str]:
    return [normalize(w) for w in text.lower().split()]