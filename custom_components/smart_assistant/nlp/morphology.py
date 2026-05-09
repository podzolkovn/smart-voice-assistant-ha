import pymorphy2

_morph = None


def get_morph():
    global _morph
    if _morph is None:
        _morph = pymorphy2.MorphAnalyzer()
    return _morph


def normalize(word: str) -> str:
    return get_morph().parse(word)[0].normal_form


def normalize_text(text: str) -> list[str]:
    return [normalize(w) for w in text.lower().split()]