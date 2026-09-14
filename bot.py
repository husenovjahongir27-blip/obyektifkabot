# -*- coding: utf-8 -*-
"""
MA’LUMOTNOMA va (ixtiyoriy) Qarindoshlar to'g'risida ma’lumot hujjatini
tayyorlovchi Telegram bot.

Ishga tushirish:
    1) pip install -r requirements.txt
    2) fonts/DejaVuSans.ttf va fonts/DejaVuSans-Bold.ttf fayllarini joylang (PDF uchun)
    3) BOT_TOKEN muhit oʻzgaruvchisini o'rnating
    4) python bot.py
"""

import logging
import os
import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from generator import generate
from labels import PROMPTS, RELATION_OPTIONS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")

# Asosiy menyu tugmalari (doimiy pastki klaviatura)
BTN_NEW = "🟢 Yangi ob'ektivka"
BTN_MY_OBJECTS = "📁 Mening ob'ektivkam"
BTN_BALANCE = "💰 Balans"


def normalize_uzbek_text(value: str) -> str:
    """o'/g' kabi yozuvlarni adabiy o'zbekcha oʻ/gʻ ko'rinishiga o'tkazadi."""
    value = value.strip()
    value = value.replace("’", "ʻ").replace("‘", "ʻ").replace("ʼ", "ʻ")
    value = re.sub(r"([oOgG])['ʻ]", r"\1ʻ", value)
    return value

(
    CHOOSING_LANG,
    CHOOSING_SCRIPT,
    FULL_NAME,
    BIRTH_DATE,
    BIRTH_PLACE,
    NATIONALITY,
    EDU_LEVEL,
    EDU_DETAIL,
    SPECIALTY,
    ACAD_DEGREE,
    ACAD_TITLE,
    FOREIGN_LANG,
    MILITARY_TITLE,
    STATE_AWARDS,
    WORK_YEARS,
    WORK_POSITION,
    WORK_LOOP,
    ASK_RELATIVES,
    REL_RELATION,
    REL_NAME,
    REL_BIRTH,
    REL_WORK,
    REL_ADDRESS,
    REL_LOOP,
    CHOOSING_FORMAT,
    PHOTO,
) = range(26)


def t(context, key):
    lang = context.user_data["lang_key"]
    return PROMPTS[lang][key]


def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 Oʻzbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
    ])


def script_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Lotin", callback_data="script_latin")],
        [InlineKeyboardButton("Кирилл", callback_data="script_cyrillic")],
    ])


def yes_no_keyboard(yes_data, no_data, lang_key):
    if lang_key == "ru":
        yes_text, no_text = "Да", "Нет"
    elif lang_key == "uz_cyrillic":
        yes_text, no_text = "Ҳа", "Йўқ"
    else:
        yes_text, no_text = "Ha", "Yoʻq"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(yes_text, callback_data=yes_data),
         InlineKeyboardButton(no_text, callback_data=no_data)],
    ])


def relation_keyboard(lang_key):
    options = RELATION_OPTIONS[lang_key]
    rows = [[InlineKeyboardButton(label, callback_data=f"relation_{key}")] for key, label in options]
    return InlineKeyboardMarkup(rows)


def format_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF", callback_data="fmt_pdf")],
        [InlineKeyboardButton("📝 DOCX (Word)", callback_data="fmt_docx")],
    ])


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BTN_NEW],
            [BTN_MY_OBJECTS, BTN_BALANCE],
        ],
        resize_keyboard=True,
    )


# ---------------------------------------------------------------------------
# Til va alifbo
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum! Bu bot MA’LUMOTNOMA va qarindoshlar toʻgʻrisidagi "
        "ma’lumot hujjatini tayyorlab beradi.\n\n"
        "Quyidagi menyudan foydalaning 👇",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def begin_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["work_history"] = []
    context.user_data["relatives"] = []
    await update.message.reply_text(
        "Hujjat tilini tanlang / Выберите язык документа:",
        reply_markup=lang_keyboard(),
    )
    return CHOOSING_LANG


async def menu_my_objects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📁 \"Mening ob'ektivkam\" boʻlimi tez orada ishga tushadi.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def menu_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "💰 Balans boʻlimi tez orada ishga tushadi.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "lang_uz":
        await query.edit_message_text("Alifboni tanlang:", reply_markup=script_keyboard())
        return CHOOSING_SCRIPT
    context.user_data["lang_key"] = "ru"
    await query.edit_message_text(t(context, "full_name"))
    return FULL_NAME


async def choose_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["lang_key"] = "uz_latin" if query.data == "script_latin" else "uz_cyrillic"
    await query.edit_message_text(t(context, "full_name"))
    return FULL_NAME


# ---------------------------------------------------------------------------
# Asosiy shaxsiy maydonlar (ketma-ket)
# ---------------------------------------------------------------------------
async def get_full_name(update, context):
    context.user_data["full_name"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "photo_prompt"))
    return PHOTO


async def get_photo(update, context):
    """Telegramdan 3x4 rasm uchun suratni qabul qiladi."""
    if not update.message.photo:
        await update.message.reply_text(t(context, "photo_prompt"))
        return PHOTO

    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    photo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(photo_dir, exist_ok=True)
    photo_path = os.path.join(photo_dir, f"photo_{update.effective_user.id}_{photo.file_unique_id}.jpg")
    await tg_file.download_to_drive(photo_path)
    context.user_data["photo_path"] = photo_path

    await update.message.reply_text(t(context, "birth_date"))
    return BIRTH_DATE


async def get_birth_date(update, context):
    context.user_data["birth_date"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "birth_place"))
    return BIRTH_PLACE


async def get_birth_place(update, context):
    context.user_data["birth_place"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "nationality"))
    return NATIONALITY


async def get_nationality(update, context):
    context.user_data["nationality"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "education_level"))
    return EDU_LEVEL


async def get_edu_level(update, context):
    context.user_data["education_level"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "education_detail"))
    return EDU_DETAIL


async def get_edu_detail(update, context):
    context.user_data["education_detail"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "specialty"))
    return SPECIALTY


async def get_specialty(update, context):
    context.user_data["specialty"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "academic_degree"))
    return ACAD_DEGREE


async def get_acad_degree(update, context):
    context.user_data["academic_degree"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "academic_title"))
    return ACAD_TITLE


async def get_acad_title(update, context):
    context.user_data["academic_title"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "foreign_lang"))
    return FOREIGN_LANG


async def get_foreign_lang(update, context):
    context.user_data["foreign_lang"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "military_title"))
    return MILITARY_TITLE


async def get_military_title(update, context):
    context.user_data["military_title"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "state_awards"))
    return STATE_AWARDS


async def get_state_awards(update, context):
    context.user_data["state_awards"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "work_years"))
    return WORK_YEARS


# ---------------------------------------------------------------------------
# Mehnat faoliyati (takrorlanuvchi bandlar)
# ---------------------------------------------------------------------------
async def get_work_years(update, context):
    context.user_data["_current_work_years"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "work_position"))
    return WORK_POSITION


async def get_work_position(update, context):
    years = context.user_data.pop("_current_work_years")
    position = normalize_uzbek_text(update.message.text)
    context.user_data["work_history"].append({"years": years, "position": position})
    lang_key = context.user_data["lang_key"]
    await update.message.reply_text(
        t(context, "work_more"), reply_markup=yes_no_keyboard("work_more_yes", "work_more_no", lang_key)
    )
    return WORK_LOOP


async def work_loop_decision(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "work_more_yes":
        await query.edit_message_text(t(context, "work_years"))
        return WORK_YEARS
    lang_key = context.user_data["lang_key"]
    await query.edit_message_text(
        t(context, "ask_relatives"), reply_markup=yes_no_keyboard("rel_yes", "rel_no", lang_key)
    )
    return ASK_RELATIVES


# ---------------------------------------------------------------------------
# Qarindoshlar (ixtiyoriy, takrorlanuvchi bandlar)
# ---------------------------------------------------------------------------
async def ask_relatives_decision(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "rel_no":
        await query.edit_message_text(t(context, "choose_format"), reply_markup=format_keyboard())
        return CHOOSING_FORMAT
    lang_key = context.user_data["lang_key"]
    await query.edit_message_text(t(context, "rel_relation"), reply_markup=relation_keyboard(lang_key))
    return REL_RELATION


async def get_rel_relation(update, context):
    query = update.callback_query
    await query.answer()
    lang_key = context.user_data["lang_key"]
    key = query.data.replace("relation_", "")
    label_map = dict(RELATION_OPTIONS[lang_key])
    context.user_data["_current_relation_label"] = label_map.get(key, key)
    await query.edit_message_text(t(context, "rel_name"))
    return REL_NAME


async def get_rel_name(update, context):
    context.user_data["_current_rel_name"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "rel_birth"))
    return REL_BIRTH


async def get_rel_birth(update, context):
    context.user_data["_current_rel_birth"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "rel_work"))
    return REL_WORK


async def get_rel_work(update, context):
    context.user_data["_current_rel_work"] = normalize_uzbek_text(update.message.text)
    await update.message.reply_text(t(context, "rel_address"))
    return REL_ADDRESS


async def get_rel_address(update, context):
    address = normalize_uzbek_text(update.message.text)
    context.user_data["relatives"].append({
        "relation_label": context.user_data.pop("_current_relation_label"),
        "name": context.user_data.pop("_current_rel_name"),
        "birth": context.user_data.pop("_current_rel_birth"),
        "work": context.user_data.pop("_current_rel_work"),
        "address": address,
    })
    lang_key = context.user_data["lang_key"]
    await update.message.reply_text(
        t(context, "rel_more"), reply_markup=yes_no_keyboard("rel_more_yes", "rel_more_no", lang_key)
    )
    return REL_LOOP


async def rel_loop_decision(update, context):
    query = update.callback_query
    await query.answer()
    lang_key = context.user_data["lang_key"]
    if query.data == "rel_more_yes":
        await query.edit_message_text(t(context, "rel_relation"), reply_markup=relation_keyboard(lang_key))
        return REL_RELATION
    await query.edit_message_text(t(context, "choose_format"), reply_markup=format_keyboard())
    return CHOOSING_FORMAT


# ---------------------------------------------------------------------------
# Format tanlash va hujjatlarni yuborish
# ---------------------------------------------------------------------------
async def choose_format_and_send(update, context):
    query = update.callback_query
    await query.answer()
    fmt = "pdf" if query.data == "fmt_pdf" else "docx"

    lang_key = context.user_data["lang_key"]
    data = context.user_data

    await query.edit_message_text(t(context, "done"))

    # MA’LUMOTNOMA va yaqin qarindoshlar ma’lumotini bitta faylga birlashtiramiz.
    try:
        path = generate("combined", lang_key, data, fmt)
    except Exception as e:
        logger.exception("Bitta hujjat yaratishda xato: %s", e)
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=f"Xatolik yuz berdi: {e}"
        )
        context.user_data.clear()
        return ConversationHandler.END

    with open(path, "rb") as f:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=f,
            filename=os.path.basename(path),
            caption="✅ MA’LUMOTNOMA va yaqin qarindoshlar haqidagi ma’lumot",
        )
    os.remove(path)

    photo_path = context.user_data.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update, context):
    photo_path = context.user_data.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi. Qaytadan boshlash uchun /start bosing.")
    return ConversationHandler.END


TEXT_FILTER = filters.TEXT & ~filters.COMMAND


def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN oʻrnatilmagan! Muhit o'zgaruvchisi sifatida bering yoki "
            "bot.py faylida toʻgʻridan-toʻgʻri kiriting."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^{re.escape(BTN_NEW)}$"), begin_document)
        ],
        states={
            CHOOSING_LANG: [CallbackQueryHandler(choose_lang, pattern="^lang_")],
            CHOOSING_SCRIPT: [CallbackQueryHandler(choose_script, pattern="^script_")],
            FULL_NAME: [MessageHandler(TEXT_FILTER, get_full_name)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            BIRTH_DATE: [MessageHandler(TEXT_FILTER, get_birth_date)],
            BIRTH_PLACE: [MessageHandler(TEXT_FILTER, get_birth_place)],
            NATIONALITY: [MessageHandler(TEXT_FILTER, get_nationality)],
            EDU_LEVEL: [MessageHandler(TEXT_FILTER, get_edu_level)],
            EDU_DETAIL: [MessageHandler(TEXT_FILTER, get_edu_detail)],
            SPECIALTY: [MessageHandler(TEXT_FILTER, get_specialty)],
            ACAD_DEGREE: [MessageHandler(TEXT_FILTER, get_acad_degree)],
            ACAD_TITLE: [MessageHandler(TEXT_FILTER, get_acad_title)],
            FOREIGN_LANG: [MessageHandler(TEXT_FILTER, get_foreign_lang)],
            MILITARY_TITLE: [MessageHandler(TEXT_FILTER, get_military_title)],
            STATE_AWARDS: [MessageHandler(TEXT_FILTER, get_state_awards)],
            WORK_YEARS: [MessageHandler(TEXT_FILTER, get_work_years)],
            WORK_POSITION: [MessageHandler(TEXT_FILTER, get_work_position)],
            WORK_LOOP: [CallbackQueryHandler(work_loop_decision, pattern="^work_more_")],
            ASK_RELATIVES: [CallbackQueryHandler(ask_relatives_decision, pattern="^rel_(yes|no)$")],
            REL_RELATION: [CallbackQueryHandler(get_rel_relation, pattern="^relation_")],
            REL_NAME: [MessageHandler(TEXT_FILTER, get_rel_name)],
            REL_BIRTH: [MessageHandler(TEXT_FILTER, get_rel_birth)],
            REL_WORK: [MessageHandler(TEXT_FILTER, get_rel_work)],
            REL_ADDRESS: [MessageHandler(TEXT_FILTER, get_rel_address)],
            REL_LOOP: [CallbackQueryHandler(rel_loop_decision, pattern="^rel_more_")],
            CHOOSING_FORMAT: [CallbackQueryHandler(choose_format_and_send, pattern="^fmt_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Asosiy menyu tugmalari (ConversationHandler'dan tashqarida, doim ishlaydi)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(BTN_MY_OBJECTS)}$"), menu_my_objects))
    app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(BTN_BALANCE)}$"), menu_balance))

    app.add_handler(conv_handler)

    logger.info("Bot ishga tushdi...")

    # Render Free Web Service uchun webhook.
    # Python 3.14 da python-telegram-bot run_webhook event-loopni
    # MainThread'da aniq yaratishni talab qilishi mumkin.
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())

    port = int(os.environ.get("PORT", "10000"))
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        webhook_url = external_url.rstrip("/") + "/telegram-webhook"
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram-webhook",
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Lokal kompyuterda ishga tushirish uchun polling.
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
