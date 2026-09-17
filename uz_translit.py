"""
Foydalanuvchi lotin yozuvida yozgan o'zbekcha matnni Kirill alifbosiga va
aksincha, Kirill yozuvidagi matnni lotin alifbosiga avtomatik o'giradigan
modul.

Foydalanuvchi boshida qaysi til/skriptni tanlagan bo'lsa (o'zbekcha-kirill,
o'zbekcha-lotin yoki ruscha), bot javoblarni o'sha skriptga moslab saqlaydi.
Agar matnda allaqachon kerakli alifbo bo'lsa, o'sha qism o'zgartirilmaydi —
bu aralash matnlarda (raqamlar, qisqartmalar bilan) xavfsiz ishlaydi.
"""

import re

# ==================== Lotin -> Kirill ====================

_LAT_DIGRAPHS = [
    ("yo", "ё"),
    ("yu", "ю"),
    ("ya", "я"),
    ("sh", "ш"),
    ("ch", "ч"),
    ("o'", "ў"), ("oʻ", "ў"), ("oʼ", "ў"), ("o’", "ў"), ("o‘", "ў"), ("o`", "ў"),
    ("g'", "ғ"), ("gʻ", "ғ"), ("gʼ", "ғ"), ("g’", "ғ"), ("g‘", "ғ"), ("g`", "ғ"),
]
_LAT_DIGRAPHS.sort(key=lambda pair: -len(pair[0]))

_LAT_SINGLE_MAP = {
    "a": "а", "b": "б", "d": "д", "f": "ф", "g": "г", "h": "ҳ", "i": "и",
    "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х",
    "y": "й", "z": "з", "c": "с",
}

_APOSTROPHES = {"'", "ʼ", "‘", "’", "`", "ʻ"}
_LAT_VOWELS = set("aeiou")

_LATIN_WORD_RE = re.compile(r"[A-Za-zʻʼ‘’`\']+")


def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яЎўҚқҒғҲҳЁё]", text))


def _word_to_cyrillic(word: str) -> str:
    out = []
    i = 0
    n = len(word)
    while i < n:
        matched = False
        for lat, cyr in _LAT_DIGRAPHS:
            L = len(lat)
            if word[i:i + L].lower() == lat:
                seg = word[i:i + L]
                out.append(cyr.upper() if seg[0].isupper() else cyr)
                i += L
                matched = True
                break
        if matched:
            continue

        ch = word[i]
        low = ch.lower()
        if low == "e":
            prev_is_vowel_or_start = (i == 0) or (word[i - 1].lower() in _LAT_VOWELS)
            cyr = "э" if prev_is_vowel_or_start else "е"
        elif ch in _APOSTROPHES:
            cyr = "ъ"
        elif low in _LAT_SINGLE_MAP:
            cyr = _LAT_SINGLE_MAP[low]
        else:
            cyr = ch  # tanilmagan belgi — o'zgartirilmaydi

        if ch.isupper() and cyr.isalpha():
            cyr = cyr.upper()
        out.append(cyr)
        i += 1

    result = "".join(out)
    # Rus tilidan o'zlashgan familiyalarda ("Aliyev" -> "Алиев",
    # "Valiyeva" -> "Валиева") "ий"+"е" birikmasidagi "й" odatda tushib qoladi.
    result = result.replace("ийев", "иев").replace("ИЙЕВ", "ИЕВ")
    result = result.replace("ийева", "иева").replace("ИЙЕВА", "ИЕВА")
    return result


def to_cyrillic(text: str) -> str:
    """Matndagi lotincha so'zlarni Kirillga o'giradi (Kirill qism o'zgarmaydi)."""
    if not text:
        return text

    def _replace(match: "re.Match[str]") -> str:
        word = match.group(0)
        if _has_cyrillic(word):
            return word
        return _word_to_cyrillic(word)
