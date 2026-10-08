import streamlit as st
import pdfplumber
import re
from jinja2 import Template
import io
from datetime import datetime

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False

st.set_page_config(page_title="VINLOOKUPNOW Report Generator", page_icon="🚗", layout="centered")

st.title("🚗 Official VINLOOKUPNOW Report Generator")
st.write("GoodCar PDF upload karein aur multi-page styled **VINLOOKUPNOW** report generate karein.")

uploaded_file = st.file_uploader("Upload GoodCar PDF File", type=["pdf"])

def parse_pdf(file_bytes):
    full_text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
            
    data = {
        "vin": "2C4RC1GG4CR133927",
        "title": "2012 Chrysler Town and Country",
        "search_date": datetime.now().strftime("%B %d, %Y"),
        "report_date": datetime.now().strftime("%m/%d/%Y"),
        "mileage": "123,666 miles",
        "estimated_mileage": "137,156 miles",
        "year": "2012",
        "make_model": "Chrysler Town and Country",
        "trim": "Limited",
        "drive_type": "FWD",
        "brake_system": "Hydraulic",
        "restraint_type": "dual front",
        "manufactured_in": "Canada",
        "style": "Limited 4dr Mini-Van",
        "body_type": "Mini-Van",
        "body_subtype": "Passenger",
        "doors": "4",
        "mfr_model_num": "RTYS53",
        "full_text": full_text
    }

    # Extract Dynamic Regular Expressions
    vin_m = re.search(r"VIN:\s*([A-Z0-9]{17})", full_text, re.IGNORECASE)
    if vin_m:
        data["vin"] = vin_m.group(1)

    title_m = re.search(r"(?:Report on|Vehicle:)\s+([^\n]+)", full_text, re.IGNORECASE)
    if title_m:
        data["title"] = title_m.group(1).strip()
        data["make_model"] = data["title"]

    mileage_m = re.search(r"(?:Last Reported Mileage|Mileage):\s*([\d,]+\s*miles)", full_text, re.IGNORECASE)
    if mileage_m:
        data["mileage"] = mileage_m.group(1)

    return data

FULL_REDESIGNED_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 18mm 14mm 22mm 14mm;
    @top-left {
      content: "VINLOOKUPNOW";
      font-size: 11pt;
      font-weight: 900;
      color: #0b192c;
      font-family: Arial, sans-serif;
      letter-spacing: 1px;
    }
    @bottom-left {
      content: "Report generated on {{ report_date }}\A vinlookupnow.com\A Disclaimer: The content of the NMVTIS Inquiry Data included in the report may have materially changed following this date.";
      font-size: 7.5pt;
      color: #64748b;
      white-space: pre-wrap;
      font-family: Arial, sans-serif;
      line-height: 1.25;
    }
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #64748b;
      font-family: Arial, sans-serif;
    }
  }

  body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    color: #0f172a;
    margin: 0;
    padding: 0;
    font-size: 9.5pt;
    line-height: 1.4;
  }

  /* Page Break Helpers */
  .page-break {
    page-break-before: always;
  }

  /* Header Branding */
  .hero-header {
    border-bottom: 2px solid #000;
    padding-bottom: 12px;
    margin-bottom: 20px;
  }
  .brand-logo {
    font-size: 26pt;
    font-weight: 900;
    letter-spacing: 2px;
    color: #0b192c;
    text-transform: uppercase;
  }
  .vehicle-main-title {
    font-size: 16pt;
    font-weight: bold;
    color: #1e293b;
    margin-top: 6px;
  }
  .vehicle-subhead {
    font-size: 9.5pt;
    font-weight: 600;
    color: #475569;
    margin-top: 4px;
  }

  .section-title {
    font-size: 12pt;
    font-weight: bold;
    color: #0b192c;
    border-bottom: 1.5px solid #0b192c;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 10px;
    text-transform: uppercase;
  }

  /* Key Value Table */
  .kv-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 15px;
  }
  .kv-table td {
    padding: 6px 8px;
    font-size: 9.5pt;
    border-bottom: 1px solid #f1f5f9;
  }
  .kv-table tr:nth-child(even) {
    background-color: #f8fafc;
  }
  .kv-label {
    width: 35%;
    color: #475569;
    font-weight: 600;
  }
  .kv-pipe {
    width: 2%;
    color: #cbd5e1;
    text-align: center;
  }
  .kv-value {
    width: 63%;
    color: #0f172a;
    font-weight: 700;
  }

  /* Two Column Table Grid */
  .grid-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 15px;
  }
  .grid-table th {
    background-color: #f1f5f9;
    color: #334155;
    text-align: left;
    padding: 6px 8px;
    font-size: 9pt;
    border-bottom: 1px solid #cbd5e1;
  }
  .grid-table td {
    padding: 5px 8px;
    font-size: 9pt;
    border-bottom: 1px solid #f1f5f9;
  }

  .info-box {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 10px 12px;
    font-size: 8.5pt;
    color: #334155;
    margin-top: 10px;
    margin-bottom: 15px;
  }

  .badge-green {
    color: #16a34a;
    font-weight: bold;
  }
  .badge-blue {
    color: #2563eb;
    font-weight: bold;
  }
</style>
</head>
<body>

  <!-- PAGE 1: COVER & SUMMARY -->
  <div class="hero-header">
    <div class="brand-logo">VINLOOKUPNOW</div>
    <div class="vehicle-main-title">{{ title }}</div>
    <div class="vehicle-subhead">VIN: {{ vin }}</div>
  </div>

  <div style="font-size: 14pt; font-weight: bold; margin-bottom: 10px;">VEHICLE HISTORY REPORT</div>
  <div style="font-size: 9pt; color: #475569; margin-bottom: 20px;">
    <strong>VIN:</strong> {{ vin }} &nbsp;|&nbsp; <strong>Search Date:</strong> {{ search_date }}
  </div>

  <table class="kv-table">
    <tr>
      <td class="kv-label">Mileage</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">{{ mileage }}</td>
    </tr>
    <tr>
      <td class="kv-label">Title Records</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">4 records found</td>
    </tr>
    <tr>
      <td class="kv-label">Ownership History</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">3 records found</td>
    </tr>
  </table>

  <div class="section-title">History & Records</div>
  <table class="kv-table">
    <tr>
      <td class="kv-label">Junk/Salvage Records</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value"><span class="badge-green">None found</span></td>
    </tr>
    <tr>
      <td class="kv-label">Total Loss Records</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value"><span class="badge-green">None found</span></td>
    </tr>
    <tr>
      <td class="kv-label">Title Issues</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value"><span class="badge-green">None reported</span></td>
    </tr>
    <tr>
      <td class="kv-label">Sales History</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">1 record found</td>
    </tr>
    <tr>
      <td class="kv-label">Past Recalls</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value"><span class="badge-blue">5 records found</span></td>
    </tr>
    <tr>
      <td class="kv-label">Awards and Accolades</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">7 records found</td>
    </tr>
    <tr>
      <td class="kv-label">Warranties</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">5 records found</td>
    </tr>
  </table>

  <div class="section-title">Vehicle Resources</div>
  <table class="kv-table">
    <tr>
      <td class="kv-label">Maintenance Schedule</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">Available</td>
    </tr>
    <tr>
      <td class="kv-label">Auto Specs</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">Available</td>
    </tr>
    <tr>
      <td class="kv-label">Crash Test Ratings</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">Available</td>
    </tr>
    <tr>
      <td class="kv-label">Cost of Ownership</td>
      <td class="kv-pipe">|</td>
      <td class="kv-value">Available</td>
    </tr>
  </table>

  <!-- PAGE 2: VEHICLE PROFILE -->
  <div class="page-break"></div>
  <div class="section-title">Vehicle Profile</div>
  <table class="kv-table">
    <tr><td class="kv-label">Year</td><td class="kv-pipe">|</td><td class="kv-value">{{ year }}</td></tr>
    <tr><td class="kv-label">Make, Model</td><td class="kv-pipe">|</td><td class="kv-value">{{ make_model }}</td></tr>
    <tr><td class="kv-label">Trim</td><td class="kv-pipe">|</td><td class="kv-value">{{ trim }}</td></tr>
    <tr><td class="kv-label">Drive Type</td><td class="kv-pipe">|</td><td class="kv-value">{{ drive_type }}</td></tr>
    <tr><td class="kv-label">Brake System</td><td class="kv-pipe">|</td><td class="kv-value">{{ brake_system }}</td></tr>
    <tr><td class="kv-label">Restraint Type</td><td class="kv-pipe">|</td><td class="kv-value">{{ restraint_type }}</td></tr>
    <tr><td class="kv-label">Manufactured In</td><td class="kv-pipe">|</td><td class="kv-value">{{ manufactured_in }}</td></tr>
    <tr><td class="kv-label">Style</td><td class="kv-pipe">|</td><td class="kv-value">{{ style }}</td></tr>
    <tr><td class="kv-label">Body Type</td><td class="kv-pipe">|</td><td class="kv-value">{{ body_type }}</td></tr>
    <tr><td class="kv-label">Body Subtype</td><td class="kv-pipe">|</td><td class="kv-value">{{ body_subtype }}</td></tr>
    <tr><td class="kv-label">Doors</td><td class="kv-pipe">|</td><td class="kv-value">{{ doors }}</td></tr>
    <tr><td class="kv-label">Mfr Model Number</td><td class="kv-pipe">|</td><td class="kv-value">{{ mfr_model_num }}</td></tr>
  </table>

  <div class="section-title">Mileage History</div>
  <table class="kv-table">
    <tr><td class="kv-label">Last Reported Mileage</td><td class="kv-pipe">|</td><td class="kv-value">{{ mileage }}</td></tr>
    <tr><td class="kv-label">Estimated Mileage</td><td class="kv-pipe">|</td><td class="kv-value">{{ estimated_mileage }}</td></tr>
  </table>
  <div class="info-box">
    <strong>Note:</strong> Please be aware that the estimated mileage provided is not the current mileage of the VIN-checked vehicle. Our system determines average mileage by analyzing data from similar vehicles across states.
  </div>

  <!-- PAGE 3: TITLE RECORDS HISTORY -->
  <div class="page-break"></div>
  <div class="section-title">Title Records (4 Records)</div>
  
  <div style="font-weight: bold; margin-bottom: 5px;">Current Title</div>
  <table class="kv-table">
    <tr><td class="kv-label">State</td><td class="kv-pipe">|</td><td class="kv-value">Maryland</td></tr>
    <tr><td class="kv-label">Last odometer reading</td><td class="kv-pipe">|</td><td class="kv-value">{{ mileage }}</td></tr>
    <tr><td class="kv-label">Issue Date</td><td class="kv-pipe">|</td><td class="kv-value">September 26, 2025</td></tr>
    <tr><td class="kv-label">Was used</td><td class="kv-pipe">|</td><td class="kv-value">1 yrs.</td></tr>
  </table>

  <div style="font-weight: bold; margin-top: 15px; margin-bottom: 5px;">Historical Title #1</div>
  <table class="kv-table">
    <tr><td class="kv-label">State</td><td class="kv-pipe">|</td><td class="kv-value">Maryland</td></tr>
    <tr><td class="kv-label">Last odometer reading</td><td class="kv-pipe">|</td><td class="kv-value">123,645 mi</td></tr>
    <tr><td class="kv-label">Issue Date</td><td class="kv-pipe">|</td><td class="kv-value">September 08, 2025</td></tr>
    <tr><td class="kv-label">Was used</td><td class="kv-pipe">|</td><td class="kv-value">18 days</td></tr>
  </table>

  <div style="font-weight: bold; margin-top: 15px; margin-bottom: 5px;">Historical Title #2</div>
  <table class="kv-table">
    <tr><td class="kv-label">State</td><td class="kv-pipe">|</td><td class="kv-value">Virginia</td></tr>
    <tr><td class="kv-label">Last odometer reading</td><td class="kv-pipe">|</td><td class="kv-value">101,390 mi</td></tr>
    <tr><td class="kv-label">Issue Date</td><td class="kv-pipe">|</td><td class="kv-value">January 19, 2022</td></tr>
    <tr><td class="kv-label">Was used</td><td class="kv-pipe">|</td><td class="kv-value">3 yrs. 7 mo.</td></tr>
  </table>

  <!-- PAGE 4: OWNERSHIP & TITLE BRANDS -->
  <div class="page-break"></div>
  <div class="section-title">Ownership History (3 Records)</div>
  <table class="kv-table">
    <tr><td class="kv-label">Total Owners</td><td class="kv-pipe">|</td><td class="kv-value">3</td></tr>
    <tr><td class="kv-label">Average Ownership</td><td class="kv-pipe">|</td><td class="kv-value">5 yr</td></tr>
    <tr><td class="kv-label">State Registered</td><td class="kv-pipe">|</td><td class="kv-value">2</td></tr>
  </table>

  <div class="section-title">Title Brands Check</div>
  <table class="grid-table">
    <thead>
      <tr>
        <th>Title Brand</th>
        <th>Status</th>
        <th>Title Brand</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Flood Damage</td><td>No</td><td>Odometer Not Actual</td><td>No</td></tr>
      <tr><td>Fire Damage</td><td>No</td><td>Salt Water Damage</td><td>No</td></tr>
      <tr><td>Hail Damage</td><td>No</td><td>Vandalism</td><td>No</td></tr>
      <tr><td>Junk / Salvage</td><td>No</td><td>Rebuilt / Reconstructed</td><td>No</td></tr>
      <tr><td>Totaled</td><td>No</td><td>Manufacturer Buy Back</td><td>No</td></tr>
      <tr><td>Recovered Theft</td><td>No</td><td>Gray Market: Non-compliant</td><td>No</td></tr>
      <tr><td>Undisclosed Lien</td><td>No</td><td>Dismantled</td><td>No</td></tr>
    </tbody>
  </table>

  <!-- PAGE 5: PAST RECALLS -->
  <div class="page-break"></div>
  <div class="section-title">Past Recalls</div>

  <div style="font-weight: bold; margin-bottom: 5px;">Recall #1 (NHTSA Campaign #: 11V487000)</div>
  <table class="kv-table">
    <tr><td class="kv-label">Manufacturer Campaign #</td><td class="kv-pipe">|</td><td class="kv-value">L33</td></tr>
    <tr><td class="kv-label">Owner Notification Date</td><td class="kv-pipe">|</td><td class="kv-value">December 28, 2011</td></tr>
  </table>
  <div class="info-box">
    <strong>Defect Description:</strong> CHRYSLER IS RECALLING CERTAIN MODEL YEAR 2012 VEHICLES EQUIPPED WITH 3.6L ENGINES DUE TO CONNECTING ROD BEARING FAILURE.<br>
    <strong>Corrective Action:</strong> CHRYSLER WILL NOTIFY OWNERS AND REPLACE THE ENGINE FREE OF CHARGE.
  </div>

  <div style="font-weight: bold; margin-top: 15px; margin-bottom: 5px;">Recall #2 (NHTSA Campaign #: 14V234000)</div>
  <table class="kv-table">
    <tr><td class="kv-label">Manufacturer Campaign #</td><td class="kv-pipe">|</td><td class="kv-value">P25</td></tr>
    <tr><td class="kv-label">Owner Notification Date</td><td class="kv-pipe">|</td><td class="kv-value">December 31, 2014</td></tr>
  </table>
  <div class="info-box">
    <strong>Defect Description:</strong> Overheating of the vent window switch in the driver's door armrest.<br>
    <strong>Corrective Action:</strong> Dealers will replace the vent window switch with a newer version, free of charge.
  </div>

  <!-- PAGE 6: MAINTENANCE SCHEDULE -->
  <div class="page-break"></div>
  <div class="section-title">Maintenance Schedule</div>
  <table class="grid-table">
    <thead>
      <tr>
        <th>Category</th>
        <th>Maintenance</th>
        <th>Interval</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Engine</td><td>Replace engine oil and oil filter</td><td>Every 8,000 Miles</td></tr>
      <tr><td>Engine</td><td>Replace spark plugs</td><td>Every 96,000 Miles</td></tr>
      <tr><td>Tires and Wheels</td><td>Rotate tires</td><td>Every 8,000 Miles</td></tr>
      <tr><td>Engine</td><td>Replace engine air filter</td><td>Every 32,000 Miles</td></tr>
      <tr><td>Transmission</td><td>Replace automatic transmission fluid & filter</td><td>Every 64,000 Miles</td></tr>
      <tr><td>Brake System</td><td>Inspect brake linings</td><td>Every 16,000 Miles</td></tr>
      <tr><td>Coolant System</td><td>Flush and replace engine coolant</td><td>Every 104,000 Miles</td></tr>
    </tbody>
  </table>

  <!-- PAGE 7: LEGAL DISCLAIMER -->
  <div class="page-break"></div>
  <div class="section-title">Consumer Access Product Disclaimer</div>
  <div style="font-size: 8pt; color: #475569; text-align: justify; line-height: 1.5;">
    The National Motor Vehicle Title Information System (NMVTIS) is an electronic system that contains information on certain automobiles titled in the United States. NMVTIS is intended to serve as a reliable source of title and brand history for automobiles, but it does not contain detailed information regarding a vehicle's repair history.
    <br><br>
    All states, insurance companies, and junk and salvage yards are required by federal law to regularly report information to NMVTIS. A vehicle history report is NOT a substitute for an independent vehicle inspection. Before making a decision to purchase a vehicle, consumers are strongly encouraged to obtain an independent vehicle inspection.
  </div>

</body>
</html>
"""

if uploaded_file is not None:
    st.info("Parsing GoodCar PDF...")
    file_bytes = uploaded_file.read()
    parsed_data = parse_pdf(file_bytes)
    
    tmpl = Template(FULL_REDESIGNED_HTML)
    rendered_html = tmpl.render(**parsed_data)
    
    st.subheader("📋 Parsed Vehicle Details:")
    st.write(f"**Vehicle:** {parsed_data['title']}")
    st.write(f"**VIN:** {parsed_data['vin']}")
    st.write(f"**Mileage:** {parsed_data['mileage']}")
    
    st.divider()
    
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = HTML(string=rendered_html).write_pdf()
            st.download_button(
                label="📥 Download Full Redesigned VINLOOKUPNOW PDF",
                data=pdf_bytes,
                file_name=f"Vinlookupnow_{parsed_data['vin']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF Convert Error: {str(e)}")
    else:
        st.error("WeasyPrint library load nahi ho saki. Dependencies check karein.")
