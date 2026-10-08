import io
import os
import re
from datetime import date
from xml.sax.saxutils import escape

import pdfplumber
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    KeepTogether, PageBreak
)

APP_NAME = "VinLookUpNow Report Studio"
NAVY = colors.HexColor("#10243A")
BLUE = colors.HexColor("#0878F9")
CYAN = colors.HexColor("#13C8E8")
INK = colors.HexColor("#172333")
MUTED = colors.HexColor("#657386")
PALE = colors.HexColor("#EEF6FF")
LINE = colors.HexColor("#DCE5EF")
BG = "#F3F6FA"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "vinlookupnow-logo.png")

st.set_page_config(page_title=APP_NAME, page_icon="🚘", layout="wide")
st.markdown("""
<style>
  .stApp { background: #f3f6fa; color: #172333; }
  .block-container { max-width: 1180px; padding-top: 1.3rem; padding-bottom: 3rem; }
  .brandbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1rem 1.25rem; background:#10243a; border-radius:18px; margin-bottom:1rem; box-shadow:0 10px 30px rgba(16,36,58,.12); }
  .brandbar img { width:230px; max-width:55%; height:auto; object-fit:contain; }
  .brandtag { color:#b9c9dc; font-size:.76rem; letter-spacing:.16em; text-transform:uppercase; text-align:right; }
  .hero { background:linear-gradient(120deg,#10243a 0%,#174c7f 65%,#0878f9 100%); border-radius:20px; padding:1.6rem 1.7rem; color:#fff; margin-bottom:1.15rem; }
  .hero .eyebrow { text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; color:#aeefff; font-weight:700; }
  .hero h1 { color:#fff; font-size:2.15rem; line-height:1.15; margin:.4rem 0 .55rem 0; }
  .hero p { color:#e0ebf8; font-size:1rem; margin:0; max-width:760px; }
  .panel { background:white; border:1px solid #e1e8f0; border-radius:16px; padding:1.15rem 1.25rem; box-shadow:0 4px 18px rgba(24,49,78,.035); }
  .notice { background:#fff8e7; border:1px solid #f3dfaa; border-left:5px solid #e4aa24; padding:.9rem 1rem; border-radius:12px; color:#5d4816; margin:1rem 0 1.2rem; }
  div[data-testid="stFileUploader"] { background:white; padding:1.1rem; border-radius:14px; border:1px dashed #9eb4ca; }
  div.stButton > button, div.stDownloadButton > button { border-radius:10px; min-height:2.8rem; font-weight:700; }
  h2, h3 { color:#10243a; }
  [data-testid="stMetric"] { background:white; border:1px solid #e1e8f0; padding:1rem; border-radius:14px; }
  .smallmuted { color:#6c7b8d; font-size:.86rem; }
</style>
""", unsafe_allow_html=True)

if os.path.exists(LOGO_PATH):
    st.markdown(f'<div class="brandbar"><img src="data:image/png;base64,{__import__("base64").b64encode(open(LOGO_PATH,"rb").read()).decode()}" alt="VinLookUpNow logo"><div class="brandtag">Vehicle history<br>report studio</div></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="brandbar"><strong style="color:white;font-size:1.6rem">VINLOOKUPNOW</strong><div class="brandtag">Vehicle history<br>report studio</div></div>', unsafe_allow_html=True)

st.markdown('''<div class="hero"><div class="eyebrow">Upload · Review · Redesign</div><h1>Make vehicle reports easier to read.</h1><p>Turn a text-based vehicle-history PDF into a polished, branded reading copy with a clear summary, structured sections, and consistent typography.</p></div>''', unsafe_allow_html=True)
st.markdown('''<div class="notice"><b>Source transparency:</b> This tool reformats the PDF you upload. It does not verify, create, or issue the underlying vehicle-history data. The exported file is clearly marked as a reformatted copy and retains source attribution.</div>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Report design")
    accent = st.color_picker("Brand accent", "#0878F9")
    st.caption("This accent is applied to section rules and highlights in the exported PDF.")
    st.divider()
    st.markdown("### Workflow")
    st.markdown("1. Upload the original PDF\n2. Check the detected vehicle and VIN\n3. Preview the extracted text\n4. Export the redesigned PDF")
    st.caption("Text-based PDFs work best. Scanned/image-only reports need OCR.")

uploaded = st.file_uploader("Upload a GoodCar or other vehicle-history report", type=["pdf"], help="Choose the original PDF from your device.")

SECTION_NAMES = {
    "Vehicle Data", "Vehicle profile", "Mileage", "Title Records", "Ownership History",
    "Junk/Salvage Records", "Total Loss Records", "Title Issues (Title Brands)",
    "Sales History", "Past Recalls", "Maintenance Schedule", "Vehicle specifications",
    "Auto Specs", "Crash Test Ratings", "Awards and Accolades", "Warranties",
    "Cost of Ownership", "Consumer Access Product Disclaimer", "Disclaimer",
    "Vehicle Information", "Accident History", "Damage History", "Theft Records",
    "Open Recalls", "Market Value", "Ownership Cost", "Safety Ratings"
}

def clean_lines(full_text, vin):
    result = []
    for raw_line in full_text.splitlines():
        line = re.sub(r"[\t ]+", " ", raw_line).strip()
        if not line:
            if result and result[-1] != "":
                result.append("")
            continue
        if re.match(r'^\s*(Report generated on|Page\s+\d+\s+of\s+\d+|Report on\s+.{0,120})\s*$', line, re.I):
            continue
        if vin and line.upper() == vin.upper():
            continue
        result.append(line)
    while result and result[-1] == "":
        result.pop()
    return result

def section_like(line):
    if line in SECTION_NAMES:
        return True
    if re.match(r'^(Recall\s*#?\s*\d+|Historical Title\s*#?\s*\d+|Current Title|Listing\s*\d+|Recall\s+\d+)$', line, re.I):
        return True
    # Common headings often extracted without exact capitalization.
    if len(line) < 58 and len(line.split()) <= 7 and line == line.title() and not re.search(r'\d{4,}|https?://', line):
        return line.lower() in {x.lower() for x in SECTION_NAMES}
    return False

def make_pdf(full_text, vehicle_name, vin, source_name, accent_hex):
    output = io.BytesIO()
    accent_color = colors.HexColor(accent_hex)
    logo = LOGO_PATH if os.path.exists(LOGO_PATH) else None
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, alignment=TA_LEFT, textColor=NAVY, spaceAfter=6))
    styles.add(ParagraphStyle(name="Kicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=accent_color, tracking=1.4, spaceAfter=8))
    styles.add(ParagraphStyle(name="SectionCustom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=11, spaceAfter=7, keepWithNext=True))
    styles.add(ParagraphStyle(name="SubHeadingCustom", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=accent_color, spaceBefore=7, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK, spaceAfter=4, splitLongWords=1, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="MetaCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED, spaceAfter=3))
    styles.add(ParagraphStyle(name="NoticeCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.5, textColor=NAVY, spaceAfter=0))
    styles.add(ParagraphStyle(name="CardLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.3, leading=9, textColor=MUTED, spaceAfter=4))
    styles.add(ParagraphStyle(name="CardValue", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=accent_color))

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = letter
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 7, w, 7, stroke=0, fill=1)
        canvas.setFillColor(accent_color)
        canvas.rect(0, h - 10, w * .32, 3, stroke=0, fill=1)
        if doc.page > 1 and logo:
            try:
                canvas.drawImage(logo, .58*inch, h - .50*inch, width=1.28*inch, height=.30*inch, preserveAspectRatio=True, mask='auto', anchor='c')
            except Exception:
                pass
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.6)
        canvas.line(.58*inch, .52*inch, w-.58*inch, .52*inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(.58*inch, .32*inch, "VINLOOKUPNOW.COM  ·  REFORMATTED SOURCE COPY")
        canvas.drawRightString(w-.58*inch, .32*inch, f"{doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=.62*inch, leftMargin=.62*inch, topMargin=.72*inch, bottomMargin=.68*inch, title=f"{vehicle_name} | VinLookUpNow reformatted copy", author="VinLookUpNow Report Studio")
    story = []
    # Cover / report identity
    if logo:
        from reportlab.platypus import Image as RLImage
        logo_img = RLImage(logo, width=2.25*inch, height=.90*inch, kind='proportional')
        logo_img.hAlign = 'LEFT'
        story.append(logo_img)
    else:
        story.append(Paragraph("VINLOOKUPNOW", styles["CoverTitle"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("VEHICLE HISTORY REPORT  /  REFORMATTED COPY", styles["Kicker"]))
    story.append(Paragraph(escape(vehicle_name or "Vehicle History Report"), styles["CoverTitle"]))
    if vin:
        vin_cell = Paragraph(f"<font color='{accent_hex}'><b>VIN</b></font><br/><font size='10'>{escape(vin)}</font>", styles["BodyCustom"])
    else:
        vin_cell = Paragraph("<b>VIN</b><br/>Not detected — please verify source", styles["BodyCustom"])
    date_cell = Paragraph(f"<font color='#657386'><b>REPORT REFORMATTED</b></font><br/>{date.today().strftime('%B %d, %Y')}", styles["BodyCustom"])
    source_cell = Paragraph(f"<font color='#657386'><b>ORIGINAL SOURCE</b></font><br/>{escape(source_name)}", styles["BodyCustom"])
    identity = Table([[vin_cell, date_cell], [source_cell, Paragraph("<b>FORMAT</b><br/>Reading copy of uploaded report", styles["BodyCustom"])]], colWidths=[3.45*inch, 3.45*inch], rowHeights=None)
    identity.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PALE), ("BOX", (0,0), (-1,-1), .6, LINE),
        ("INNERGRID", (0,0), (-1,-1), .5, LINE), ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10), ("TOPPADDING", (0,0), (-1,-1), 9), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "TOP")
    ]))
    story.append(identity)
    story.append(Spacer(1, 12))
    notice = Table([[Paragraph("<b>SOURCE & AUTHENTICITY NOTICE</b><br/>This document is a redesigned reading copy generated from a user-uploaded PDF. VinLookUpNow has not independently verified or issued the underlying vehicle-history data. Refer to the original report and its provider for authoritative source information. No missing records have intentionally been filled in.", styles["NoticeCustom"])]], colWidths=[6.9*inch])
    notice.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF8E7")),("BOX",(0,0),(-1,-1),.6,colors.HexColor("#F0DCA7")),("LINEBEFORE",(0,0),(0,-1),4,colors.HexColor("#E4AA24")),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9)]))
    story.append(notice)
    story.append(Spacer(1, 14))

    lines = clean_lines(full_text, vin)
    # Create a prominent dashboard from only values we can directly detect in source text.
    joined = "\n".join(lines)
    mileage_match = re.search(r'(?i)\b([\d,]{3,})\s*(?:miles|mi)\b', joined)
    title_count = re.search(r'(?i)(\d+)\s+(?:title )?records? found', joined)
    ownership_count = re.search(r'(?i)(\d+)\s+records? found.{0,35}ownership', joined)
    cards = []
    if mileage_match:
        cards.append(("MILEAGE FOUND", mileage_match.group(1) + " miles"))
    if title_count:
        cards.append(("TITLE RECORDS", title_count.group(1) + " found"))
    if ownership_count:
        cards.append(("OWNERSHIP", ownership_count.group(1) + " records"))
    if cards:
        card_data = []
        for label, value in cards[:3]:
            card_data.append([Paragraph(escape(label), styles["CardLabel"]), Paragraph(escape(value), styles["CardValue"])])
        while len(card_data) < 3:
            card_data.append([Paragraph("REPORT CONTENT", styles["CardLabel"]), Paragraph("See details below", styles["CardValue"])])
        dashboard = Table([card_data], colWidths=[2.3*inch]*3)
        dashboard.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.white),("BOX",(0,0),(-1,-1),.7,LINE),("INNERGRID",(0,0),(-1,-1),.6,LINE),
            ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),
            ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),("VALIGN",(0,0),(-1,-1),"TOP")
        ]))
        story.append(dashboard)
        story.append(Spacer(1, 13))

    story.append(Paragraph("REPORT DETAILS", styles["Kicker"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=accent_color, spaceAfter=7))
    last_blank = False
    for line in lines:
        if not line:
            if not last_blank:
                story.append(Spacer(1, 3))
            last_blank = True
            continue
        last_blank = False
        if section_like(line):
            story.append(KeepTogether([Spacer(1, 3), Paragraph(escape(line.upper()), styles["SectionCustom"]), HRFlowable(width="100%", thickness=.55, color=LINE, spaceAfter=5)]))
        elif re.match(r'^(Recall\s*#?\s*\d+|Historical Title\s*#?\s*\d+|Current Title|Listing\s*\d+)$', line, re.I):
            story.append(Paragraph(escape(line), styles["SubHeadingCustom"]))
        elif len(line) < 70 and (line.endswith(":") or re.match(r'^(Year|Make|Model|Trim|Engine|Body Style|Transmission|Fuel Type|VIN|Mileage|Odometer)\b', line, re.I)):
            story.append(Paragraph(f"<b>{escape(line)}</b>", styles["BodyCustom"]))
        else:
            story.append(Paragraph(escape(line), styles["BodyCustom"]))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return output.getvalue()

if uploaded:
    raw = uploaded.getvalue()
    if len(raw) > 30 * 1024 * 1024:
        st.error("This file is larger than 30 MB. Please upload a smaller PDF.")
        st.stop()
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = [p.extract_text(layout=False) or "" for p in pdf.pages]
            page_count = len(pdf.pages)
    except Exception as exc:
        st.error(f"Could not read this PDF: {exc}")
        st.stop()
    full_text = "\n".join(pages)
    if not full_text.strip():
        st.error("No selectable text was found. This version needs a text-based PDF; scanned PDFs require OCR first.")
        st.stop()
    vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', full_text.upper())
    vin_default = vin_match.group(0) if vin_match else ""
    vehicle_default = "Vehicle History Report"
    for line in full_text.splitlines():
        cleaned = re.sub(r'\s+', ' ', line).strip()
        if re.search(r'\b(19|20)\d{2}\b', cleaned) and not re.search(r'\b(VIN|vehicle history report|report on)\b', cleaned, re.I) and len(cleaned) < 100:
            if not re.match(r'^(page|report generated|disclaimer)', cleaned, re.I):
                vehicle_default = cleaned
                break
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("PDF pages", page_count)
    m2.metric("Text extracted", f"{len(full_text):,} chars")
    m3.metric("VIN detection", "Found" if vin_default else "Check manually")
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        vehicle_name = st.text_input("Vehicle title", value=vehicle_default[:100])
    with c2:
        vin = st.text_input("VIN (verify against original)", value=vin_default, max_chars=17).strip().upper()
    with st.expander("Preview extracted source text", expanded=False):
        st.caption("Check for missing or flattened table values before exporting.")
        st.text_area("Extracted text", value=full_text[:100000], height=280, disabled=True, label_visibility="collapsed")
    if st.button("✨ Generate redesigned PDF", type="primary", use_container_width=True):
        if vin and not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}', vin):
            st.error("VIN should be 17 valid VIN characters. Correct it or leave it blank if the source contains no VIN.")
            st.stop()
        try:
            pdf_bytes = make_pdf(full_text, vehicle_name, vin, uploaded.name, accent)
            st.success("Your redesigned report is ready.")
            st.download_button("Download redesigned report", data=pdf_bytes, file_name="vinlookupnow-reformatted-source-copy.pdf", mime="application/pdf", type="primary", use_container_width=True)
            st.caption("Always compare the exported copy with the source PDF. Text extraction can flatten complex tables.")
        except Exception as exc:
            st.error(f"Could not generate the PDF: {exc}")
else:
    st.markdown("### Your workflow")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel"><h3>01 · Upload</h3><p>Choose a GoodCar or other text-based vehicle-history PDF.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><h3>02 · Review</h3><p>Confirm the vehicle title, VIN, and extracted report text.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel"><h3>03 · Export</h3><p>Get a redesigned PDF with branded headings, summary cards, and source notice.</p></div>', unsafe_allow_html=True)
    st.write("")
    st.caption("Design note: the export now uses the VinLookUpNow logo, a branded report header, a vehicle identity panel, a source notice, summary cards when values are detected, section dividers, and consistent typography.")
