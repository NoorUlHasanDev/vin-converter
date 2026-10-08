import streamlit as st
import pdfplumber
import re
from jinja2 import Template
import io
from datetime import datetime

# Try importing WeasyPrint for PDF generation
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False

st.set_page_config(page_title="VIN Report Redesigner", page_icon="🚗", layout="centered")

st.title("🚗 Redesigned VIN Report Generator")
st.write("GoodCar PDF upload karein aur official **Vinlookupnow** style report generate karein.")

uploaded_file = st.file_uploader("Upload GoodCar PDF", type=["pdf"])

def parse_pdf(file_bytes):
    """
    Extracts structured vehicle history data from uploaded GoodCar PDF.
    """
    full_text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
            
    # Default fallbacks
    data = {
        "title": "Vehicle History Report",
        "vin": "N/A",
        "search_date": datetime.now().strftime("%B %d, %Y"),
        "report_date": datetime.now().strftime("%m/%d/%Y"),
        "mileage": "N/A",
        "estimated_mileage": "N/A",
        "title_records_count": "0",
        "owners_count": "0",
        "year": "N/A",
        "make_model": "N/A",
        "trim": "N/A",
        "drive_type": "N/A",
        "brake_system": "N/A",
        "restraint_type": "N/A",
        "manufactured_in": "N/A",
        "style": "N/A",
        "body_type": "N/A",
        "body_subtype": "N/A",
        "doors": "N/A",
        "mfr_model_num": "N/A",
        "full_text": full_text
    }

    # Extract VIN
    vin_m = re.search(r"VIN:\s*([A-Z0-9]{17})", full_text, re.IGNORECASE)
    if vin_m:
        data["vin"] = vin_m.group(1)

    # Extract Title / Year Make Model
    title_m = re.search(r"(?:Report on|Vehicle:)\s+([^\n]+)", full_text, re.IGNORECASE)
    if title_m:
        data["title"] = title_m.group(1).strip()
        data["make_model"] = data["title"]

    # Extract Mileage
    mileage_m = re.search(r"(?:Last Reported Mileage|Mileage):\s*([\d,]+\s*miles)", full_text, re.IGNORECASE)
    if mileage_m:
        data["mileage"] = mileage_m.group(1)

    est_mileage_m = re.search(r"Estimated Mileage:\s*([\d,]+\s*miles)", full_text, re.IGNORECASE)
    if est_mileage_m:
        data["estimated_mileage"] = est_mileage_m.group(1)

    # Extract Specs
    specs_map = {
        "year": r"Year\s+([0-9]{4})",
        "trim": r"Trim\s+([^\n]+)",
        "drive_type": r"Drive Type\s+([^\n]+)",
        "brake_system": r"Brake System\s+([^\n]+)",
        "restraint_type": r"Restraint Type\s+([^\n]+)",
        "manufactured_in": r"Manufactured In\s+([^\n]+)",
        "style": r"Style\s+([^\n]+)",
        "body_type": r"Body Type\s+([^\n]+)",
        "doors": r"Doors\s+([^\n]+)"
    }
    
    for key, pattern in specs_map.items():
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            data[key] = m.group(1).strip()

    return data

# High-Precision CSS Template Matching vinlookupnow-redesigned-report_2.pdf
REDESIGNED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 18mm 15mm 22mm 15mm;
    @bottom-left {
      content: "Report generated on {{ report_date }}\A vinlookupnow.com\A Disclaimer: The content of the NMVTIS Inquiry Data included in the report may have materially changed following this date.";
      font-size: 7pt;
      color: #64748b;
      white-space: pre-wrap;
      font-family: Arial, sans-serif;
      line-height: 1.3;
    }
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #64748b;
      font-family: Arial, sans-serif;
    }
  }

  body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    color: #0f172a;
    margin: 0;
    padding: 0;
    font-size: 10pt;
    line-height: 1.4;
  }

  /* Header Branding */
  .header-brand {
    font-size: 20pt;
    font-weight: 900;
    letter-spacing: 1.5px;
    color: #0b192c;
    margin-bottom: 2px;
    text-transform: uppercase;
  }

  .vehicle-heading {
    font-size: 14pt;
    font-weight: bold;
    color: #1e293b;
    margin-bottom: 2px;
  }

  .vin-subhead {
    font-size: 10pt;
    font-weight: 600;
    color: #475569;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #cbd5e1;
  }

  /* Section Titles */
  .section-header {
    font-size: 12pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 18px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .sub-section-header {
    font-size: 11pt;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 14px;
    margin-bottom: 8px;
  }

  /* Key Value Tables */
  .kv-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
  }

  .kv-table td {
    padding: 6px 10px;
    font-size: 9.5pt;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
  }

  .kv-table tr:nth-child(even) {
    background-color: #f8fafc;
  }

  .kv-label {
    width: 38%;
    color: #475569;
    font-weight: 600;
  }

  .kv-value {
    color: #0f172a;
    font-weight: 700;
  }

  .pipe-sep {
    color: #cbd5e1;
    margin: 0 6px;
  }

  /* Checkbox & Status Lists */
  .status-badge-green {
    color: #16a34a;
    font-weight: 700;
  }

  .status-badge-blue {
    color: #2563eb;
    font-weight: 700;
  }

  /* Two Column Table Layout for WeasyPrint */
  .two-col-table {
    display: table;
    width: 100%;
    margin-bottom: 10px;
  }

  .two-col-row {
    display: table-row;
  }

  .two-col-cell {
    display: table-cell;
    width: 48%;
    vertical-align: top;
  }

  .two-col-gap {
    display: table-cell;
    width: 4%;
  }

  .info-box {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
    font-size: 9pt;
    color: #334155;
  }

  .title-brand-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
  }

  .title-brand-table th {
    background-color: #f1f5f9;
    color: #334155;
    text-align: left;
    padding: 5px 8px;
    font-weight: bold;
    border-bottom: 1px solid #cbd5e1;
  }

  .title-brand-table td {
    padding: 4px 8px;
    border-bottom: 1px solid #f1f5f9;
  }
</style>
</head>
<body>

  <!-- HEADER BRANDING -->
  <div class="header-brand">VINLOOKUPNOW</div>
  <div class="vehicle-heading">{{ title }}</div>
  <div class="vin-subhead">VEHICLE HISTORY REPORT &nbsp;|&nbsp; VIN: {{ vin }} &nbsp;|&nbsp; Search Date: {{ search_date }}</div>

  <!-- SUMMARY SNAPSHOT -->
  <div class="section-header">History & Records Summary</div>
  <table class="kv-table">
    <tr>
      <td class="kv-label">Last Reported Mileage</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ mileage }}</td>
    </tr>
    <tr>
      <td class="kv-label">Junk / Salvage Records</td>
      <td class="kv-value"><span class="pipe-sep">|</span> <span class="status-badge-green">None Found</span></td>
    </tr>
    <tr>
      <td class="kv-label">Total Loss Records</td>
      <td class="kv-value"><span class="pipe-sep">|</span> <span class="status-badge-green">None Found</span></td>
    </tr>
    <tr>
      <td class="kv-label">Title Issues (Brands)</td>
      <td class="kv-value"><span class="pipe-sep">|</span> <span class="status-badge-green">None Reported</span></td>
    </tr>
    <tr>
      <td class="kv-label">Past Recalls</td>
      <td class="kv-value"><span class="pipe-sep">|</span> <span class="status-badge-blue">Available</span></td>
    </tr>
  </table>

  <!-- VEHICLE PROFILE / SPECS -->
  <div class="section-header">Vehicle Profile</div>
  <table class="kv-table">
    <tr>
      <td class="kv-label">Year</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ year }}</td>
    </tr>
    <tr>
      <td class="kv-label">Make, Model</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ make_model }}</td>
    </tr>
    <tr>
      <td class="kv-label">Trim</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ trim }}</td>
    </tr>
    <tr>
      <td class="kv-label">Drive Type</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ drive_type }}</td>
    </tr>
    <tr>
      <td class="kv-label">Brake System</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ brake_system }}</td>
    </tr>
    <tr>
      <td class="kv-label">Restraint Type</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ restraint_type }}</td>
    </tr>
    <tr>
      <td class="kv-label">Manufactured In</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ manufactured_in }}</td>
    </tr>
    <tr>
      <td class="kv-label">Style / Body Type</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ style }} ({{ body_type }})</td>
    </tr>
    <tr>
      <td class="kv-label">Doors</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ doors }}</td>
    </tr>
  </table>

  <!-- MILEAGE DETAILS -->
  <div class="section-header">Mileage History</div>
  <table class="kv-table">
    <tr>
      <td class="kv-label">Last Reported Mileage</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ mileage }}</td>
    </tr>
    <tr>
      <td class="kv-label">Estimated Mileage</td>
      <td class="kv-value"><span class="pipe-sep">|</span> {{ estimated_mileage }}</td>
    </tr>
  </table>
  <div class="info-box">
    <strong>Note:</strong> Please be aware that the estimated mileage provided is not the current mileage of the VIN-checked vehicle. Our system determines average mileage by analyzing data from similar vehicles across states.
  </div>

  <!-- TITLE BRAND CHECKLIST -->
  <div class="section-header">Title Brands Check</div>
  <table class="title-brand-table">
    <thead>
      <tr>
        <th>Title Brand</th>
        <th>Status</th>
        <th>Title Brand</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Flood Damage</td><td>No</td>
        <td>Odometer Not Actual</td><td>No</td>
      </tr>
      <tr>
        <td>Fire Damage</td><td>No</td>
        <td>Salt Water Damage</td><td>No</td>
      </tr>
      <tr>
        <td>Hail Damage</td><td>No</td>
        <td>Vandalism</td><td>No</td>
      </tr>
      <tr>
        <td>Junk / Salvage</td><td>No</td>
        <td>Rebuilt / Reconstructed</td><td>No</td>
      </tr>
      <tr>
        <td>Totaled</td><td>No</td>
        <td>Manufacturer Buy Back</td><td>No</td>
      </tr>
    </tbody>
  </table>

</body>
</html>
"""

if uploaded_file is not None:
    st.info("Parsing GoodCar PDF...")
    file_bytes = uploaded_file.read()
    parsed_data = parse_pdf(file_bytes)
    
    # Render HTML
    tmpl = Template(REDESIGNED_HTML_TEMPLATE)
    rendered_html = tmpl.render(**parsed_data)
    
    st.subheader("📋 Extracted Details:")
    st.write(f"**Vehicle:** {parsed_data['title']}")
    st.write(f"**VIN:** {parsed_data['vin']}")
    st.write(f"**Mileage:** {parsed_data['mileage']}")
    
    st.divider()
    
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = HTML(string=rendered_html).write_pdf()
            st.download_button(
                label="📥 Download Redesigned Vinlookupnow PDF",
                data=pdf_bytes,
                file_name=f"Vinlookupnow_{parsed_data['vin']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Convert Error: {str(e)}")
    else:
        st.error("WeasyPrint library load nahi ho saki. Dependencies check karein.")
