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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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


def _malumotnoma_rows(data: dict):
    return [
        [("birth_date", data["birth_date"]), ("birth_place", data["birth_place"])],
        [("nationality", data["nationality"]), None],
        [("education_level", data["education_level"]), ("education_detail", data["education_detail"])],
        [("specialty", data["specialty"]), None],
        [("academic_degree", data["academic_degree"]), ("academic_title", data["academic_title"])],
        [("foreign_lang", data["foreign_lang"]), ("military_title", data["military_title"])],
        [("state_awards", data["state_awards"]), None],
    ]


def _set_fixed_layout(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)


def _remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def generate_malumotnoma_docx(lang_key: str, data: dict) -> str:
    L = LABELS[lang_key]
    doc = Document()
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(12)

    for section in doc.sections:
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run(L["doc_title"])
    r.bold = True
    r.font.size = Pt(16)

    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = name_p.add_run(data["full_name"])
    r.bold = True
    r.font.size = Pt(13)

    doc.add_paragraph()

    rows = _malumotnoma_rows(data)
    table = doc.add_table(rows=len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _remove_table_borders(table)
    _set_fixed_layout(table)
    table.columns[0].width = Cm(8.2)
    table.columns[1].width = Cm(8.2)

    def fill_cell(cell, label_key, value):
        cell.paragraphs[0].text = ""
        p1 = cell.paragraphs[0]
        run1 = p1.add_run(L[label_key])
        run1.bold = True
        run1.font.size = Pt(11)
        p2 = cell.add_paragraph(str(value))
        if p2.runs:
            p2.runs[0].font.size = Pt(11)

    for i, row_pairs in enumerate(rows):
        left, right = row_pairs
        left_cell = table.cell(i, 0)
        right_cell = table.cell(i, 1)
        if right is None:
            merged = left_cell.merge(right_cell)
            merged.width = Cm(16.4)
            fill_cell(merged, left[0], left[1])
        else:
            left_cell.width = Cm(8.2)
            right_cell.width = Cm(8.2)
            fill_cell(left_cell, left[0], left[1])
            fill_cell(right_cell, right[0], right[1])

    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = heading.add_run(L["work_history_heading"])
    r.bold = True
    r.font.size = Pt(13)

    doc.add_paragraph()

    work_table = doc.add_table(rows=len(data["work_history"]), cols=3)
    work_table.autofit = False
    _remove_table_borders(work_table)
    _set_fixed_layout(work_table)
    widths = [Cm(3.4), Cm(0.6), Cm(12.5)]
    work_table.columns[0].width = widths[0]
    work_table.columns[1].width = widths[1]
    work_table.columns[2].width = widths[2]
    for row_idx, entry in enumerate(data["work_history"]):
        cells = work_table.rows[row_idx].cells
        cells[0].text = entry["years"]
        cells[1].text = "-"
        cells[2].text = entry["position"]
        for col_idx, w in enumerate(widths):
            cells[col_idx].width = w

    path = _unique_path("docx")
    doc.save(path)
    return path


def generate_relatives_docx(lang_key: str, data: dict) -> str:
    L = LABELS[lang_key]
    doc = Document()
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(12)

    for section in doc.sections:
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)

    title_text = L["rel_title_tpl"].format(name=data["full_name"])
    for line in title_text.split("\n"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        r.bold = True
        r.font.size = Pt(14)

    doc.add_paragraph()

    headers = [
        L["rel_col_relation"], L["rel_col_name"], L["rel_col_birth"],
        L["rel_col_work"], L["rel_col_address"],
    ]
    relatives = data["relatives"]
    table = doc.add_table(rows=len(relatives) + 1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for col_idx, htext in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(htext)
        r.bold = True
        r.font.size = Pt(10)

    for row_idx, rel in enumerate(relatives, start=1):
        values = [rel["relation_label"], rel["name"], rel["birth"], rel["work"], rel["address"]]
        for col_idx, val in enumerate(values):
            cell = table.cell(row_idx, col_idx)
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx > 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size = Pt(10)

    col_widths = [Cm(2.8), Cm(3.8), Cm(3.3), Cm(3.8), Cm(3.3)]
    for row in table.rows:
        for col_idx, w in enumerate(col_widths):
            row.cells[col_idx].width = w

    path = _unique_path("docx")
    doc.save(path)
    return path


def _pdf_styles():
    _register_pdf_fonts()
    title_style = ParagraphStyle(
        "title", fontName="DejaVuSans-Bold", fontSize=15, alignment=TA_CENTER, leading=18,
    )
    name_style = ParagraphStyle(
        "name", fontName="DejaVuSans-Bold", fontSize=12, alignment=TA_CENTER,
        spaceAfter=10, leading=15,
    )
    cell_style = ParagraphStyle(
        "cell", fontName="DejaVuSans", fontSize=9.5, alignment=TA_LEFT, leading=12,
    )
    cell_bold_style = ParagraphStyle(
        "cell_bold", fontName="DejaVuSans-Bold", fontSize=9.5, alignment=TA_LEFT, leading=12,
    )
    header_style = ParagraphStyle(
        "header", fontName="DejaVuSans-Bold", fontSize=9.5, alignment=TA_CENTER, leading=12,
    )
    return title_style, name_style, cell_style, cell_bold_style, header_style


def generate_malumotnoma_pdf(lang_key: str, data: dict) -> str:
    L = LABELS[lang_key]
    title_style, name_style, cell_style, cell_bold_style, header_style = _pdf_styles()

    path = _unique_path("pdf")
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2 * rl_cm, rightMargin=1.5 * rl_cm,
        topMargin=1.5 * rl_cm, bottomMargin=1.5 * rl_cm,
    )
    elements = [
        Paragraph(L["doc_title"], title_style),
        Spacer(1, 6),
        Paragraph(data["full_name"], name_style),
        Spacer(1, 10),
    ]

    rows = _malumotnoma_rows(data)
    table_data = []
    span_commands = []
    for i, row_pairs in enumerate(rows):
        left, right = row_pairs
        left_cell = Paragraph(f"<b>{L[left[0]]}</b><br/>{left[1]}", cell_style)
        if right is None:
            table_data.append([left_cell, ""])
            span_commands.append(("SPAN", (0, i), (1, i)))
        else:
            right_cell = Paragraph(f"<b>{L[right[0]]}</b><br/>{right[1]}", cell_style)
            table_data.append([left_cell, right_cell])

    col_width = (A4[0] - 2.2 * rl_cm - 1.5 * rl_cm) / 2
    info_table = Table(table_data, colWidths=[col_width, col_width])
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ] + span_commands
    info_table.setStyle(TableStyle(style_cmds))
    elements.append(info_table)

    elements.append(Spacer(1, 14))
    elements.append(Paragraph(f"<b>{L['work_history_heading']}</b>", name_style))
    elements.append(Spacer(1, 6))

    work_rows = []
    for entry in data["work_history"]:
        work_rows.append([
            Paragraph(entry["years"], cell_style),
            Paragraph("-", cell_style),
            Paragraph(entry["position"], cell_style),
        ])
    work_table = Table(
        work_rows,
        colWidths=[3.2 * rl_cm, 0.5 * rl_cm, (A4[0] - 2.2 * rl_cm - 1.5 * rl_cm - 3.7 * rl_cm)],
    )
    work_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(work_table)

    doc.build(elements)
    return path


def generate_relatives_pdf(lang_key: str, data: dict) -> str:
    L = LABELS[lang_key]
    title_style, name_style, cell_style, cell_bold_style, header_style = _pdf_styles()

    path = _unique_path("pdf")
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=1.3 * rl_cm, rightMargin=1.3 * rl_cm,
        topMargin=1.5 * rl_cm, bottomMargin=1.5 * rl_cm,
    )

    title_text = L["rel_title_tpl"].format(name=data["full_name"])
    elements = [Paragraph(title_text.replace("\n", "<br/>"), title_style), Spacer(1, 14)]

    headers = [
        L["rel_col_relation"], L["rel_col_name"], L["rel_col_birth"],
        L["rel_col_work"], L["rel_col_address"],
    ]
    table_data = [[Paragraph(h, header_style) for h in headers]]
    for rel in data["relatives"]:
        table_data.append([
            Paragraph(rel["relation_label"], cell_style),
            Paragraph(rel["name"], cell_style),
            Paragraph(rel["birth"], cell_style),
            Paragraph(rel["work"], cell_style),
            Paragraph(rel["address"], cell_style),
        ])

    usable_width = A4[0] - 2.6 * rl_cm
    col_widths = [w * usable_width for w in (0.15, 0.23, 0.19, 0.23, 0.20)]
    rel_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    rel_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(rel_table)

    doc.build(elements)
    return path


def generate(doc_type: str, lang_key: str, data: dict, fmt: str) -> str:
    """
    doc_type: 'malumotnoma' | 'relatives'
    fmt:      'pdf' | 'docx'
    """
    mapping = {
        ("malumotnoma", "docx"): generate_malumotnoma_docx,
        ("malumotnoma", "pdf"): generate_malumotnoma_pdf,
        ("relatives", "docx"): generate_relatives_docx,
        ("relatives", "pdf"): generate_relatives_pdf,
    }
    key = (doc_type, fmt)
    if key not in mapping:
        raise ValueError(f"Noma'lum kombinatsiya: {key}")
    return mapping[key](lang_key, data)
