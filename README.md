# VinLookUpNow Report Studio

A Streamlit app that accepts a text-based vehicle-history PDF, extracts its text, and exports a cleaner PDF reading copy with VinLookUpNow styling and explicit source attribution.

## Important transparency note

This tool does **not** verify or issue vehicle-history data. It reformats a user-supplied source report and labels the result as a reformatted copy. Keep the original provider's identity and disclaimers intact when required. Do not present the output as an original report issued by VinLookUpNow or imply that VinLookUpNow independently verified the data.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud through GitHub

1. Create a GitHub repository, for example `vinlookupnow-report-studio`.
2. Upload `app.py`, `requirements.txt`, `README.md`, and `.gitignore` to the repository root. Do not commit customer reports or private PDFs.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and connect GitHub.
4. Choose **Create app**, select the repository and branch, and set the main file path to `app.py`.
5. Deploy. Streamlit installs dependencies from `requirements.txt`.

## Current limitations

- Works best with text-based PDFs. Scanned PDFs without selectable text need OCR.
- PDF text extraction can flatten multi-column tables; always compare the generated file with the source.
- The app does not query GoodCar or any other provider and cannot verify record accuracy or completeness.
- For large reports, review the output carefully before using it.
