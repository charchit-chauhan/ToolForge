# Deploy Tool Forge

## Before you deploy

1. Put your code on **GitHub** (public or private repo).
2. Do **not** commit `.env` (secrets). Set keys in the host’s Environment Variables UI.
3. Free hosts often **cannot** install Tesseract / Poppler / LibreOffice.  
   - Translation, QR, most PDF/image tools still work.  
   - OCR and some PDF→image features may fail unless you use a Docker image with those packages.

---

## Option A — Render (recommended free)

1. Push your project to GitHub.
2. Go to [https://render.com](https://render.com) → **New → Web Service**.
3. Connect the GitHub repo.
4. Settings:

| Field | Value |
|--------|--------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Instance** | Free |

5. **Environment variables** (Environment tab):

```
SECRET_KEY=long-random-string-change-me
DEEPL_API_KEY=your-deepl-key-if-any
GOOGLE_TRANSLATE_API_KEY=
```

6. Click **Create Web Service**.  
   After build, open the `https://….onrender.com` URL.

**Note:** Free tier sleeps after ~15 minutes idle; first request can take 30–60s.

---

## Option B — Railway

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.
2. Add variables: `SECRET_KEY`, optional `DEEPL_API_KEY`.
3. Start command (if needed):  
   `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Generate a public domain in Settings.

---

## Option C — PythonAnywhere (beginner-friendly)

1. Upload/clone the project in a free account.
2. Create a web app (Manual config, Flask).
3. Point the WSGI file to your `app` object, e.g.:

```python
import sys
path = "/home/YOURUSER/ToolForge"
if path not in sys.path:
    sys.path.append(path)
from app import app as application
```

4. Reload the web app.

Outbound internet on free accounts is limited — translation APIs may not work.

---

## Option D — Local network (no cloud)

On your PC (always-on machine):

```powershell
.\.venv\Scripts\activate
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
```

Others on the same Wi‑Fi open: `http://YOUR-PC-IP:5000`

---

## Production checklist

- [ ] `SECRET_KEY` set to a long random value  
- [ ] `DEEPL_API_KEY` (or Google) set for reliable translation  
- [ ] `debug=False` (use gunicorn, not `python app.py`)  
- [ ] `.env` not committed to Git  
- [ ] File size limits OK for your host’s disk/RAM  

---

## Full tools (OCR, PDF→images) on a VPS

Use a small VPS (DigitalOcean, Linode, etc.) with Docker or apt:

```bash
sudo apt update
sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-eng libreoffice
pip install -r requirements.txt
gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

Put Nginx + HTTPS in front for a real domain.
