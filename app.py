import io
import re
from datetime import date

import pdfplumber
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, HRFlowable
from xml.sax.saxutils import escape

APP_NAME = "VinLookUpNow Report Studio"
NAVY = colors.HexColor("#14283F")
BLUE = colors.HexColor("#1F6FEB")
PALE = colors.HexColor("#EEF4FB")
GRAY = colors.HexColor("#5C6673")

st.set_page_config(page_title=APP_NAME, page_icon="🚘", layout="wide")
st.markdown("""
<style>
  .stApp { background: #f5f7fb; }
  .hero { padding: 1.25rem 1.5rem; border-radius: 16px; background: linear-gradient(115deg,#14283f,#24558b); color: white; margin-bottom: 1rem; }
  .hero h1 { margin: 0; font-size: 2rem; }
  .hero p { margin: .4rem 0 0; opacity: .9; }
  .notice { background: #fff8e6; border-left: 4px solid #d89b13; padding: .85rem 1rem; border-radius: 6px; color: #4b3b12; }
  div[data-testid="stFileUploader"] { background: white; padding: 1rem; border-radius: 12px; border: 1px dashed #9aaac0; }
</style>
<div class="hero"><h1>VinLookUpNow Report Studio</h1><p>Upload a vehicle-history PDF and generate a cleaner, branded reading copy.</p></div>
<div class="notice"><b>Source transparency:</b> This tool reformats the PDF you provide. It does not verify, create, or issue vehicle-history data. Every output is labeled as a reformatted copy of the uploaded source, with source attribution retained where available.</div>
""", unsafe_allow_html=True)

st.write("")
with st.sidebar:
    st.header("Report settings")
    accent = st.color_picker("Accent color", "#1F6FEB")
    include_source_notice = st.checkbox("Include source/provenance notice", value=True, disabled=True)
    st.caption("The source notice is always included to prevent the redesigned copy being mistaken for an original report issued by VinLookUpNow.")
    st.divider()
    st.caption("Recommended workflow: upload → review extracted details → download PDF → verify against the original.")

uploaded = st.file_uploader("Upload the original vehicle-history report (PDF)", type=["pdf"])
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
    vehicle_default = ""
    for line in full_text.splitlines():
        cleaned = re.sub(r'\s+', ' ', line).strip()
        if re.search(r'\b(19|20)\d{2}\b', cleaned) and re.search(r'\b(VIN|vehicle history report|report on)\b', cleaned, re.I) is False and len(cleaned) < 100:
            if not re.match(r'^(page|report generated|disclaimer)', cleaned, re.I):
                vehicle_default = cleaned
                break
    if not vehicle_default:
        vehicle_default = "Vehicle History Report"

    st.success(f"PDF read successfully — {page_count} pages, {len(full_text):,} extracted characters.")
    c1, c2 = st.columns(2)
    with c1:
        vehicle_name = st.text_input("Vehicle title shown on the redesigned report", value=vehicle_default[:100])
    with c2:
        vin = st.text_input("VIN (check this against the source PDF)", value=vin_default, max_chars=17).strip().upper()

    st.subheader("Review extracted source text")
    st.caption("This preview helps you catch extraction errors before generating the PDF. The output keeps source text rather than inventing missing records.")
    with st.expander("Show extracted text", expanded=False):
        st.text_area("Extracted content", value=full_text[:100000], height=300, disabled=True, label_visibility="collapsed")

    if st.button("Generate redesigned PDF", type="primary", use_container_width=True):
        if vin and not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}', vin):
            st.error("VIN should be 17 valid VIN characters. Correct it or leave it blank if the source contains no VIN.")
            st.stop()

        output = io.BytesIO()
        brand_color = colors.HexColor(accent)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="BrandTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=NAVY, alignment=TA_LEFT, spaceAfter=6))
        styles.add(ParagraphStyle(name="Vehicle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=GRAY, spaceAfter=3))
        styles.add(ParagraphStyle(name="SectionHeadingCustom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=NAVY, spaceBefore=11, spaceAfter=5, keepWithNext=True))
        styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.4, leading=11.2, textColor=colors.HexColor("#263445"), spaceAfter=3, splitLongWords=1, wordWrap="CJK"))
        styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=GRAY, spaceAfter=3))
        styles.add(ParagraphStyle(name="NoticeCustom", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=NAVY, backColor=PALE, borderPadding=7, spaceBefore=6, spaceAfter=10))

        def header_footer(canvas, doc):
            canvas.saveState()
            w, h = letter
            canvas.setFillColor(NAVY)
            canvas.rect(0, h - 0.18*inch, w, 0.18*inch, stroke=0, fill=1)
            canvas.setStrokeColor(colors.HexColor("#D9E1EB"))
            canvas.line(0.62*inch, 0.55*inch, w - 0.62*inch, 0.55*inch)
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(GRAY)
            canvas.drawString(0.62*inch, 0.35*inch, "VINLOOKUPNOW.COM  •  REFORMATTED SOURCE COPY")
            canvas.drawRightString(w - 0.62*inch, 0.35*inch, f"Page {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=.62*inch, leftMargin=.62*inch, topMargin=.58*inch, bottomMargin=.75*inch, title=f"{vehicle_name} — Reformatted Source Copy", author="VinLookUpNow Report Studio")
        story = []
        story.append(Paragraph("VinLookUpNow", styles["BrandTitle"]))
        story.append(Paragraph("VEHICLE HISTORY REPORT · REFORMATTED COPY", styles["Vehicle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=brand_color, spaceBefore=4, spaceAfter=12))
        story.append(Paragraph(escape(vehicle_name or "Vehicle History Report"), styles["Heading1"]))
        if vin:
            story.append(Paragraph(f"VIN: <b>{escape(vin)}</b>", styles["Vehicle"]))
        story.append(Paragraph(f"Reformatted on {date.today().strftime('%B %d, %Y')} · Original source file: {escape(uploaded.name)}", styles["SmallCustom"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("SOURCE AND AUTHENTICITY NOTICE: This document is a reformatted reading copy generated from a user-uploaded PDF. VinLookUpNow has not independently verified or issued the underlying vehicle-history data. Refer to the original report and its provider for authoritative source information. No missing data has intentionally been filled in.", styles["NoticeCustom"]))
        story.append(Paragraph("Extracted report content", styles["SectionHeadingCustom"]))
        story.append(Paragraph("The text below is taken from the uploaded report. Page headers and repeated page-number/footer lines may be omitted during cleanup; substantive source text and disclaimers are retained when extractable.", styles["SmallCustom"]))

        section_names = {
            "Vehicle Data", "Vehicle profile", "Mileage", "Title Records", "Ownership History", "Junk/Salvage Records", "Total Loss Records", "Title Issues (Title Brands)", "Sales History", "Past Recalls", "Maintenance Schedule", "Vehicle specifications", "Auto Specs", "Crash Test Ratings", "Awards and Accolades", "Warranties", "Cost of Ownership", "Consumer Access Product Disclaimer", "Disclaimer"
        }
        skip_patterns = [r'^\s*Report generated on .*$', r'^\s*Page\s+\d+\s+of\s+\d+\s*$', r'^\s*Report on .{0,120}$']
        last_was_blank = False
        for raw_line in full_text.splitlines():
            line = re.sub(r'[\t ]+', ' ', raw_line).strip()
            if not line:
                if not last_was_blank:
                    story.append(Spacer(1, 2))
                last_was_blank = True
                continue
            last_was_blank = False
            if any(re.match(p, line, re.I) for p in skip_patterns):
                continue
            if vin and line.upper() == vin:
                continue
            if line in section_names or re.match(r'^(Recall #\d+|Historical Title #\d+|Current Title|Listing \d+|Recall\s+\d+)$', line, re.I):
                story.append(Paragraph(escape(line), styles["SectionHeadingCustom"]))
            else:
                # Preserve the extracted line without guessing at table structure.
                story.append(Paragraph(escape(line), styles["BodyCustom"]))

        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        st.download_button("Download redesigned PDF", data=output.getvalue(), file_name="vinlookupnow-reformatted-source-copy.pdf", mime="application/pdf", type="primary", use_container_width=True)
        st.info("Before sharing, compare the output with the source PDF. Text-based extraction can flatten tables, and scanned/image-only PDFs are not supported in this starter version.")
else:
    st.markdown("### How it works")
    a, b, c = st.columns(3)
    a.markdown("**1. Upload**\n\nChoose a GoodCar vehicle-history PDF.")
    b.markdown("**2. Review**\n\nCheck the detected VIN and extracted text.")
    c.markdown("**3. Export**\n\nDownload a cleaner PDF with clear source attribution.")
    st.caption("This starter version supports text-based PDFs. OCR for scanned reports and more precise table reconstruction can be added later.")
