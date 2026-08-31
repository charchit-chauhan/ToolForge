# Tool Forge (Flask)

All-in-one document, image, and language utility suite — modern dark UI on **Flask + HTML/CSS/JS**.

## Features

| Tool | Capabilities |
|------|--------------|
| **Smart Translator** | 70+ languages, auto-detect, word-sense disambiguation, romanization, back-translation, TTS |
| **PDF Toolkit** | Merge, split, rotate, compress, watermark, protect, unlock, extract text/images, PDF↔images |
| **Word ⇄ PDF** | DOCX→PDF, PDF→DOCX, plain text→PDF, plain text→DOCX |
| **OCR & Text→Image** | Tesseract OCR multi-language, styled text rendered to PNG |
| **Image Tools** | Convert format, compress, resize, rotate/flip, watermark, grayscale, filters |
| **Text → Speech** | Speech audio in many languages |
| **QR Generator** | Custom size & colours |

## Quick start

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**

### System packages (recommended)

- **Poppler** — PDF → images  
- **Tesseract OCR** — image text extraction  
- **LibreOffice** — best Word ↔ PDF quality  

Windows: install via [poppler](https://github.com/oschwartz10612/poppler-windows), [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki), and LibreOffice.

---

## Translation — long-term setup (recommended)

Free unofficial endpoints get rate-limited. For reliable translation, set **at least one** API key.

### Option A — DeepL Free (easiest)

1. Create a free account: https://www.deepl.com/pro-api  
2. Copy your auth key (often ends with `:fx`)  
3. Create a `.env` file in the project root:

```env
DEEPL_API_KEY=your-key-here:fx
```

Free tier: **500,000 characters / month**.

### Option B — Google Cloud Translation

1. Go to [Google Cloud Console](https://console.cloud.google.com/)  
2. Enable **Cloud Translation API**  
3. Create an API key  
4. Add to `.env`:

```env
GOOGLE_TRANSLATE_API_KEY=your-google-api-key
```

### Option C — LibreTranslate (self-hosted / private)

```env
LIBRETRANSLATE_URL=http://localhost:5000
LIBRETRANSLATE_API_KEY=optional-key
```

### Provider priority

1. DeepL (if `DEEPL_API_KEY` set)  
2. Google Cloud (if `GOOGLE_TRANSLATE_API_KEY` set)  
3. LibreTranslate (if `LIBRETRANSLATE_URL` set)  
4. Free fallbacks (Google GTX → MyMemory) — rate-limited  

Copy `.env.example` to `.env` and fill in values. Restart `python app.py` after changing `.env`.

---

## Project layout

```
├── app.py
├── processors.py
├── requirements.txt
├── .env.example
├── README.md
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── index.html
    └── …
```

## Notes

- Max upload size: 80 MB  
- Without API keys, translation may show rate-limit errors after a few requests  
- OCR quality depends on installed Tesseract language packs  
