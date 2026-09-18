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
from states import ObyektivkaForm, AdminBroadcastForm
from generator import generate_malumotnoma_docx, convert_docx_to_pdf
from uz_translit import normalize_text, to_latin

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def _parse_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or ""
    ids = set()
    for item in raw.replace(";", ",").split(","):
        item = item.strip()
        if item:
            try:
                ids.add(int(item))
            except ValueError:
                logging.warning("Noto'g'ri ADMIN_ID: %s", item)
    return ids

ADMIN_IDS = _parse_admin_ids()

def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in ADMIN_IDS)

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(storage=MemoryStorage())

MENU_NEW = "🟢 Yangi obʼektivka"
MENU_MY = "📁 Mening obʼektivkam"
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
