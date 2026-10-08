import io
import fitz  # PyMuPDF
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="PDF Logo Replacer", page_icon="📄", layout="wide"
)

st.title("📄 Vehicle Report Logo Replacer")
st.write(
    "Upload a GoodCar PDF report and your custom logo to automatically replace"
    " the header logo across all pages."
)

# Sidebar - Logo Positioning Controls
st.sidebar.header("🎯 Logo Placement Controls")
st.sidebar.caption(
    "Adjust these values to align your logo over the original logo."
)

x0 = st.sidebar.slider("Left Margin (X)", min_value=0, max_value=600, value=35)
y0 = st.sidebar.slider("Top Margin (Y)", min_value=0, max_value=800, value=20)
target_width = st.sidebar.slider(
    "Logo Width", min_value=20, max_value=300, value=160
)
target_height = st.sidebar.slider(
    "Logo Height", min_value=10, max_value=150, value=45
)
whiteout_old = st.sidebar.checkbox("Cover original logo with white box", value=True)

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
  st.subheader("1. Upload Files")
  uploaded_pdf = st.file_uploader(
      "Upload GoodCar PDF Report", type=["pdf"], key="pdf"
  )
  uploaded_logo = st.file_uploader(
      "Upload Custom Logo (PNG / JPG)",
      type=["png", "jpg", "jpeg"],
      key="logo",
  )


def process_pdf(pdf_bytes, logo_bytes, coords, erase_background=True):
  """Processes all pages in the PDF, erases the old logo zone, and stamps the new logo."""
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")

  # Calculate target rectangle preserving logo aspect ratio
  logo_img = Image.open(io.BytesIO(logo_bytes))
  orig_w, orig_h = logo_img.size
  aspect = orig_w / orig_h

  x, y, max_w, max_h = coords
  calc_h = max_w / aspect
  if calc_h > max_h:
    calc_h = max_h
    calc_w = calc_h * aspect
  else:
    calc_w = max_w

  logo_rect = fitz.Rect(x, y, x + calc_w, y + calc_h)
  cover_rect = fitz.Rect(x - 2, y - 2, x + max_w + 2, y + max_h + 2)

  for page in doc:
    if erase_background:
      # Draw white rectangle over old logo region
      page.draw_rect(cover_rect, color=(1, 1, 1), fill=(1, 1, 1))

    # Stamp new logo
    page.insert_image(logo_rect, stream=logo_bytes)

  output_stream = io.BytesIO()
  doc.save(output_stream)
  doc.close()
  output_stream.seek(0)
  return output_stream


def get_page_preview(pdf_bytes, logo_bytes, coords, erase_background=True):
  """Renders a low-res image preview of Page 1 with the logo applied."""
  doc = fitz.open(stream=pdf_bytes, filetype="pdf")
  page = doc[0]

  logo_img = Image.open(io.BytesIO(logo_bytes))
  orig_w, orig_h = logo_img.size
  aspect = orig_w / orig_h

  x, y, max_w, max_h = coords
  calc_h = max_w / aspect
  if calc_h > max_h:
    calc_h = max_h
    calc_w = calc_h * aspect
  else:
    calc_w = max_w

  logo_rect = fitz.Rect(x, y, x + calc_w, y + calc_h)
  cover_rect = fitz.Rect(x - 2, y - 2, x + max_w + 2, y + max_h + 2)

  if erase_background:
    page.draw_rect(cover_rect, color=(1, 1, 1), fill=(1, 1, 1))

  page.insert_image(logo_rect, stream=logo_bytes)

  pix = page.get_pixmap(dpi=120)
  img_bytes = pix.tobytes("png")
  doc.close()
  return img_bytes


with col2:
  st.subheader("2. Live Page 1 Preview")
  if uploaded_pdf and uploaded_logo:
    pdf_data = uploaded_pdf.read()
    logo_data = uploaded_logo.read()
    coords = (x0, y0, target_width, target_height)

    preview_img = get_page_preview(
        pdf_data, logo_data, coords, erase_background=whiteout_old
    )
    st.image(
        preview_img,
        caption="Preview of Page 1 with new logo",
        use_container_width=True,
    )

    st.markdown("---")
    if st.button("🚀 Process Full Report & Replace Logo", type="primary"):
      with st.spinner(
          "Processing all pages... This takes less than 3 seconds."
      ):
        modified_pdf = process_pdf(
            pdf_data, logo_data, coords, erase_background=whiteout_old
        )

        st.success("Replacement complete!")
        st.download_button(
            label="📥 Download Modified PDF Report",
            data=modified_pdf,
            file_name=f"modified_{uploaded_pdf.name}",
            mime="application/pdf",
        )
  else:
    st.info(
        "Upload both a PDF and a logo image to generate the live preview."
    )
