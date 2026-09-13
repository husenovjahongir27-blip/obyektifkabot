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
