# -*- coding: utf-8 -*-
"""
MA'LUMOTNOMA va (ixtiyoriy) Qarindoshlar to'g'risida ma'lumot hujjatini
tayyorlovchi Telegram bot.

Ishga tushirish:
    1) pip install -r requirements.txt
    2) fonts/DejaVuSans.ttf va fonts/DejaVuSans-Bold.ttf fayllarini joylang (PDF uchun)
    3) BOT_TOKEN muhit o'zgaruvchisini o'rnating
    4) python bot.py
"""

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
) = range(25)


def t(context, key):
    lang = context.user_data["lang_key"]
    return PROMPTS[lang][key]


def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
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
        yes_text, no_text = "Ha", "Yo'q"
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


# ---------------------------------------------------------------------------
# Til va alifbo
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["work_history"] = []
    context.user_data["relatives"] = []
    await update.message.reply_text(
        "Assalomu alaykum! Bu bot MA'LUMOTNOMA va qarindoshlar to'g'risidagi "
        "ma'lumot hujjatini tayyorlab beradi.\n\n"
        "Hujjat tilini tanlang / Выберите язык документа:",
        reply_markup=lang_keyboard(),
    )
    return CHOOSING_LANG


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
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text(t(context, "birth_date"))
    return BIRTH_DATE


async def get_birth_date(update, context):
    context.user_data["birth_date"] = update.message.text.strip()
    await update.message.reply_text(t(context, "birth_place"))
    return BIRTH_PLACE


async def get_birth_place(update, context):
    context.user_data["birth_place"] = update.message.text.strip()
    await update.message.reply_text(t(context, "nationality"))
    return NATIONALITY


async def get_nationality(update, context):
    context.user_data["nationality"] = update.message.text.strip()
    await update.message.reply_text(t(context, "education_level"))
    return EDU_LEVEL


async def get_edu_level(update, context):
    context.user_data["education_level"] = update.message.text.strip()
    await update.message.reply_text(t(context, "education_detail"))
    return EDU_DETAIL


async def get_edu_detail(update, context):
    context.user_data["education_detail"] = update.message.text.strip()
    await update.message.reply_text(t(context, "specialty"))
    return SPECIALTY


async def get_specialty(update, context):
    context.user_data["specialty"] = update.message.text.strip()
    await update.message.reply_text(t(context, "academic_degree"))
    return ACAD_DEGREE


async def get_acad_degree(update, context):
    context.user_data["academic_degree"] = update.message.text.strip()
    await update.message.reply_text(t(context, "academic_title"))
    return ACAD_TITLE


async def get_acad_title(update, context):
    context.user_data["academic_title"] = update.message.text.strip()
    await update.message.reply_text(t(context, "foreign_lang"))
    return FOREIGN_LANG


async def get_foreign_lang(update, context):
    context.user_data["foreign_lang"] = update.message.text.strip()
    await update.message.reply_text(t(context, "military_title"))
    return MILITARY_TITLE


async def get_military_title(update, context):
    context.user_data["military_title"] = update.message.text.strip()
    await update.message.reply_text(t(context, "state_awards"))
    return STATE_AWARDS


async def get_state_awards(update, context):
    context.user_data["state_awards"] = update.message.text.strip()
    await update.message.reply_text(t(context, "work_years"))
    return WORK_YEARS


# ---------------------------------------------------------------------------
# Mehnat faoliyati (takrorlanuvchi bandlar)
# ---------------------------------------------------------------------------
async def get_work_years(update, context):
    context.user_data["_current_work_years"] = update.message.text.strip()
    await update.message.reply_text(t(context, "work_position"))
    return WORK_POSITION


async def get_work_position(update, context):
    years = context.user_data.pop("_current_work_years")
    position = update.message.text.strip()
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
    context.user_data["_current_rel_name"] = update.message.text.strip()
    await update.message.reply_text(t(context, "rel_birth"))
    return REL_BIRTH


async def get_rel_birth(update, context):
    context.user_data["_current_rel_birth"] = update.message.text.strip()
    await update.message.reply_text(t(context, "rel_work"))
    return REL_WORK


async def get_rel_work(update, context):
    context.user_data["_current_rel_work"] = update.message.text.strip()
    await update.message.reply_text(t(context, "rel_address"))
    return REL_ADDRESS


async def get_rel_address(update, context):
    address = update.message.text.strip()
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

    doc_types = ["malumotnoma"]
    if data.get("relatives"):
        doc_types.append("relatives")

    for doc_type in doc_types:
        try:
            path = generate(doc_type, lang_key, data, fmt)
        except Exception as e:
            logger.exception("Hujjat yaratishda xato: %s", doc_type)
            await context.bot.send_message(
                chat_id=query.message.chat_id, text=f"Xatolik yuz berdi ({doc_type}): {e}"
            )
            continue
        with open(path, "rb") as f:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=f,
                filename=os.path.basename(path),
                caption="✅",
            )
        os.remove(path)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi. Qaytadan boshlash uchun /start bosing.")
    return ConversationHandler.END


TEXT_FILTER = filters.TEXT & ~filters.COMMAND


def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN o'rnatilmagan! Muhit o'zgaruvchisi sifatida bering yoki "
            "bot.py faylida to'g'ridan-to'g'ri kiriting."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANG: [CallbackQueryHandler(choose_lang, pattern="^lang_")],
            CHOOSING_SCRIPT: [CallbackQueryHandler(choose_script, pattern="^script_")],
            FULL_NAME: [MessageHandler(TEXT_FILTER, get_full_name)],
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

    app.add_handler(conv_handler)

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
