"""
Rasmiy MA'LUMOTNOMA namunasidagi band nomlari (label) — uchta variantda:
    - uz_cyr — o'zbekcha, kirill (namunadagi asl matn, dasturiy nusxa
      ko'chirish orqali olingan — imlo xatosi bo'lmasligi uchun)
    - uz_lat — o'zbekcha, lotin (uz_cyr dan avtomatik transliteratsiya
      qilingan, qo'lda qayta terilmagan)
    - ru — ruscha (mazmunan tarjima qilingan, chunki bu alifbo emas,
      alohida til)

get_label_set(variant) shu uchtadan birini SimpleNamespace ko'rinishida
qaytaradi.
"""

from types import SimpleNamespace

from uz_translit import to_latin

# ==================== O'zbekcha - Kirill (namunadan aynan) ====================

_UZ_CYR = dict(
    TITLE="МАЪЛУМОТНОМА",
    BIRTH_LABELS=["Туғилган йили:", "Туғилган жойи:"],
    NATIONALITY_LABELS=["Миллати:", "Партиявийлиги:"],
    EDUCATION_LABELS=["Маълумоти:", "Тамомлаган:"],
    SPECIALTY_LABEL="Маълумоти бўйича мутахассислиги:",
    DEGREE_LABELS=["Илмий даражаси:", "Илмий унвони:"],
    LANGUAGE_LABELS=["Қайси чет тилларини билади:", "Ҳарбий (махсус) унвони:"],
    STATE_AWARDS_LABEL="Давлат мукофотлари ва премиялари билан тақдирланганми (қанақа):",
    DEPT_AWARDS_LABEL="Идоравий мукофотлар билан тақдирланганми (қанақа):",
    ELECTED_MEMBER_LABEL=(
        "Халқ депутатлари, республика, вилоят, шаҳар ва туман Кенгаши "
        "депутатими ёки бошқа сайланадиган органларнинг аъзосими "
        "(тўлиқ кўрсатилиши лозим):"
    ),
    WORK_HEADING="МЕҲНАТ ФАОЛИЯТИ",
    PHOTO_PLACEHOLDER=(
        "3х4 см, охирги 3 ой давомида олинган рангли фотосурат, "
        "электрон кўринишда (расмий кийимда, оқ фонда)."
    ),
    # 2-sahifa: yaqin qarindoshlari haqida
    RELATIVES_TITLE_SUFFIX="нинг яқин қариндошлари ҳақида",
    RELATIVES_HEADING="МАЪЛУМОТ",
    RELATIVES_HEADERS=[
        "Қариндош-\nлиги",
        "Фамилияси, исми\nва отасининг исми",
        "Туғилган йили\nва жойи",
        "Иш жойи ва лавозими",
        "Турар жойи",
    ],
)

# ==================== O'zbekcha - Lotin (avtomatik, uz_cyr dan) ====================

_LIST_KEYS = {"BIRTH_LABELS", "NATIONALITY_LABELS", "EDUCATION_LABELS",
              "DEGREE_LABELS", "LANGUAGE_LABELS", "RELATIVES_HEADERS"}

_UZ_LAT = {
    key: ([to_latin(v) for v in value] if key in _LIST_KEYS else to_latin(value))
    for key, value in _UZ_CYR.items()
}

# ==================== Ruscha (mazmunan tarjima) ====================

_RU = dict(
    TITLE="СПРАВКА",
    BIRTH_LABELS=["Дата рождения:", "Место рождения:"],
    NATIONALITY_LABELS=["Национальность:", "Партийность:"],
    EDUCATION_LABELS=["Образование:", "Окончил(а):"],
    SPECIALTY_LABEL="Специальность по образованию:",
    DEGREE_LABELS=["Учёная степень:", "Учёное звание:"],
    LANGUAGE_LABELS=["Какими иностранными языками владеет:", "Воинское (специальное) звание:"],
    STATE_AWARDS_LABEL="Награждён(а) ли государственными наградами и премиями (какими):",
    DEPT_AWARDS_LABEL="Награждён(а) ли ведомственными наградами (какими):",
    ELECTED_MEMBER_LABEL=(
        "Является ли депутатом Кенгаша народных депутатов Республики, области, "
        "города и района или членом других избираемых органов (указать полностью):"
    ),
    WORK_HEADING="ТРУДОВАЯ ДЕЯТЕЛЬНОСТЬ",
    PHOTO_PLACEHOLDER=(
        "Цветная фотография 3x4 см, сделанная в течение последних 3 месяцев, "
        "в электронном виде (в официальной одежде, на белом фоне)."
    ),
    RELATIVES_TITLE_SUFFIX=" — о его (её) близких родственниках",
    RELATIVES_HEADING="СВЕДЕНИЯ",
    RELATIVES_HEADERS=[
        "Степень\nродства",
        "Фамилия, имя\nи отчество",
        "Год и место\nрождения",
        "Место работы\nи должность",
        "Место\nжительства",
    ],
)

_LABEL_SETS = {
    "uz_cyr": _UZ_CYR,
    "uz_lat": _UZ_LAT,
    "ru": _RU,
}


def get_label_set(variant: str) -> SimpleNamespace:
    """variant: 'uz_cyr', 'uz_lat' yoki 'ru'. Noma'lum bo'lsa 'uz_cyr' ishlatiladi."""
    return SimpleNamespace(**_LABEL_SETS.get(variant, _UZ_CYR))
