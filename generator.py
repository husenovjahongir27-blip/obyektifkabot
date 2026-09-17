"""
Rasmiy "MA'LUMOTNOMA" (obyektivka) hujjatini namunaga (2025-yilgi rasmiy shakl)
mos ravishda yaratish uchun modul.

Hujjat ikki sahifadan iborat:
    1-sahifa — obyektivka to'ldiruvchi (asosiy shaxs) haqida ma'lumot
    2-sahifa — uning yaqin qarindoshlari haqida jadval (agar kiritilgan bo'lsa)

Namunada ko'rsatilgan rasmiylashtirish talablari qo'llanildi:
    - Shrift: Times New Roman, 11 pt
    - Sahifa chegaralari: yuqoridan 1.5 sm, pastdan 1 sm, o'ngdan 1 sm, chapdan 2 sm

Barcha band nomlari (label) namuna faylidan dasturiy nusxa ko'chirish orqali
olingan (labels.py), qo'lda qayta terilmagan — bu imlo xatolarining oldini oladi.
"""

import os
import subprocess

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import labels as labels_module
from uz_translit import normalize_uz_apostrophes

FONT_NAME = "Times New Roman"
FONT_SIZE = Pt(11)


# ---------- Yordamchi (past darajadagi XML) funksiyalar ----------

def _set_run_font(run, size=FONT_SIZE, bold=False, italic=False):
    run.font.name = FONT_NAME
    run.font.size = size
    run.bold = bold
    run.italic = italic
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), FONT_NAME)


def _remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'none')
        el.set(qn('w:sz'), '0')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), 'auto')
        borders.append(el)
    tblPr.append(borders)


def _set_table_borders_single(table, size=4, color="000000"):
    """Jadvalning barcha chiziqlarini yupqa, yagona chiziq (single) qilib chizadi
    — 2-sahifadagi qarindoshlar jadvali namunadagidek chiziqli bo'lishi uchun."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), str(size))
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        borders.append(el)
    tblPr.append(borders)


def _set_cell_border_box(cell, size=8, color="000000"):
    """Bitta katakka (foto uchun) chiziqli quti chizadi."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'dashSmallGap')
        el.set(qn('w:sz'), str(size))
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        borders.append(el)
    tcPr.append(borders)


def _set_col_widths(table, widths_cm):
    table.autofit = False
    for row in table.rows:
        for idx, width in enumerate(widths_cm):
