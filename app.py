import streamlit as st
import pdfplumber
import re
from jinja2 import Template
import io

# Try importing WeasyPrint for PDF generation
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False

st.set_page_config(page_title="VIN Report Converter", page_icon="🚗", layout="centered")

st.title("🚗 VIN Report Converter")
st.write("GoodCar PDF upload karein aur Vinlookupnow style mein nayi report download karein.")

# File Uploader
uploaded_file = st.file_uploader("GoodCar PDF File Select Karein", type=["pdf"])

def parse_pdf(file_bytes):
    data = {
        "vin": "NOT FOUND",
        "year_make_model": "Vehicle History Report",
        "mileage": "N/A",
        "full_text": ""
    }
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
        
        data["full_text"] = full_text
        
        # 1. Extract VIN
        vin_match = re.search(r"VIN:\s*([A-Z0-9]{17})", full_text, re.IGNORECASE)
        if vin_match:
            data["vin"] = vin_match.group(1)
            
        # 2. Extract Mileage
        mileage_match = re.search(r"(?:Mileage|Odometer):\s*([\d,]+\s*(?:miles|mi)?)", full_text, re.IGNORECASE)
        if mileage_match:
            data["mileage"] = mileage_match.group(1)
            
        # 3. Extract Vehicle Title
        vehicle_match = re.search(r"Report on\s+([^\n]+)", full_text, re.IGNORECASE)
        if vehicle_match:
            data["year_make_model"] = vehicle_match.group(1).strip()

    return data

# WeasyPrint Compatible Vinlookupnow HTML/CSS Layout Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 12mm;
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #666666;
    }
  }
  body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    color: #1e293b;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .header {
    background-color: #003366 !important;
    color: #ffffff;
    padding: 18px;
    border-radius: 6px;
    margin-bottom: 20px;
  }
  .brand {
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 1px;
    color: #38bdf8;
  }
  .title {
    font-size: 18px;
    margin-top: 6px;
    font-weight: 600;
    color: #ffffff;
  }
  .vin-tag {
    font-size: 12px;
    background-color: #1e40af !important;
    color: #ffffff;
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    margin-top: 8px;
    font-family: monospace;
  }
  /* WeasyPrint CSS Table Layout (Flexbox alternative) */
  .grid-table {
    display: table;
    width: 100%;
    margin-bottom: 20px;
  }
  .grid-row {
    display: table-row;
  }
  .card-cell {
    display: table-cell;
    width: 48%;
    background-color: #f8fafc !important;
    padding: 15px;
    border-left: 4px solid #0056b3;
    border-radius: 4px;
    vertical-align: top;
  }
  .card-spacer {
    display: table-cell;
    width: 4%;
  }
  .label { 
    font-size: 10px; 
    color: #64748b; 
    text-transform: uppercase; 
    font-weight: bold; 
  }
  .value { 
    font-size: 16px; 
    font-weight: bold; 
    color: #0f172a; 
    margin-top: 4px; 
  }
  .section-title {
    font-size: 14px;
    font-weight: bold;
    color: #003366;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 5px;
    margin-top: 20px;
    margin-bottom: 10px;
  }
  .content-box {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0;
    padding: 15px;
    border-radius: 6px;
    font-size: 10.5pt;
    white-space: pre-wrap;
    line-height: 1.5;
    color: #334155;
  }
</style>
</head>
<body>
  <div class="header">
    <div class="brand">VINLOOKUPNOW</div>
    <div class="title">{{ year_make_model }}</div>
    <div class="vin-tag">VIN: {{ vin }}</div>
  </div>

  <div class="grid-table">
    <div class="grid-row">
      <div class="card-cell">
        <div class="label">Last Mileage</div>
        <div class="value">{{ mileage }}</div>
      </div>
      <div class="card-spacer"></div>
      <div class="card-cell">
        <div class="label">Report Status</div>
        <div class="value" style="color: #16a34a;">Verified Data</div>
      </div>
    </div>
  </div>

  <div class="section-title">Report Summary & History Details</div>
  <div class="content-box">{{ full_text[:3500] }}</div>
</body>
</html>
"""

if uploaded_file is not None:
    st.info("PDF Process ho rahi hai...")
    file_bytes = uploaded_file.read()
    parsed_data = parse_pdf(file_bytes)
    
    # Render HTML Template
    tmpl = Template(HTML_TEMPLATE)
    rendered_html = tmpl.render(**parsed_data)
    
    st.subheader("📋 Parsed Details Preview:")
    st.write(f"**Vehicle:** {parsed_data['year_make_model']}")
    st.write(f"**VIN:** {parsed_data['vin']}")
    st.write(f"**Mileage:** {parsed_data['mileage']}")
    
    st.divider()
    
    # Download PDF / HTML Buttons
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = HTML(string=rendered_html).write_pdf()
            st.download_button(
                label="📥 Download Vinlookupnow PDF Report",
                data=pdf_bytes,
                file_name=f"Vinlookupnow_{parsed_data['vin']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Convert Error: {str(e)}")
    else:
        st.error("WeasyPrint library load nahi ho saki. Packages check karein.")
    
    st.download_button(
        label="🌐 Download Mobile HTML Version",
        data=rendered_html,
        file_name=f"Vinlookupnow_{parsed_data['vin']}.html",
        mime="text/html"
    )
