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
    PHOTO,
) = range(26)


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
