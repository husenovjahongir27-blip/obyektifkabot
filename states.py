from aiogram.fsm.state import State, StatesGroup


class ObyektivkaForm(StatesGroup):
    """
    Rasmiy MA'LUMOTNOMA (obyektivka) namunasiga mos bosqichlar.
    Faqat obyektivka to'ldiruvchi (asosiy shaxs) haqidagi bo'lim to'ldiriladi;
    "yaqin qarindoshlari haqida" bo'limi ushbu botda ishlanmaydi.
    """

    language = State()               # "uz" yoki "ru"
    script = State()                 # "uz" tanlansa: "cyr" yoki "lat"

    photo = State()                 # 3x4 profil surati (ixtiyoriy)

    full_name = State()             # F.I.Sh. (to'liq)
    position_since = State()        # Masalan: "2007 йил 5 октябрдан"
    current_position = State()      # Hozirgi lavozimi va tashkilot nomi (to'liq)

    birth_date = State()            # Tug'ilgan yili (sana)
    birth_place = State()           # Tug'ilgan joyi
    nationality = State()           # Millati
    party_affiliation = State()     # Partiyaviyligi

    education_level = State()       # Ma'lumoti (oliy / o'rta maxsus va h.k.)
    graduated_from = State()        # Tamomlagan (muassasa, yil, shakli)
    specialty = State()             # Ma'lumoti bo'yicha mutaxassisligi

    academic_degree = State()       # Ilmiy darajasi
    academic_title = State()        # Ilmiy unvoni
    foreign_languages = State()     # Qaysi chet tillarini biladi
    military_title = State()        # Harbiy (maxsus) unvoni

    state_awards = State()          # Davlat mukofotlari va premiyalari
    departmental_awards = State()   # Idoraviy mukofotlar
    elected_member = State()        # Saylanadigan organlar a'zoligi

    work_entry = State()            # Mehnat faoliyati: bitta yozuv (yillar - lavozim)
    work_entry_more = State()       # Yana qo'shish yoki tugatish

    notes = State()                 # Izoh (ixtiyoriy)
