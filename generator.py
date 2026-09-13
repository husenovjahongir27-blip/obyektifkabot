        for rr in p2.runs:
            rr.font.name = "Times New Roman"
            rr.font.size = Pt(14)
    for i, row_pairs in enumerate(rows):
        left, right = row_pairs
        left_cell, right_cell = table.cell(i, 0), table.cell(i, 1)
        if right is None:
            merged = left_cell.merge(right_cell); merged.width = Cm(16.4); fill_cell(merged, left[0], left[1])
        else:
            left_cell.width = Cm(8.2); right_cell.width = Cm(8.2)
            fill_cell(left_cell, left[0], left[1]); fill_cell(right_cell, right[0], right[1])

    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.paragraph_format.line_spacing = 1.15
    heading.paragraph_format.space_before = Pt(0)
    heading.paragraph_format.space_after = Pt(0)
    r = heading.add_run(L["work_history_heading"])
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    doc.add_paragraph()
    work_table = doc.add_table(rows=len(data["work_history"]), cols=3)
    work_table.autofit = False; _remove_table_borders(work_table); _set_fixed_layout(work_table)
    widths = [Cm(3.4), Cm(0.6), Cm(12.5)]
    for i, entry in enumerate(data["work_history"]):
        cells = work_table.rows[i].cells
        cells[0].text = entry["years"]; cells[1].text = "-"; cells[2].text = entry["position"]
        for j,w in enumerate(widths):
            cells[j].width=w
            for para in cells[j].paragraphs:
                para.paragraph_format.line_spacing = 1.15
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                for run in para.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(14)

    if data.get("relatives"):
        _add_relatives_docx_section(doc, lang_key, data)
    path = _unique_path("docx")
    doc.save(path)
    return path


def _add_relatives_pdf_section(elements, lang_key: str, data: dict):
    L = LABELS[lang_key]
    title_style, name_style, cell_style, cell_bold_style, header_style = _pdf_styles()
    elements.append(PageBreak())
    title_text = L["rel_title_tpl"].format(name=data["full_name"])
    elements.append(Paragraph(title_text.replace("\n", "<br/>"), title_style))
    elements.append(Spacer(1, 14))
    headers = [L["rel_col_relation"], L["rel_col_name"], L["rel_col_birth"], L["rel_col_work"], L["rel_col_address"]]
    table_data = [[Paragraph(h, header_style) for h in headers]]
    for rel in data["relatives"]:
        table_data.append([Paragraph(str(rel["relation_label"]), cell_style), Paragraph(str(rel["name"]), cell_style), Paragraph(str(rel["birth"]), cell_style), Paragraph(str(rel["work"]), cell_style), Paragraph(str(rel["address"]), cell_style)])
    usable_width = A4[0] - 2.6 * rl_cm
    col_widths = [w * usable_width for w in (0.15, 0.23, 0.19, 0.23, 0.20)]
    rel_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    rel_table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.75, colors.black), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
    elements.append(rel_table)


def generate_combined_pdf(lang_key: str, data: dict) -> str:
    L = LABELS[lang_key]
    title_style, name_style, cell_style, cell_bold_style, header_style = _pdf_styles()
    path = _unique_path("pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2.2*rl_cm, rightMargin=1.5*rl_cm, topMargin=1.5*rl_cm, bottomMargin=1.5*rl_cm)
    elements = [Paragraph(L["doc_title"], title_style), Spacer(1, 6)]
    photo_stream = _photo_3x4_stream(data)
    if photo_stream:
        photo_flowable = Table([[RLImage(photo_stream, width=3 * rl_cm, height=4 * rl_cm)]],
                               colWidths=[3 * rl_cm], rowHeights=[4 * rl_cm])
        photo_flowable.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    else:
        photo_flowable = Spacer(3 * rl_cm, 4 * rl_cm)
    name_style_header = ParagraphStyle("name_header", parent=name_style, fontSize=14, leading=16.1, alignment=TA_CENTER)
    name_flowable = Paragraph(data["full_name"], name_style_header)
    header = Table([[name_flowable, photo_flowable]], colWidths=[col for col in (A4[0] - 2.2*rl_cm - 1.5*rl_cm - 3.6*rl_cm, 3.6*rl_cm)])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.extend([header, Spacer(1, 10)])
    rows = _malumotnoma_rows(data); table_data=[]; span_commands=[]
    for i,(left,right) in enumerate(rows):
        left_cell=Paragraph(f"<b>{L[left[0]]}</b><br/>{left[1]}", cell_style)
        if right is None: table_data.append([left_cell, ""]); span_commands.append(("SPAN",(0,i),(1,i)))
        else: table_data.append([left_cell, Paragraph(f"<b>{L[right[0]]}</b><br/>{right[1]}", cell_style)])
    col_width=(A4[0]-2.2*rl_cm-1.5*rl_cm)/2
    info_table=Table(table_data,colWidths=[col_width,col_width])
    info_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]+span_commands))
    elements.append(info_table); elements.append(Spacer(1,14)); elements.append(Paragraph(f"<b>{L['work_history_heading']}</b>", name_style)); elements.append(Spacer(1,6))
    work_rows=[[Paragraph(e["years"],cell_style),Paragraph("-",cell_style),Paragraph(e["position"],cell_style)] for e in data["work_history"]]
    work_table=Table(work_rows,colWidths=[3.2*rl_cm,0.5*rl_cm,(A4[0]-2.2*rl_cm-1.5*rl_cm-3.7*rl_cm)])
    work_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),4)])); elements.append(work_table)
    if data.get("relatives"): _add_relatives_pdf_section(elements, lang_key, data)
    doc.build(elements)
    return path

def generate(doc_type: str, lang_key: str, data: dict, fmt: str) -> str:
    """
    doc_type: 'malumotnoma' | 'relatives' | 'combined'
    fmt:      'pdf' | 'docx'
    """
    mapping = {
        ("malumotnoma", "docx"): generate_malumotnoma_docx,
        ("malumotnoma", "pdf"): generate_malumotnoma_pdf,
        ("relatives", "docx"): generate_relatives_docx,
        ("relatives", "pdf"): generate_relatives_pdf,
        ("combined", "docx"): generate_combined_docx,
        ("combined", "pdf"): generate_combined_pdf,
    }
    key = (doc_type, fmt)
    if key not in mapping:
        raise ValueError(f"Noma'lum kombinatsiya: {key}")
    return mapping[key](lang_key, data)
