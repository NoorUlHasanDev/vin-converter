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
  .hero { background:#ffffff; border:1px solid #d8e6f4; border-radius:8px; padding:1.35rem 1.5rem; color:#10385e; margin-bottom:1.15rem; }
  .hero .eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; color:#0878f9; font-weight:700; }
  .hero h1 { color:#10385e; font-size:2.05rem; line-height:1.15; margin:.4rem 0 .55rem 0; }
  .hero p { color:#526b82; font-size:1rem; margin:0; max-width:760px; }
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
    """Render a close visual match to the user's supplied VinLookUpNow PDF."""
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.colors import HexColor
    output = io.BytesIO()
    blue = HexColor("#0878F9")
    ink = HexColor("#171B22")
    muted = HexColor("#687384")
    pale = HexColor("#EDF6FF")
    line = HexColor("#C9D8E8")
    navy = HexColor("#0C3154")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="VTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_LEFT, textColor=navy, spaceAfter=5))
    styles.add(ParagraphStyle(name="VSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.white, backColor=navy, borderPadding=(6,8,6,8), spaceBefore=9, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle(name="VSub", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=ink, spaceBefore=5, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="VBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.2, leading=11, textColor=ink, spaceAfter=3, splitLongWords=1, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="VSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.1, leading=9, textColor=muted, spaceAfter=2))
    styles.add(ParagraphStyle(name="VMetricLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=ink, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="VMetricValue", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=blue, alignment=TA_LEFT))

    def header_footer(canvas, doc):
        canvas.saveState(); w,h=letter
        # Deep-navy report masthead, matching the user's requested reference mockup.
        canvas.setFillColor(navy); canvas.rect(0, h-.78*inch, w, .78*inch, fill=1, stroke=0)
        if os.path.exists(LOGO_PATH):
            try: canvas.drawImage(LOGO_PATH, .48*inch, h-.66*inch, width=2.05*inch, height=.48*inch, preserveAspectRatio=True, mask='auto', anchor='c')
            except Exception: pass
        canvas.setFont('Helvetica-Bold', 7.4); canvas.setFillColor(colors.white)
        canvas.drawRightString(w-.52*inch, h-.30*inch, 'Trusted Vehicle History')
        canvas.setFont('Helvetica', 7); canvas.drawRightString(w-.52*inch, h-.44*inch, 'Vehicle report copy')
        canvas.setStrokeColor(line); canvas.setLineWidth(.65); canvas.line(.45*inch,.60*inch,w-.45*inch,.60*inch)
        canvas.setFillColor(muted); canvas.setFont('Helvetica',6.5)
        canvas.drawString(.48*inch,.41*inch,'Report generated on '+date.today().strftime('%m/%d/%Y'))
        canvas.drawCentredString(w/2,.41*inch,'vinlookupnow.com')
        canvas.drawRightString(w-.48*inch,.41*inch,f'Page {doc.page}')
        canvas.setFont('Helvetica-Oblique',5.5)
        canvas.drawString(.48*inch,.24*inch,'Reformatted from uploaded source; underlying data has not been independently verified.')
        canvas.restoreState()

    doc=SimpleDocTemplate(output,pagesize=letter,leftMargin=.55*inch,rightMargin=.55*inch,topMargin=.98*inch,bottomMargin=.74*inch,title=f'{vehicle_name} | VinLookUpNow',author='VinLookUpNow')
    story=[]
    lines=clean_lines(full_text,vin)
    joined='\n'.join(lines)
    story.append(Paragraph(escape(vehicle_name or 'Vehicle History Report'),styles['VTitle']))
    story.append(Paragraph('V E H I C L E   H I S T O R Y   R E P O R T',ParagraphStyle('SubTitle',parent=styles['VSmall'],textColor=ink,fontSize=8,leading=10,spaceAfter=9)))
    vinp=Paragraph(f'<font color="#0878F9"><b>VIN: {escape(vin or "Not detected")}</b></font>',styles['VBody'])
    datep=Paragraph('Search Date: '+date.today().strftime('%B %d, %Y'),ParagraphStyle('DateR',parent=styles['VBody'],alignment=2))
    meta=Table([[vinp,datep]],colWidths=[4.1*inch,2.8*inch])
    meta.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),pale),('BOX',(0,0),(-1,-1),.5,line),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story += [meta,Spacer(1,10)]
    # Match the supplied report's three-column blue summary strip using values found in source text.
    mileage=re.search(r'(?i)\b([\d,]{3,})\s*(?:miles|mi)\b',joined)
    titles=re.search(r'(?i)(\d+)\s+(?:title )?records? found',joined)
    owners=re.search(r'(?i)(\d+)\s+records? found.{0,35}ownership',joined)
    metric_values=[('Mileage',mileage.group(1)+' miles' if mileage else 'See details'),('Title Records',(titles.group(1)+' records found') if titles else 'See details'),('Ownership History',(owners.group(1)+' records found') if owners else 'See details')]
    cells=[]
    for label,value in metric_values:
        cells.append([Paragraph(escape(label),styles['VMetricLabel']),Spacer(1,5),Paragraph(escape(value),styles['VMetricValue'])])
    metrics=Table([cells],colWidths=[2.3*inch]*3)
    metrics.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),pale),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),11),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story += [metrics,Spacer(1,11)]
    story.append(Paragraph('Vehicle Data',styles['VSection']))
    # Detect simple key/value lines and render them as alternating blue-white rows.
    data_rows=[]
    for ln in lines:
        m=re.match(r'^(Year|Make,? Model|Make|Model|Trim|Drive Type|Brake System|Restraint Type|Manufactured In|Style|Body Type|Body Subtype|Doors|Mfr Model Number)\s*:?\s+(.+)$',ln,re.I)
        if m: data_rows.append([Paragraph(escape(m.group(1)),styles['VBody']),Paragraph(escape(m.group(2)),styles['VBody'])])
    if not data_rows:
        for label,value in [('Vehicle',vehicle_name or 'Vehicle History Report'),('VIN',vin or 'Not detected'),('Source file',source_name)]:
            data_rows.append([Paragraph(escape(label),styles['VBody']),Paragraph(escape(value),styles['VBody'])])
    dt=Table(data_rows[:12],colWidths=[3.45*inch,3.45*inch],repeatRows=0)
    ts=[('LINEBELOW',(0,0),(-1,-1),.45,line),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    for i in range(len(data_rows[:12])):
        if i%2==0: ts.append(('BACKGROUND',(0,i),(-1,i),pale))
    dt.setStyle(TableStyle(ts)); story.append(dt); story.append(Spacer(1,8))

    # Group content under source headings, retaining original wording and order.
    section_names={x.lower() for x in SECTION_NAMES}
    current=[]
    def flush_group():
        nonlocal current
        if current:
            rows=[]
            for ln in current:
                if not ln: continue
                if ':' in ln and len(ln.split(':',1)[0])<38:
                    k,v=ln.split(':',1)
                    rows.append([Paragraph('<b>'+escape(k.strip())+'</b>',styles['VBody']),Paragraph(escape(v.strip()),styles['VBody'])])
                else:
                    rows.append([Paragraph(escape(ln),styles['VBody'])])
            if rows:
                # Keep simple rows compact and use the target's pale-blue zebra-table treatment.
                normalized=[]
                for r in rows:
                    normalized.append(r if len(r)==2 else [r[0],Paragraph('',styles['VBody'])])
                t=Table(normalized,colWidths=[2.35*inch,4.55*inch],hAlign='LEFT')
                stl=[('LINEBELOW',(0,0),(-1,-1),.4,line),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('VALIGN',(0,0),(-1,-1),'TOP')]
                for i in range(len(normalized)):
                    if i%2==0: stl.append(('BACKGROUND',(0,i),(-1,i),pale))
                t.setStyle(TableStyle(stl)); story.append(t); story.append(Spacer(1,6))
        current=[]
    for ln in lines:
        if not ln: continue
        if section_like(ln):
            flush_group()
            story.append(Paragraph(escape(ln),styles['VSection']))

        else:
            current.append(ln)
    flush_group()
    story.append(Spacer(1,8))
    story.append(Paragraph('<b>Source file:</b> '+escape(source_name)+' &nbsp; | &nbsp; <b>Source notice:</b> This is a reformatted reading copy of the uploaded report. VinLookUpNow has not independently verified the underlying data.',styles['VSmall']))
    doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)
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
