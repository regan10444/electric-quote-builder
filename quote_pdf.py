"""
quote_pdf.py — customer-facing quote PDF (no markup, no gas/drive costs shown)
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

YELLOW_HEX = colors.HexColor("#F5B800")
DARK_BG    = colors.HexColor("#1A1A1A")
MED_GRAY   = colors.HexColor("#BBBBBB")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
WHITE      = colors.white
BLACK      = colors.black


def generate_pdf(data: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.6*inch,   bottomMargin=0.75*inch,
    )
    styles = getSampleStyleSheet()
    story  = []

    s_company = ParagraphStyle("company", fontSize=22, fontName="Helvetica-Bold",
                               textColor=YELLOW_HEX, spaceAfter=2)
    s_sub     = ParagraphStyle("sub",     fontSize=10, fontName="Helvetica",
                               textColor=colors.HexColor("#888888"), spaceAfter=2)
    s_heading = ParagraphStyle("heading", fontSize=10, fontName="Helvetica-Bold",
                               textColor=colors.HexColor("#555555"), spaceBefore=8, spaceAfter=2)
    s_body    = ParagraphStyle("body",    fontSize=10, fontName="Helvetica",
                               textColor=BLACK, spaceAfter=4, leading=14)
    s_small   = ParagraphStyle("small",   fontSize=8,  fontName="Helvetica",
                               textColor=MED_GRAY)

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("⚡ Your Company Name", s_company),
        Table([
            [Paragraph(f"Estimate ID: {data.get('estimate_id','')}", s_sub)],
            [Paragraph(f"Date: {data.get('date','')}", s_sub)],
        ], colWidths=[2.2*inch])
    ]]
    header_table = Table(header_data, colWidths=[4*inch, 2.2*inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN",  (1,0), (1,-1), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Paragraph("Your Address | Your Phone | yourwebsite.com", s_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=YELLOW_HEX, spaceAfter=10))

    # ── Customer Info ─────────────────────────────────────────────────────────
    cust = data.get("customer", {})
    svc  = data.get("service_address", "")

    def addr_block(label, lines):
        return [Paragraph(label, s_heading)] + [Paragraph(l, s_body) for l in lines if l]

    bill_block = addr_block("BILL TO", [
        cust.get("name", ""), cust.get("address", ""),
        cust.get("phone", ""), cust.get("email", ""),
    ])
    svc_block = addr_block("SERVICE ADDRESS", [svc or cust.get("address", "")])

    max_rows = max(len(bill_block), len(svc_block))
    while len(bill_block) < max_rows: bill_block.append(Paragraph("", s_body))
    while len(svc_block)  < max_rows: svc_block.append(Paragraph("", s_body))

    addr_table = Table([[b, s] for b, s in zip(bill_block, svc_block)],
                       colWidths=[3.1*inch, 3.1*inch])
    addr_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(addr_table)
    story.append(Spacer(1, 10))

    desc = data.get("description", "")
    if desc:
        story.append(Paragraph("DESCRIPTION OF WORK", s_heading))
        story.append(Paragraph(desc, s_body))
        story.append(Spacer(1, 6))

    # ── Materials Table ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#DDDDDD"), spaceAfter=6))
    story.append(Paragraph("MATERIALS", s_heading))

    mat_rows = [["#", "Description", "Qty", "Unit Price", "Line Total"]]
    for i, item in enumerate(data.get("line_items", []), 1):
        mat_rows.append([
            str(i), item["name"], f"{item['qty']:.0f}",
            f"${item['unit_price']:.2f}", f"${item['line_total']:.2f}",
        ])

    mat_table = Table(mat_rows,
                      colWidths=[0.35*inch, 3.4*inch, 0.5*inch, 0.85*inch, 0.9*inch])
    mat_table.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), DARK_BG),
        ("TEXTCOLOR",      (0,0), (-1,0), YELLOW_HEX),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,0), 9),
        ("ALIGN",          (0,0), (-1,0), "CENTER"),
        ("FONTNAME",       (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,1), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("ALIGN",          (2,1), (-1,-1), "RIGHT"),
        ("ALIGN",          (0,1), (0,-1), "CENTER"),
        ("GRID",           (0,0), (-1,-1), 0.25, colors.HexColor("#DDDDDD")),
        ("TOPPADDING",     (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 4),
    ]))
    story.append(mat_table)
    story.append(Spacer(1, 10))

    # ── Cost Summary (customer-facing: materials + labor + total ONLY) ────────
    def _money(val):
        try:
            if isinstance(val, str):
                return float(val.replace("$","").replace(",",""))
            return float(val)
        except Exception:
            return 0.0

    breakdown   = data.get("breakdown", {})
    mat_total   = _money(breakdown.get("materials", 0))
    labor_total = _money(breakdown.get("labor", 0))
    markup_amt  = _money(breakdown.get("markup_amt", 0))
    grand_total = _money(data.get("total", 0))

    summary_rows = [
        ["Materials", f"${mat_total:,.2f}"],
        ["Labor",     f"${labor_total:,.2f}"],
    ]
    if markup_amt > 0:
        summary_rows.append(["Other Fees", f"${markup_amt:,.2f}"])
    sum_table = Table(summary_rows, colWidths=[2*inch, 1*inch], hAlign="RIGHT")
    sum_table.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("TEXTCOLOR",      (0,0), (0,-1), MED_GRAY),
        ("ALIGN",          (1,0), (1,-1), "RIGHT"),
        ("LINEBELOW",      (0,-1), (-1,-1), 1, colors.HexColor("#DDDDDD")),
        ("TOPPADDING",     (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 3),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 4))

    total_table = Table([["TOTAL ESTIMATE", f"${grand_total:,.2f}"]],
                        colWidths=[2*inch, 1*inch], hAlign="RIGHT")
    total_table.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,-1), 13),
        ("TEXTCOLOR",      (0,0), (-1,-1), YELLOW_HEX),
        ("ALIGN",          (1,0), (1,0), "RIGHT"),
        ("BACKGROUND",     (0,0), (-1,-1), DARK_BG),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (0,0), 8),
        ("RIGHTPADDING",   (-1,0), (-1,0), 8),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 16))

    # ── Notes / Terms ─────────────────────────────────────────────────────────
    notes = data.get("notes", "")
    if notes:
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#DDDDDD"), spaceAfter=6))
        story.append(Paragraph("NOTES & TERMS", s_heading))
        story.append(Paragraph(notes, s_body))
        story.append(Spacer(1, 12))

    # ── Signature ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#DDDDDD"), spaceAfter=16))
    sig_data = [[
        [Paragraph("Customer Signature", s_small),
         HRFlowable(width=2.5*inch, thickness=1, color=BLACK),
         Paragraph(" ", s_small)],
        [Paragraph("Date", s_small),
         HRFlowable(width=1.5*inch, thickness=1, color=BLACK),
         Paragraph(" ", s_small)],
    ]]
    story.append(Table(sig_data, colWidths=[3.5*inch, 2.7*inch]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Thank you for your business.",
                            ParagraphStyle("footer", fontSize=9, fontName="Helvetica",
                                           textColor=MED_GRAY, alignment=TA_CENTER)))
    doc.build(story)
