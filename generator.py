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


def _set_docx_paragraph_format(paragraph, align=None):
    """Barcha Word matnlarini 14 pt va 1.5 qator oralig'ida saqlaydi."""
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)


def _set_cell_paragraphs(cell):
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)


def _add_cell_border(cell, color="000000", sz="8"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "left", "bottom", "right"):
        tag = "w:" + edge
        element = tcBorders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tcBorders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), sz)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def _framed_photo_docx(photo_stream):
    """Namuna kabi 3x4 suratni ingichka qora ramka ichida qaytaradi."""
    if not photo_stream:
        return None
    table = Document().add_table(rows=1, cols=1)
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Cm(3.0)
    cell.height = Cm(4.0)
