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
