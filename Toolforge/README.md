# Tool Forge (Flask)

All-in-one document, image, and language utility suite — rebuilt from the original Streamlit app with a modern dark UI on **Flask + HTML/CSS/JS**.

## Features

| Tool | Capabilities |
|------|--------------|
| **Smart Translator** | 70+ languages, auto-detect, word-sense disambiguation, romanization, back-translation, TTS |
| **PDF Toolkit** | Merge, split (all / range), rotate, compress, watermark, protect, unlock, extract text/images, PDF↔images |
| **Word ⇄ PDF** | DOCX→PDF, PDF→DOCX, plain text→PDF, plain text→DOCX |
| **OCR & Text→Image** | Tesseract OCR multi-language, styled text rendered to PNG |
| **Image Tools** | Convert format, compress, resize, rotate/flip, watermark, grayscale, filters |
| **Text → Speech** | Google TTS-style audio in many languages |
| **QR Generator** | Custom size & colours |

## Quick start

```bash
cd /path/to/this/folder
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# System packages (Debian/Ubuntu):
# sudo apt install poppler-utils tesseract-ocr tesseract-ocr-eng libreoffice

python app.py
```

Open **http://127.0.0.1:5000**

## Project layout

```
├── app.py              # Flask routes & API
├── processors.py       # PDF / image / document processing
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── translator.html
    ├── pdf.html
    ├── convert.html
    ├── ocr.html
    ├── images.html
    ├── tts.html
    └── qr.html
```

## Notes

- Translation & TTS use public Google Translate endpoints (no API key). Rate limits may apply.
- PDF→Word and Word→PDF work best when `libreoffice` and `poppler-utils` are installed.
- OCR quality depends on installed Tesseract language packs.
- Max upload size: 80 MB.
