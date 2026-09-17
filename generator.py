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
            row.cells[idx].width = Cm(width)
    for idx, width in enumerate(widths_cm):
        table.columns[idx].width = Cm(width)


def _cell_paragraph(cell, text="", bold=False, size=FONT_SIZE, align=None,
                     space_after=Pt(0), italic=False, clear=True):
    if clear:
        p = cell.paragraphs[0]
        p.text = ""
    else:
        p = cell.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = space_after
    p.paragraph_format.space_before = Pt(0)
    if text:
        lines = str(text).split("\n")
        for idx, line in enumerate(lines):
            if idx > 0:
                run = p.add_run()
                run.add_break()
            run = p.add_run(line)
            _set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def _doc_paragraph(doc, text="", bold=False, size=FONT_SIZE, align=None,
                    space_after=Pt(4), space_before=Pt(0)):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = space_after
    p.paragraph_format.space_before = space_before
    if text:
        run = p.add_run(text)
        _set_run_font(run, size=size, bold=bold)
    return p


# ---------- Asosiy jadval: juftlik va yakka maydonlar ----------

def _add_pair_row(table, label1, value1, label2, value2):
    header_row = table.add_row()
    for cell, label in zip(header_row.cells, (label1, label2)):
        _cell_paragraph(cell, label, bold=True, space_after=Pt(0))

    value_row = table.add_row()
    for cell, value in zip(value_row.cells, (value1, value2)):
        _cell_paragraph(cell, value if value else "-", space_after=Pt(8))


def _add_single_row(table, label, value):
    header_row = table.add_row()
    header_row.cells[0].merge(header_row.cells[1])
    _cell_paragraph(header_row.cells[0], label, bold=True, space_after=Pt(0))

    value_row = table.add_row()
    value_row.cells[0].merge(value_row.cells[1])
    _cell_paragraph(value_row.cells[0], value if value else "-", space_after=Pt(8))


# ---------- Sarlavha qismi: F.I.Sh / lavozim / surat ----------

def _add_header_block(doc, data, photo_path, L):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    _remove_table_borders(table)
    _set_col_widths(table, [12.5, 4.5])

    left_cell, right_cell = table.rows[0].cells
    left_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    right_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    _cell_paragraph(left_cell, data.get("full_name", "-"), bold=True, size=Pt(14),
                     space_after=Pt(6))
    since_text = (data.get("position_since") or "").strip()
    if since_text and not since_text.endswith(":"):
        since_text += ":"
    _cell_paragraph(left_cell, since_text, space_after=Pt(2), clear=False)
    _cell_paragraph(left_cell, data.get("current_position", "-"), bold=True,
                     space_after=Pt(0), clear=False)

    _set_cell_border_box(right_cell)
    if photo_path and os.path.exists(photo_path):
        p = right_cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(photo_path, width=Cm(3), height=Cm(4))
    else:
        _cell_paragraph(
            right_cell,
            L.PHOTO_PLACEHOLDER,
            size=Pt(8.5), italic=True, align=WD_ALIGN_PARAGRAPH.CENTER,
        )

    return table


# ---------- 2-sahifa: yaqin qarindoshlari haqida jadval ----------

def _add_relatives_page(doc, data, L):
    relatives = data.get("relatives") or []
    if not relatives:
        return

    doc.add_page_break()

    full_name = data.get("full_name", "-")
    title = f"{full_name}{L.RELATIVES_TITLE_SUFFIX}"
    _doc_paragraph(doc, title, bold=True, size=Pt(12),
                   align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(0))
    _doc_paragraph(doc, L.RELATIVES_HEADING, bold=True, size=Pt(12),
                   align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(10))

    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders_single(table)
    _set_col_widths(table, [2.2, 3.7, 2.6, 5.2, 3.3])

    header_cells = table.rows[0].cells
    for cell, text in zip(header_cells, L.RELATIVES_HEADERS):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _cell_paragraph(cell, text, bold=True, size=Pt(10),
                        align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(0))

    for rel in relatives:
        row = table.add_row()
        values = [
            rel.get("relation", "-"),
            rel.get("full_name", "-"),
            rel.get("birth_info", "-"),
            rel.get("job_info", "-"),
            rel.get("address", "-"),
        ]
        for cell, value in zip(row.cells, values):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            _cell_paragraph(cell, value or "-", size=Pt(10),
                            align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(0))


# ---------- Asosiy generatsiya funksiyasi ----------

def generate_malumotnoma_docx(data: dict, output_path: str, photo_path: str | None = None,
                                lang_variant: str = "uz_cyr") -> str:
    """
    data kutilayotgan kalitlar:
        full_name, position_since, current_position,
        birth_date, birth_place, nationality, party_affiliation,
        education_level, graduated_from, specialty,
        academic_degree, academic_title, foreign_languages, military_title,
        state_awards, departmental_awards, elected_member,
        work_history (list[str]),
        relatives (list[dict]) — har biri:
            relation, full_name, birth_info, job_info, address

    lang_variant: "uz_cyr" (o'zbekcha-kirill), "uz_lat" (o'zbekcha-lotin)
                  yoki "ru" (ruscha) — hujjat band nomlari shu variantda chiqadi.
    """
    L = labels_module.get_label_set(lang_variant)
    doc = Document()

    section = doc.sections[0]
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1)
    section.left_margin = Cm(2)
    section.right_margin = Cm(1)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = FONT_NAME
    normal_style.font.size = FONT_SIZE
    rpr = normal_style.element.get_or_add_rPr()
    rFonts = rpr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rpr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), FONT_NAME)

    # Sarlavha
    _doc_paragraph(doc, L.TITLE, bold=True, size=Pt(14),
                   align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(8))

    _add_header_block(doc, data, photo_path, L)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Asosiy ma'lumotlar jadvali
    info_table = doc.add_table(rows=0, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    _remove_table_borders(info_table)
    _set_col_widths(info_table, [8.5, 8.5])

    _add_pair_row(info_table, L.BIRTH_LABELS[0], data.get("birth_date"),
                  L.BIRTH_LABELS[1], data.get("birth_place"))
    _add_pair_row(info_table, L.NATIONALITY_LABELS[0], data.get("nationality"),
                  L.NATIONALITY_LABELS[1], data.get("party_affiliation"))
    _add_pair_row(info_table, L.EDUCATION_LABELS[0], data.get("education_level"),
                  L.EDUCATION_LABELS[1], data.get("graduated_from"))
    _add_single_row(info_table, L.SPECIALTY_LABEL, data.get("specialty"))
    _add_pair_row(info_table, L.DEGREE_LABELS[0], data.get("academic_degree"),
                  L.DEGREE_LABELS[1], data.get("academic_title"))
    _add_pair_row(info_table, L.LANGUAGE_LABELS[0], data.get("foreign_languages"),
                  L.LANGUAGE_LABELS[1], data.get("military_title"))
    _add_single_row(info_table, L.STATE_AWARDS_LABEL, data.get("state_awards"))
    _add_single_row(info_table, L.DEPT_AWARDS_LABEL, data.get("departmental_awards"))
    _add_single_row(info_table, L.ELECTED_MEMBER_LABEL, data.get("elected_member"))

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # Mehnat faoliyati
    _doc_paragraph(doc, L.WORK_HEADING, bold=True, size=Pt(14),
                   align=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(6))

    work_history = data.get("work_history") or []
    for entry in work_history:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Cm(2.3)
        p.paragraph_format.first_line_indent = Cm(-2.3)
        run = p.add_run(entry)
        _set_run_font(run)

    # 2-sahifa: yaqin qarindoshlari haqida (agar kiritilgan bo'lsa)
    _add_relatives_page(doc, data, L)

    doc.save(output_path)
    return output_path


def convert_docx_to_pdf(docx_path: str, output_dir: str) -> str | None:
    """LibreOffice yordamida .docx faylni .pdf ga aylantiradi."""
    try:
        subprocess.run(
            [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", output_dir, docx_path,
            ],
            check=True,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None

    pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
    return pdf_path if os.path.exists(pdf_path) else None
