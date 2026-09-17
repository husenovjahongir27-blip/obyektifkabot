import asyncio
import logging
import os
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    FSInputFile,
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
)
from aiohttp import web
from dotenv import load_dotenv

import db
from states import ObyektivkaForm
from generator import generate_malumotnoma_docx, convert_docx_to_pdf
from uz_translit import normalize_text, to_latin

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(storage=MemoryStorage())

MENU_NEW = "🟢 Yangi ob'ektivka"
MENU_MY = "📁 Mening ob'ektivkam"
MENU_BALANCE = "💰 Balans"


def _lang_variant(data: dict) -> str:
    """FSM data'dagi til/skript tanloviga qarab label variantini aniqlaydi."""
    if data.get("language") == "ru":
        return "ru"
    if data.get("script") == "lat":
        return "uz_lat"
    return "uz_cyr"


async def normalize_input(state: FSMContext, text: str) -> str:
    data = await state.get_data()
    language = data.get("language", "uz")
    script = data.get("script", "cyr")
    return normalize_text(text, language, script)


async def skip_default(state: FSMContext) -> str:
    data = await state.get_data()
    variant = _lang_variant(data)
    return {"uz_cyr": "йўқ", "uz_lat": "yo'q", "ru": "нет"}.get(variant, "йўқ")


def _ui(text: str, variant: str) -> str:
    """Botning o'z savol/xabarlari (har doim kirillcha yozilgan) tanlangan
    skriptga moslab ko'rsatiladi. Faqat uz_lat uchun lotinga o'giriladi —
    uz_cyr va ru holatlarida matn o'zgarishsiz qoladi."""
    if variant == "uz_lat":
        return to_latin(text)
    return text


async def _variant(state: FSMContext) -> str:
    data = await state.get_data()
    return _lang_variant(data)


async def say(message: Message, state: FSMContext, text: str, reply_markup=None):
    """message.answer() o'rnini bosadi, lekin matnni avval tanlangan
    skriptga moslaydi."""
    variant = await _variant(state)
    await message.answer(_ui(text, variant), reply_markup=reply_markup)


def skip_kb(variant: str, text: str = "Йўқ / ўтказиб юбориш") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_ui(text, variant), callback_data="skip")]]
    )


def more_or_done_kb(variant: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_ui("➕ Яна қўшиш", variant), callback_data="more"),
                InlineKeyboardButton(text=_ui("✅ Тугатиш", variant), callback_data="done"),
            ]
        ]
    )


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="O'zbekcha", callback_data="lang_uz"),
                InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
            ]
        ]
    )


def script_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Кирилча", callback_data="script_cyr"),
                InlineKeyboardButton(text="Lotincha", callback_data="script_lat"),
            ]
        ]
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_NEW)],
            [KeyboardButton(text=MENU_MY), KeyboardButton(text=MENU_BALANCE)],
        ],
        resize_keyboard=True,
    )


# ---------- Doimiy menyu tugmalari (holatdan qat'i nazar ishlaydi) ----------
# MUHIM: bu handlerlar faylda pastdagi @dp.message(ObyektivkaForm.xxx)
# handlerlaridan OLDIN turishi shart — aks holda FSM jarayonida bosilgan
# tugma matni navbatdagi savolga "javob" sifatida qabul qilinib qoladi.

@dp.message(F.text == MENU_NEW)
async def menu_new(message: Message, state: FSMContext):
    await start_flow(message, state)


@dp.message(F.text == MENU_MY)
async def menu_my_documents(message: Message, state: FSMContext):
    try:
        rows = await db.get_user_documents(message.chat.id)
    except Exception:
        logging.exception("DB xatosi: get_user_documents")
        rows = []

    if not rows:
        await message.answer("Sizda hali tayyorlangan hujjatlar yo'q. \"🟢 Yangi ob'ektivka\" tugmasini bosing.")
        return

    buttons = []
    for row in rows:
        created = row["created_at"].strftime("%d.%m.%Y") if row["created_at"] else ""
        label = f"{row['full_name'] or 'Malumotnoma'} ({(row['fmt'] or '').upper()}) — {created}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"doc:{row['id']}")])

    await message.answer(
        "Sizning oxirgi hujjatlaringiz — yuklab olish uchun bosing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@dp.callback_query(F.data.startswith("doc:"))
async def send_saved_document(callback: CallbackQuery):
    try:
        doc_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    try:
        row = await db.get_document_file(doc_id, callback.message.chat.id)
    except Exception:
        logging.exception("DB xatosi: get_document_file")
        row = None

    if not row or not row["file_data"]:
        await callback.answer("Hujjat topilmadi.", show_alert=True)
        return

    await callback.message.answer_document(
        BufferedInputFile(bytes(row["file_data"]), filename=row["file_name"] or "malumotnoma.docx")
    )
    await callback.answer()


@dp.message(F.text == MENU_BALANCE)
async def menu_balance(message: Message):
    await message.answer("💰 Balans funksiyasi tez orada qo'shiladi.")


# ---------- /start va /cancel ----------

async def start_flow(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(work_history=[], relatives=[])

    try:
        await db.register_user(message.chat.id, message.from_user.username if message.from_user else None)
    except Exception:
        logging.exception("DB xatosi: register_user")

    await message.answer(
        "Assalomu alaykum! Men rasmiy MA'LUMOTNOMA (obyektivka) tayyorlab beruvchi botman.",
        reply_markup=main_menu_kb(),
    )
    await message.answer(
        "Avvalo, hujjat qaysi tilda bo'lishini tanlang:",
        reply_markup=language_kb(),
    )
    await state.set_state(ObyektivkaForm.language)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await start_flow(message, state)


@dp.callback_query(ObyektivkaForm.language, F.data == "lang_uz")
async def choose_lang_uz(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language="uz")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Qaysi yozuvda (alifboda) yozishni xohlaysiz? "
        "Javoblaringizni istagan yozuvda kiriting — hujjat tanlangan yozuvga moslab tayyorlanadi.",
        reply_markup=script_kb(),
    )
    await state.set_state(ObyektivkaForm.script)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.language, F.data == "lang_ru")
async def choose_lang_ru(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language="ru", script=None)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Диққат: ушбу режимда ҳужжат банд номлари русча чиқади, лекин жавобларни "
        "ЎЗИНГИЗ русча киритишингиз керак — автоматик таржима амалга оширилмайди.",
    )
    await start_photo_step(callback.message, state)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.script, F.data.in_({"script_cyr", "script_lat"}))
async def choose_script(callback: CallbackQuery, state: FSMContext):
    script = "cyr" if callback.data == "script_cyr" else "lat"
    await state.update_data(script=script)
    await callback.message.edit_reply_markup(reply_markup=None)
    await start_photo_step(callback.message, state)
    await callback.answer()


async def start_photo_step(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Жараённи истаган вақтда /cancel буйруғи билан бекор қилишингиз мумкин.\n\n"
        "Аввало, 3x4 см ҳажмдаги профил суратингизни юборинг "
        "(агар ҳозир бўлмаса, пастдаги тугмани босинг):",
        reply_markup=skip_kb(variant, "Суратсиз давом этиш"),
    )
    await state.set_state(ObyektivkaForm.photo)


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await say(message, state, "Жараён бекор қилинди. Қайта бошлаш учун /start босинг.")


# ---------- Surat ----------

@dp.message(ObyektivkaForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await ask_full_name(message, state)


@dp.callback_query(ObyektivkaForm.photo, F.data == "skip")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_full_name(callback.message, state)
    await callback.answer()


async def ask_full_name(message: Message, state: FSMContext):
    await say(message, state, "Ф.И.Ш. (фамилия, исм, шарифингизни) тўлиқ киритинг:")
    await state.set_state(ObyektivkaForm.full_name)


# ---------- Oddiy matnli bosqichlar ----------

@dp.message(ObyektivkaForm.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=await normalize_input(state, message.text.strip()))
    await say(
        message, state,
        "Ҳозирги лавозимингизга қачондан бошлаб ишлаётганингизни киритинг.\n"
        "Масалан: 2007 йил 5 октябрдан"
    )
    await state.set_state(ObyektivkaForm.position_since)


@dp.message(ObyektivkaForm.position_since)
async def process_position_since(message: Message, state: FSMContext):
    await state.update_data(position_since=await normalize_input(state, message.text.strip()))
    await say(
        message, state,
        "Ҳозирги лавозимингиз ва ташкилот номини тўлиқ киритинг.\n"
        "Масалан: Тошкент давлат иқтисодиёт университетининг ўқув ишлари бўйича проректори"
    )
    await state.set_state(ObyektivkaForm.current_position)


@dp.message(ObyektivkaForm.current_position)
async def process_current_position(message: Message, state: FSMContext):
    await state.update_data(current_position=await normalize_input(state, message.text.strip()))
    await say(message, state, "Туғилган йилингиз (сана, масалан: 15.02.1989):")
    await state.set_state(ObyektivkaForm.birth_date)


@dp.message(ObyektivkaForm.birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    await state.update_data(birth_date=await normalize_input(state, message.text.strip()))
    await say(message, state, "Туғилган жойингиз:")
    await state.set_state(ObyektivkaForm.birth_place)


@dp.message(ObyektivkaForm.birth_place)
async def process_birth_place(message: Message, state: FSMContext):
    await state.update_data(birth_place=await normalize_input(state, message.text.strip()))
    await say(message, state, "Миллатингиз:")
    await state.set_state(ObyektivkaForm.nationality)


@dp.message(ObyektivkaForm.nationality)
async def process_nationality(message: Message, state: FSMContext):
    await state.update_data(nationality=await normalize_input(state, message.text.strip()))
    variant = await _variant(state)
    await say(
        message, state,
        "Партиявийлигингиз (аъзо бўлмасангиз, «йўқ» тугмасини босинг):",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.party_affiliation)


@dp.message(ObyektivkaForm.party_affiliation)
async def process_party_affiliation(message: Message, state: FSMContext):
    await state.update_data(party_affiliation=await normalize_input(state, message.text.strip()))
    await ask_education_level(message, state)


@dp.callback_query(ObyektivkaForm.party_affiliation, F.data == "skip")
async def skip_party_affiliation(callback: CallbackQuery, state: FSMContext):
    await state.update_data(party_affiliation=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_education_level(callback.message, state)
    await callback.answer()


async def ask_education_level(message: Message, state: FSMContext):
    await say(message, state, "Маълумотингиз (масалан: олий, ўрта махсус):")
    await state.set_state(ObyektivkaForm.education_level)


@dp.message(ObyektivkaForm.education_level)
async def process_education_level(message: Message, state: FSMContext):
    await state.update_data(education_level=await normalize_input(state, message.text.strip()))
    await say(
        message, state,
        "Тамомлаган ўқув юртингиз, йили ва шакли (кундузги/сиртқи) ни киритинг.\n"
        "Масалан: 1982 й. Тошкент давлат университети (кундузги)"
    )
    await state.set_state(ObyektivkaForm.graduated_from)


@dp.message(ObyektivkaForm.graduated_from)
async def process_graduated_from(message: Message, state: FSMContext):
    await state.update_data(graduated_from=await normalize_input(state, message.text.strip()))
    await say(message, state, "Маълумотингиз бўйича мутахассислигингиз:")
    await state.set_state(ObyektivkaForm.specialty)


@dp.message(ObyektivkaForm.specialty)
async def process_specialty(message: Message, state: FSMContext):
    await state.update_data(specialty=await normalize_input(state, message.text.strip()))
    variant = await _variant(state)
    await say(
        message, state,
        "Илмий даражангиз борми? Бўлса ёзинг, бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.academic_degree)


@dp.message(ObyektivkaForm.academic_degree)
async def process_academic_degree(message: Message, state: FSMContext):
    await state.update_data(academic_degree=await normalize_input(state, message.text.strip()))
    await ask_academic_title(message, state)


@dp.callback_query(ObyektivkaForm.academic_degree, F.data == "skip")
async def skip_academic_degree(callback: CallbackQuery, state: FSMContext):
    await state.update_data(academic_degree=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_academic_title(callback.message, state)
    await callback.answer()


async def ask_academic_title(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Илмий унвонингиз борми? Бўлса ёзинг, бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.academic_title)


@dp.message(ObyektivkaForm.academic_title)
async def process_academic_title(message: Message, state: FSMContext):
    await state.update_data(academic_title=await normalize_input(state, message.text.strip()))
    await ask_foreign_languages(message, state)


@dp.callback_query(ObyektivkaForm.academic_title, F.data == "skip")
async def skip_academic_title(callback: CallbackQuery, state: FSMContext):
    await state.update_data(academic_title=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_foreign_languages(callback.message, state)
    await callback.answer()


async def ask_foreign_languages(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Қайси чет тилларини мукаммал биласиз? "
        "(Луғат ёрдамида биладиганлари кўрсатилмайди.) Бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.foreign_languages)


@dp.message(ObyektivkaForm.foreign_languages)
async def process_foreign_languages(message: Message, state: FSMContext):
    await state.update_data(foreign_languages=await normalize_input(state, message.text.strip()))
    await ask_military_title(message, state)


@dp.callback_query(ObyektivkaForm.foreign_languages, F.data == "skip")
async def skip_foreign_languages(callback: CallbackQuery, state: FSMContext):
    await state.update_data(foreign_languages=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_military_title(callback.message, state)
    await callback.answer()


async def ask_military_title(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Ҳарбий (махсус) унвонингиз борми (фақат ҳарбий/ҳуқуқни муҳофаза қилиш "
        "идоралари ходимлари учун)? Бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.military_title)


@dp.message(ObyektivkaForm.military_title)
async def process_military_title(message: Message, state: FSMContext):
    await state.update_data(military_title=await normalize_input(state, message.text.strip()))
    await ask_state_awards(message, state)


@dp.callback_query(ObyektivkaForm.military_title, F.data == "skip")
async def skip_military_title(callback: CallbackQuery, state: FSMContext):
    await state.update_data(military_title=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_state_awards(callback.message, state)
    await callback.answer()


async def ask_state_awards(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Давлат мукофотлари ва премиялари билан тақдирланганмисиз (қанақа)? "
        "Бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.state_awards)


@dp.message(ObyektivkaForm.state_awards)
async def process_state_awards(message: Message, state: FSMContext):
    await state.update_data(state_awards=await normalize_input(state, message.text.strip()))
    await ask_departmental_awards(message, state)


@dp.callback_query(ObyektivkaForm.state_awards, F.data == "skip")
async def skip_state_awards(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_awards=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_departmental_awards(callback.message, state)
    await callback.answer()


async def ask_departmental_awards(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Идоравий мукофотлар билан тақдирланганмисиз (қанақа)? "
        "Бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.departmental_awards)


@dp.message(ObyektivkaForm.departmental_awards)
async def process_departmental_awards(message: Message, state: FSMContext):
    await state.update_data(departmental_awards=await normalize_input(state, message.text.strip()))
    await ask_elected_member(message, state)


@dp.callback_query(ObyektivkaForm.departmental_awards, F.data == "skip")
async def skip_departmental_awards(callback: CallbackQuery, state: FSMContext):
    await state.update_data(departmental_awards=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_elected_member(callback.message, state)
    await callback.answer()


async def ask_elected_member(message: Message, state: FSMContext):
    variant = await _variant(state)
    await say(
        message, state,
        "Халқ депутатлари, республика, вилоят, шаҳар ва туман Кенгаши депутатимисиз "
        "ёки бошқа сайланадиган органларнинг аъзосимисиз (тўлиқ кўрсатинг)? "
        "Бўлмаса тугмани босинг:",
        reply_markup=skip_kb(variant),
    )
    await state.set_state(ObyektivkaForm.elected_member)


@dp.message(ObyektivkaForm.elected_member)
async def process_elected_member(message: Message, state: FSMContext):
    await state.update_data(elected_member=await normalize_input(state, message.text.strip()))
    await ask_work_entry(message, state)


@dp.callback_query(ObyektivkaForm.elected_member, F.data == "skip")
async def skip_elected_member(callback: CallbackQuery, state: FSMContext):
    await state.update_data(elected_member=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_work_entry(callback.message, state)
    await callback.answer()


async def ask_work_entry(message: Message, state: FSMContext):
    await say(
        message, state,
        "Энди МЕҲНАТ ФАОЛИЯТИНГИЗ ҳақида, талаба йилларингиздан бошлаб, "
        "хронологик тартибда киритинг.\n"
        "Бир ёзувни қуйидаги тартибда юборинг:\n"
        "<йиллар> йй. - <лавозим/ташкилот>\n\n"
        "Масалан: 1998-2004 йй. - Тошкент давлат университети талабаси"
    )
    await state.set_state(ObyektivkaForm.work_entry)


@dp.message(ObyektivkaForm.work_entry)
async def process_work_entry(message: Message, state: FSMContext):
    data = await state.get_data()
    work_history = data.get("work_history", [])
    work_history.append(await normalize_input(state, message.text.strip()))
    await state.update_data(work_history=work_history)

    variant = await _variant(state)
    await say(
        message, state,
        "Яна бир иш/лавозим ёзувини қўшасизми?",
        reply_markup=more_or_done_kb(variant),
    )
    await state.set_state(ObyektivkaForm.work_entry_more)


@dp.callback_query(ObyektivkaForm.work_entry_more, F.data == "more")
async def work_entry_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await say(callback.message, state, "Яна бир ёзувни киритинг (йиллар йй. - лавозим/ташкилот):")
    await state.set_state(ObyektivkaForm.work_entry)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.work_entry_more, F.data == "done")
async def work_entry_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_relative_relation(callback.message, state, first=True)
    await callback.answer()


# ---------- Yaqin qarindoshlari haqida (2-sahifa uchun) ----------

async def ask_relative_relation(message: Message, state: FSMContext, first: bool = False):
    variant = await _variant(state)
    if first:
        text = (
            "Энди яқин қариндошларингиз (отаси, онаси, турмуш ўртоғи, "
            "фарзандлари, ака-ука, опа-сингиллари ва ҳ.к.) ҳақида маълумот "
            "киритамиз.\n\n"
            "Аввало, қариндошлик даражасини киритинг (масалан: Отаси):"
        )
        await say(message, state, text, reply_markup=skip_kb(variant, "Киритмайман / ўтказиб юбориш"))
    else:
        await say(message, state, "Қариндошлик даражасини киритинг (масалан: Онаси):")
    await state.set_state(ObyektivkaForm.relative_relation)


@dp.callback_query(ObyektivkaForm.relative_relation, F.data == "skip")
async def skip_relatives_entirely(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await generate_and_send(callback.message, state)
    await callback.answer()


@dp.message(ObyektivkaForm.relative_relation)
async def process_relative_relation(message: Message, state: FSMContext):
    await state.update_data(
        current_relative={"relation": await normalize_input(state, message.text.strip())}
    )
    await say(message, state, "Ф.И.Ш.ини (фамилияси, исми ва отасининг исми) тўлиқ киритинг:")
    await state.set_state(ObyektivkaForm.relative_name)


@dp.message(ObyektivkaForm.relative_name)
async def process_relative_name(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["full_name"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(
        message, state,
        "Туғилган йили ва жойини киритинг.\nМасалан: 1959 йил, Қибрай тумани"
    )
    await state.set_state(ObyektivkaForm.relative_birth)


@dp.message(ObyektivkaForm.relative_birth)
async def process_relative_birth(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["birth_info"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(
        message, state,
        "Иш жойи ва лавозимини киритинг.\n"
        "Масалан: Тошкент тиббиёт коллежи ўқитувчиси ёки Пенсияда"
    )
    await state.set_state(ObyektivkaForm.relative_job)


@dp.message(ObyektivkaForm.relative_job)
async def process_relative_job(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["job_info"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(message, state, "Турар жойини (манзилини) киритинг:")
    await state.set_state(ObyektivkaForm.relative_address)


@dp.message(ObyektivkaForm.relative_address)
async def process_relative_address(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["address"] = await normalize_input(state, message.text.strip())

    relatives = data.get("relatives", [])
    relatives.append(current)
    await state.update_data(relatives=relatives, current_relative={})

    variant = await _variant(state)
    await say(
        message, state,
        "Яна бир қариндош қўшасизми?",
        reply_markup=more_or_done_kb(variant),
    )
    await state.set_state(ObyektivkaForm.relative_more)


@dp.callback_query(ObyektivkaForm.relative_more, F.data == "more")
async def relative_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_relative_relation(callback.message, state, first=False)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.relative_more, F.data == "done")
async def relative_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await generate_and_send(callback.message, state)
    await callback.answer()


# ---------- Hujjatni yaratish va yuborish ----------

async def generate_and_send(message: Message, state: FSMContext, bot: Bot | None = None):
    data = await state.get_data()
    await say(message, state, "Ҳужжат тайёрланмоқда, бироз кутинг...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        safe_name = "".join(
            c for c in data.get("full_name", "malumotnoma") if c.isalnum() or c in " _-"
        ).strip()
        safe_name = safe_name.replace(" ", "_") or "malumotnoma"

        photo_path = None
        photo_file_id = data.get("photo_file_id")
        if photo_file_id:
            bot_instance = bot or message.bot
            photo_path = os.path.join(tmp_dir, "photo.jpg")
            await bot_instance.download(photo_file_id, destination=photo_path)

        docx_path = os.path.join(tmp_dir, f"{safe_name}.docx")
        generate_malumotnoma_docx(data, docx_path, photo_path=photo_path,
                                    lang_variant=_lang_variant(data))

        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        try:
            await db.log_document(
                message.chat.id, data.get("full_name", "-"), "docx",
                os.path.basename(docx_path), docx_bytes,
            )
        except Exception:
            logging.exception("DB xatosi: log_document (docx)")

        await message.answer_document(FSInputFile(docx_path))

        pdf_path = convert_docx_to_pdf(docx_path, tmp_dir)
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            try:
                await db.log_document(
                    message.chat.id, data.get("full_name", "-"), "pdf",
                    os.path.basename(pdf_path), pdf_bytes,
                )
            except Exception:
                logging.exception("DB xatosi: log_document (pdf)")
            await message.answer_document(FSInputFile(pdf_path))
        else:
            await say(
                message, state,
                "PDF версиясини тайёрлаб бўлмади (серверда LibreOffice топилмади), "
                "лекин Word (.docx) файли тайёр.",
            )

    await say(
        message, state,
        "Маълумотнома тайёр! Юқоридаги файл(лар)ни очиб юклаб олишингиз мумкин. "
        "Янгисини яратиш учун \"🟢 Yangi ob'ektivka\" тугмасини босинг.",
        reply_markup=main_menu_kb(),
    )
    await state.clear()


async def _health(request):
    return web.Response(text="OK")


async def start_web_server():
    """Render 'Web Service' $PORT ni tinglashni talab qiladi — aks holda
    deploy 'Timed Out' bo'lib, eski jarayon bilan yangisi bir vaqtda
    ishga tushib, Telegram 'Conflict' xatosiga olib keladi. Shu sabab
    polling bilan bir qatorda mayda HTTP server ham ishga tushiriladi."""
    app = web.Application()
    app.router.add_get("/", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Health-check HTTP server {port}-portda ishga tushdi")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN топилмади. Лойиҳа папкасида .env файл яратинг ва "
            "ичига BOT_TOKEN=... деб ёзинг (токенни @BotFather дан олинг)."
        )

    try:
        await db.init_db()
    except Exception:
        logging.exception("DB xatosi: init_db")

    bot = Bot(token=BOT_TOKEN)
    # Agar avval botga webhook o'rnatilgan bo'lsa, uni o'chirish shart —
    # aks holda getUpdates (polling) bilan "Conflict" xatosi chiqadi.
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
