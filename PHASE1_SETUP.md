# ToolForge AI — Phase 1 setup (Windows / VS Code)

## 1. Extract and open

1. Download and extract `ToolForge_Phase1_Stabilized.zip`.
2. Open the extracted `ToolForge` folder in VS Code.
3. Keep your original uploaded ZIP unchanged as the backup.

## 2. Create a virtual environment

Open the VS Code terminal (PowerShell) in the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Configure environment variables

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `.env` as `SECRET_KEY=...`. Add your own translation provider key only if you use that provider. Never paste keys into source code or commit `.env`.

## 4. Install external system tools

The Python packages do not install all system executables. For OCR, install Tesseract OCR and ensure `tesseract.exe` is available on PATH. For PDF-to-image conversion, install Poppler and ensure its `bin` directory is on PATH. LibreOffice is optional and improves DOCX-to-PDF fidelity; the application has a Python fallback.

## 5. Run regression tests

```powershell
pytest -q
```

The Phase 1 tests check the session gate, API access, and PDF upload validation. They do not replace manual testing of every existing tool.

## 6. Run the application

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser. The Phase 1 name/email sign-in is a temporary compatibility gate, not real account authentication. MySQL-backed registration, password authentication, roles, and CSRF protection are Phase 2.

## 7. Manual regression checklist

After signing in, test each existing area:

- [ ] Translator: detect language and translate text
- [ ] PDF: merge, split, rotate, compress, watermark, protect, unlock, extract text/images, PDF to images, images to PDF, PDF info
- [ ] Conversion: Word to PDF, PDF to Word, text to PDF/DOCX
- [ ] OCR: upload a valid image and extract text
- [ ] Images: convert, compress, resize, rotate, watermark, grayscale, filters
- [ ] Text to speech
- [ ] QR generation
- [ ] Utilities
- [ ] Theme toggle and browser history

Also verify that unsupported file extensions and invalid/corrupt PDF/image/DOCX files are rejected.

## 8. Credential incident reminder

The uploaded archive contained a translation-provider credential in a duplicate environment file. That file has been removed from this cleaned package. Revoke/rotate that credential in the provider dashboard immediately, then place the replacement only in your private `.env`. If the original archive or Git history was shared or pushed remotely, rotate the credential regardless of whether the repository was later made private.
