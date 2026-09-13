# -*- coding: utf-8 -*-
"""
Ikki turdagi hujjatni tayyorlaydi:
  1) "malumotnoma"  — shaxsiy MA'LUMOTNOMA (F.I.Sh, tug'ilgan yili/joyi, ma'lumoti,
     mehnat faoliyati ro'yxati va h.k.)
  2) "relatives"     — yaqin qarindoshlari to'g'risida MA'LUMOT (jadval)

Har biri DOCX (python-docx) yoki PDF (reportlab) ko'rinishida yaratiladi.
PDF uchun fonts/DejaVuSans.ttf va fonts/DejaVuSans-Bold.ttf fayllari kerak
(lotin/kirill harflarini to'g'ri chizish uchun).
"""

import os
import uuid
from io import BytesIO

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm as rl_cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

from labels import LABELS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_REGULAR_PATH = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf")

_FONTS_REGISTERED = False


def _register_pdf_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    if not os.path.exists(FONT_REGULAR_PATH):
        raise FileNotFoundError(
            f"Shrift topilmadi: {FONT_REGULAR_PATH}\n"
            "DejaVuSans.ttf va DejaVuSans-Bold.ttf fayllarini fonts/ papkasiga joylang."
        )
    pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_REGULAR_PATH))
    if os.path.exists(FONT_BOLD_PATH):
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD_PATH))
    else:
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_REGULAR_PATH))
    _FONTS_REGISTERED = True


def _unique_path(ext: str) -> str:
    return os.path.join(OUTPUT_DIR, f"hujjat_{uuid.uuid4().hex[:10]}.{ext}")


def _photo_3x4_stream(data: dict):
    """Suratni markazdan 3:4 nisbatda kesib, xotiradagi JPEG oqimini qaytaradi."""
    photo_path = data.get("photo_path")
    if not photo_path or not os.path.exists(photo_path):
        return None

    with PILImage.open(photo_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        target_ratio = 3 / 4
        current_ratio = width / height if height else target_ratio

        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))

        stream = BytesIO()
        img.save(stream, format="JPEG", quality=95)
        stream.seek(0)
        return stream

