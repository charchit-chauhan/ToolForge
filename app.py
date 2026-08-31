"""
Tool Forge — Flask edition
All-in-one document, image, and language utility suite.
Beautiful modern dark UI · Translator · PDF tools · Word↔PDF · OCR · Image tools · TTS · QR
"""

import os
import io
import re
import time
import base64
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, send_file,
    redirect, url_for, flash, session
)
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import requests

from processors import (
    pdf_merge, pdf_split, pdf_split_range, pdf_rotate, pdf_compress_simple,
    pdf_add_watermark, pdf_protect, pdf_unlock, pdf_extract_text,
    pdf_extract_images, pdf_to_images, images_to_pdf, pdf_get_page_count,
    pdf_to_word, word_to_pdf, text_to_docx, text_to_pdf, docx_extract_text,
    image_convert_format, image_compress, image_resize, image_rotate_flip,
    image_add_watermark_text, image_to_grayscale, image_apply_filter,
    text_to_image, generate_qr_code, WORKDIR,
)

# Load .env from project root if present (no extra dependency required)
def _load_dotenv():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass

_load_dotenv()


# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "toolforge-dev-secret-change-me")
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30 days
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80 MB
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKDIR, exist_ok=True)


# ── Auth (one-time name gate for tools) ────────────────────────────────────
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_name"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_name"):
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        if not name:
            error = "Please enter your name."
        elif not email:
            error = "Please enter your email."
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            error = "Please enter a valid email address."
        else:
            session["user_name"] = name[:80]
            session["user_email"] = email[:120]
            session.permanent = True
            nxt = request.args.get("next") or url_for("index")
            if not nxt.startswith("/"):
                nxt = url_for("index")
            return redirect(nxt)
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Language maps ──────────────────────────────────────────────────────────
LANG_MAP = {
    "English": "en", "Hindi": "hi", "French": "fr", "German": "de",
    "Spanish": "es", "Chinese (Simplified)": "zh", "Japanese": "ja",
    "Arabic": "ar", "Bengali": "bn", "Portuguese": "pt", "Russian": "ru",
    "Italian": "it", "Korean": "ko", "Turkish": "tr", "Dutch": "nl",
    "Polish": "pl", "Swedish": "sv", "Norwegian": "no", "Danish": "da",
    "Finnish": "fi", "Greek": "el", "Czech": "cs", "Romanian": "ro",
    "Hungarian": "hu", "Ukrainian": "uk", "Thai": "th", "Vietnamese": "vi",
    "Indonesian": "id", "Malay": "ms", "Persian": "fa", "Urdu": "ur",
    "Punjabi": "pa", "Gujarati": "gu", "Marathi": "mr", "Tamil": "ta",
    "Telugu": "te", "Kannada": "kn", "Malayalam": "ml", "Swahili": "sw",
    "Afrikaans": "af", "Hebrew": "iw", "Catalan": "ca", "Croatian": "hr",
    "Serbian": "sr", "Slovak": "sk", "Bulgarian": "bg", "Latvian": "lv",
    "Lithuanian": "lt", "Estonian": "et", "Slovenian": "sl", "Albanian": "sq",
    "Macedonian": "mk", "Tagalog (Filipino)": "tl", "Welsh": "cy",
    "Irish": "ga", "Latin": "la", "Esperanto": "eo", "Zulu": "zu",
    "Yoruba": "yo", "Somali": "so", "Nepali": "ne", "Sinhala": "si",
    "Khmer": "km", "Mongolian": "mn", "Kazakh": "kk", "Uzbek": "uz",
    "Armenian": "hy", "Georgian": "ka", "Haitian Creole": "ht",
    "Icelandic": "is", "Maltese": "mt",
}
LANG_CODES_REVERSE = {v: k for k, v in LANG_MAP.items()}

TESSERACT_LANG_MAP = {
    "en": "eng", "hi": "hin", "fr": "fra", "de": "deu", "es": "spa",
    "zh": "chi_sim", "ja": "jpn", "ar": "ara", "pt": "por", "ru": "rus",
    "it": "ita", "ko": "kor", "auto": "eng",
}

# ── Word-sense disambiguation ──────────────────────────────────────────────
AMBIGUOUS_WORDS = {
    "bat": {
        "senses": {
            "Animal (flying mammal)": {
                "hint": "the flying mammal animal",
                "keywords": ["flying", "cave", "nocturnal", "mammal", "wing", "sonar", "vampire", "fruit bat"],
            },
            "Cricket/Baseball bat": {
                "hint": "a cricket or baseball bat (sports equipment)",
                "keywords": ["cricket", "baseball", "hit", "swing", "sport", "wicket", "run", "innings", "score"],
            },
            "Verb: to bat": {
                "hint": "a verb meaning to hit or strike",
                "keywords": ["batting", "batted", "eyelid", "blink"],
            },
        },
        "default_sense": "Animal (flying mammal)",
    },
    "bats": {
        "senses": {
            "Animals (flying mammals)": {
                "hint": "flying mammal animals (plural)",
                "keywords": ["flying", "cave", "nocturnal", "mammal", "wing", "sonar", "vampire", "fruit", "colony"],
            },
            "Cricket/Baseball bats": {
                "hint": "cricket or baseball bats (plural)",
                "keywords": ["cricket", "baseball", "hit", "swing", "willow", "rubber"],
            },
            "Verb: bats": {
                "hint": "a verb (he/she bats)",
                "keywords": ["he bats", "she bats", "batting", "average"],
            },
            "Crazy/insane (slang)": {
                "hint": "crazy or insane (informal slang)",
                "keywords": ["crazy", "mad", "insane", "nuts", "mental"],
            },
        },
        "default_sense": "Animals (flying mammals)",
    },
    "bank": {
        "senses": {
            "Financial institution": {
                "hint": "a financial institution",
                "keywords": ["money", "account", "loan", "deposit", "withdraw", "interest", "finance", "savings"],
            },
            "River bank": {
                "hint": "the bank/shore of a river or lake",
                "keywords": ["river", "lake", "stream", "shore", "water", "flood", "fish", "boat"],
            },
            "Verb: to bank": {
                "hint": "a verb meaning to tilt or rely on",
                "keywords": ["banked", "banking", "turn", "aircraft", "tilt", "rely", "count on"],
            },
        },
        "default_sense": "Financial institution",
    },
    "crane": {
        "senses": {
            "Bird": {
                "hint": "a crane bird",
                "keywords": ["bird", "fly", "migration", "flock", "nest", "feather", "beak", "wetland"],
            },
            "Construction crane": {
                "hint": "a construction crane machine",
                "keywords": ["construction", "lift", "building", "machine", "operator", "site", "heavy"],
            },
            "Verb: to crane": {
                "hint": "a verb meaning to stretch the neck",
                "keywords": ["neck", "stretch", "look", "peer"],
            },
        },
        "default_sense": "Bird",
    },
    "spring": {
        "senses": {
            "Season": {
                "hint": "the season of spring",
                "keywords": ["season", "summer", "autumn", "winter", "flowers", "bloom", "march", "april"],
            },
            "Coil / mechanical spring": {
                "hint": "a metal coil spring",
                "keywords": ["coil", "metal", "bounce", "mattress", "elasticity", "compress"],
            },
            "Water spring": {
                "hint": "a natural water spring",
                "keywords": ["water", "source", "stream", "fresh", "mountain"],
            },
            "Verb: to spring": {
                "hint": "a verb meaning to jump or arise",
                "keywords": ["jump", "leap", "arise", "suddenly"],
            },
        },
        "default_sense": "Season",
    },
    "light": {
        "senses": {
            "Illumination": {
                "hint": "illumination or brightness",
                "keywords": ["bright", "dark", "lamp", "sun", "bulb", "shine", "glow"],
            },
            "Not heavy": {
                "hint": "not heavy in weight",
                "keywords": ["heavy", "weight", "carry", "feather", "lightweight"],
            },
            "Pale colour": {
                "hint": "a pale or light colour",
                "keywords": ["colour", "color", "pale", "shade", "dark", "hue"],
            },
        },
        "default_sense": "Illumination",
    },
    "mouse": {
        "senses": {
            "Animal": {
                "hint": "a small rodent animal",
                "keywords": ["rodent", "cheese", "cat", "trap", "tail", "squeak"],
            },
            "Computer mouse": {
                "hint": "a computer pointing device",
                "keywords": ["computer", "click", "cursor", "screen", "keyboard", "usb"],
            },
        },
        "default_sense": "Animal",
    },
    "watch": {
        "senses": {
            "Timepiece": {
                "hint": "a wristwatch or clock",
                "keywords": ["time", "clock", "wrist", "hour", "minute", "strap"],
            },
            "Verb: to watch": {
                "hint": "a verb meaning to observe",
                "keywords": ["look", "see", "observe", "tv", "movie", "screen"],
            },
        },
        "default_sense": "Timepiece",
    },
    "right": {
        "senses": {
            "Correct / true": {
                "hint": "correct or true",
                "keywords": ["wrong", "correct", "true", "answer", "yes"],
            },
            "Direction (opposite of left)": {
                "hint": "the direction opposite of left",
                "keywords": ["left", "direction", "turn", "hand", "side"],
            },
            "Legal entitlement": {
                "hint": "a legal right or entitlement",
                "keywords": ["law", "human", "freedom", "privilege", "claim"],
            },
        },
        "default_sense": "Correct / true",
    },
    "park": {
        "senses": {
            "Public park": {
                "hint": "a public green space",
                "keywords": ["garden", "trees", "bench", "playground", "picnic", "green"],
            },
            "Verb: to park": {
                "hint": "a verb meaning to leave a vehicle",
                "keywords": ["car", "vehicle", "parking", "lot", "space", "drive"],
            },
        },
        "default_sense": "Public park",
    },
}


# ── Helper functions ───────────────────────────────────────────────────────
# ════════════════════════════════════════════════
#  TRANSLATION PROVIDERS (long-term / production)
# ════════════════════════════════════════════════
# Priority order (first success wins):
#   1. DeepL          — set DEEPL_API_KEY
#   2. Google Cloud   — set GOOGLE_TRANSLATE_API_KEY
#   3. LibreTranslate — set LIBRETRANSLATE_URL (+ optional LIBRETRANSLATE_API_KEY)
#   4. Free fallbacks — Google GTX → MyMemory (rate-limited; last resort)
#
# Get free keys:
#   DeepL free:     https://www.deepl.com/pro-api  (500k chars/month free)
#   Google Cloud:   https://console.cloud.google.com/  (enable Cloud Translation)
#   LibreTranslate: self-host or use a public host with a key
# ════════════════════════════════════════════════

DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "").strip()
GOOGLE_TRANSLATE_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "").strip()
LIBRETRANSLATE_URL = os.environ.get("LIBRETRANSLATE_URL", "").strip().rstrip("/")
LIBRETRANSLATE_API_KEY = os.environ.get("LIBRETRANSLATE_API_KEY", "").strip()

# DeepL uses slightly different language codes
_DEEPL_CODE = {
    "en": "EN", "hi": "HI", "fr": "FR", "de": "DE", "es": "ES",
    "zh": "ZH", "ja": "JA", "ar": "AR", "pt": "PT", "ru": "RU",
    "it": "IT", "ko": "KO", "tr": "TR", "nl": "NL", "pl": "PL",
    "sv": "SV", "da": "DA", "fi": "FI", "el": "EL", "cs": "CS",
    "ro": "RO", "hu": "HU", "uk": "UK", "bg": "BG", "sk": "SK",
    "sl": "SL", "et": "ET", "lv": "LV", "lt": "LT", "id": "ID",
    "nb": "NB", "no": "NB",
}


def _headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _translate_deepl(text: str, src: str, tgt: str) -> str | None:
    """Official DeepL API (free or pro key)."""
    if not DEEPL_API_KEY:
        return None
    src_dl = _DEEPL_CODE.get(src)
    tgt_dl = _DEEPL_CODE.get(tgt)
    if not tgt_dl:
        return None  # unsupported language
    # Free keys use api-free.deepl.com; pro keys use api.deepl.com
    base = "https://api-free.deepl.com" if DEEPL_API_KEY.endswith(":fx") or True else "https://api.deepl.com"
    # Try free host first; if 403, try pro host
    for host in ("https://api-free.deepl.com", "https://api.deepl.com"):
        try:
            data = {"text": text, "target_lang": tgt_dl}
            if src_dl:
                data["source_lang"] = src_dl
            resp = requests.post(
                f"{host}/v2/translate",
                data=data,
                headers={"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"},
                timeout=20,
            )
            if resp.status_code == 403:
                continue
            if resp.status_code != 200:
                return None
            translations = resp.json().get("translations") or []
            if translations:
                return translations[0].get("text") or None
        except Exception:
            continue
    return None


def _translate_google_official(text: str, src: str, tgt: str) -> str | None:
    """Official Google Cloud Translation API v2."""
    if not GOOGLE_TRANSLATE_API_KEY:
        return None
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "key": GOOGLE_TRANSLATE_API_KEY,
        "q": text,
        "target": tgt,
        "format": "text",
    }
    if src and src != "auto":
        params["source"] = src
    try:
        resp = requests.post(url, params=params, timeout=20)
        if resp.status_code != 200:
            return None
        data = resp.json()
        translations = (data.get("data") or {}).get("translations") or []
        if translations:
            return translations[0].get("translatedText")
    except Exception:
        return None
    return None


def _translate_libre_configured(text: str, src: str, tgt: str) -> str | None:
    """User-configured LibreTranslate instance."""
    if not LIBRETRANSLATE_URL:
        return None
    code_map = {"iw": "he", "zh": "zh"}
    payload = {
        "q": text,
        "source": code_map.get(src, src),
        "target": code_map.get(tgt, tgt),
        "format": "text",
    }
    if LIBRETRANSLATE_API_KEY:
        payload["api_key"] = LIBRETRANSLATE_API_KEY
    try:
        resp = requests.post(
            f"{LIBRETRANSLATE_URL}/translate",
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        return (resp.json() or {}).get("translatedText") or None
    except Exception:
        return None


def _translate_google_free(text: str, src: str, tgt: str) -> str | None:
    """Unofficial Google GTX endpoint (rate-limited)."""
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": text}
    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=12)
        if resp.status_code == 429:
            return None
        resp.raise_for_status()
        data = resp.json()
        if not data or not data[0]:
            return None
        return "".join(part[0] for part in data[0] if part and part[0])
    except Exception:
        return None


def _translate_mymemory(text: str, src: str, tgt: str) -> str | None:
    """MyMemory free API (~1000 req/day, no key)."""
    code_map = {"zh": "zh-CN", "iw": "he"}
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text[:450],
        "langpair": f"{code_map.get(src, src)}|{code_map.get(tgt, tgt)}",
    }
    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("responseStatus") != 200:
            return None
        translated = (data.get("responseData") or {}).get("translatedText") or ""
        if not translated or "MYMEMORY WARNING" in translated.upper():
            return None
        return translated
    except Exception:
        return None


def _translate_chunk(text: str, src: str, tgt: str) -> str:
    """Translate one chunk via the best available provider."""
    text = (text or "").strip()
    if not text:
        return ""

    providers = [
        ("DeepL", _translate_deepl),
        ("Google Cloud", _translate_google_official),
        ("LibreTranslate", _translate_libre_configured),
        ("Google Free", _translate_google_free),
        ("MyMemory", _translate_mymemory),
    ]

    errors = []
    for name, fn in providers:
        try:
            result = fn(text, src, tgt)
            if result:
                return result
        except Exception as e:
            errors.append(f"{name}: {e}")

    configured = any([DEEPL_API_KEY, GOOGLE_TRANSLATE_API_KEY, LIBRETRANSLATE_URL])
    if not configured:
        hint = (
            " No API key configured. For reliable translation set DEEPL_API_KEY "
            "(free at deepl.com/pro-api) or GOOGLE_TRANSLATE_API_KEY."
        )
    else:
        hint = " Check your API key / quota."
    return f"[Translation error: All providers failed or are rate-limited.{hint}]"


def google_translate_fallback(text: str, src: str, tgt: str) -> str:
    """Translate text; split long input into chunks."""
    text = (text or "").strip()
    if not text:
        return ""
    max_len = 450
    if len(text) <= max_len:
        return _translate_chunk(text, src, tgt)

    parts = re.split(r"(?<=[.!?।])\s+", text)
    chunks, buf = [], ""
    for p in parts:
        if len(buf) + len(p) + 1 <= max_len:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                chunks.append(buf)
            if len(p) > max_len:
                for i in range(0, len(p), max_len):
                    chunks.append(p[i : i + max_len])
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)

    results = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(0.3)
        results.append(_translate_chunk(chunk, src, tgt))
    return " ".join(results)


def detect_language(text: str) -> str:
    # Prefer Google free detect; fall back to "en"
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text[:200]}
        resp = requests.get(url, params=params, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data[2] if len(data) > 2 else "en"
    except Exception:
        pass
    return "en"


def smart_translate(text: str, src_code: str, tgt_code: str) -> str:
    if not text.strip():
        return ""
    return google_translate_fallback(text, src_code, tgt_code)


def translation_status() -> dict:
    """Return which providers are configured (for UI / health)."""
    return {
        "deepl": bool(DEEPL_API_KEY),
        "google_cloud": bool(GOOGLE_TRANSLATE_API_KEY),
        "libretranslate": bool(LIBRETRANSLATE_URL),
        "free_fallback": True,
    }


def find_ambiguous_words(text: str) -> list:
    words = re.findall(r"\b\w+\b", text.lower())
    found = []
    for w in words:
        if w in AMBIGUOUS_WORDS and w not in found:
            found.append(w)
    return found


def auto_detect_sense(word: str, text: str) -> str:
    entry = AMBIGUOUS_WORDS.get(word)
    if not entry:
        return ""
    text_lower = text.lower()
    best, best_score = entry["default_sense"], 0
    for sense, info in entry["senses"].items():
        score = sum(1 for kw in info["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best = sense
    return best


def build_disambiguated_text(original: str, word_sense_map: dict) -> str:
    result = original
    for word, (sense, hint) in word_sense_map.items():
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(f"{word} ({hint})", result, count=1)
    return result


def strip_context_hints(text: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", text)


def get_tts_audio_b64(text: str, lang_code: str) -> str | None:
    try:
        url = "https://translate.google.com/translate_tts"
        params = {"ie": "UTF-8", "client": "tw-ob", "tl": lang_code, "q": text[:200]}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        if resp.status_code == 200 and resp.content:
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        pass
    return None


def get_romanization(text: str, src_code: str) -> str:
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": src_code, "tl": "en", "dt": "rm", "q": text}
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if data and data[0]:
            parts = [p[3] for p in data[0] if len(p) > 3 and p[3]]
            return " ".join(parts) if parts else ""
    except Exception:
        pass
    return ""


def allowed_file(filename, exts):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in exts


def read_upload(file_storage):
    return file_storage.read()


# ── Routes: pages ──────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return render_template("index.html", languages=list(LANG_MAP.keys()))


@app.route("/translator")
@login_required
def translator_page():
    return render_template("translator.html", languages=list(LANG_MAP.keys()))


@app.route("/pdf")
@login_required
def pdf_page():
    return render_template("pdf.html")


@app.route("/convert")
@login_required
def convert_page():
    return render_template("convert.html")


@app.route("/ocr")
@login_required
def ocr_page():
    return render_template("ocr.html", languages=list(LANG_MAP.keys()))


@app.route("/images")
@login_required
def images_page():
    return render_template("images.html")


@app.route("/tts")
@login_required
def tts_page():
    return render_template("tts.html", languages=list(LANG_MAP.keys()))


@app.route("/qr")
@login_required
def qr_page():
    return render_template("qr.html")



@app.route("/utilities")
@login_required
def utilities_page():
    return render_template("utilities.html")


@app.route("/history")
@login_required
def history_page():
    return render_template("history.html")

# ── API: Translator ────────────────────────────────────────────────────────
@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    src_lang = data.get("src_lang", "English")
    tgt_lang = data.get("tgt_lang", "Hindi")
    auto_detect = data.get("auto_detect", False)
    senses = data.get("senses") or {}  # {word: sense_name}

    if not text:
        return jsonify({"error": "Please enter some text."}), 400

    src_code = LANG_MAP.get(src_lang, "en")
    tgt_code = LANG_MAP.get(tgt_lang, "hi")

    if auto_detect:
        detected = detect_language(text)
        src_code = detected
        src_lang = LANG_CODES_REVERSE.get(detected, detected)

    if src_code == tgt_code:
        return jsonify({"error": "Source and target languages must be different."}), 400

    # Disambiguation
    ambig = find_ambiguous_words(text)
    word_sense_map = {}
    for w in ambig:
        sense_name = senses.get(w) or auto_detect_sense(w, text)
        entry = AMBIGUOUS_WORDS[w]
        if sense_name in entry["senses"]:
            word_sense_map[w] = (sense_name, entry["senses"][sense_name]["hint"])
        else:
            default = entry["default_sense"]
            word_sense_map[w] = (default, entry["senses"][default]["hint"])

    to_translate = build_disambiguated_text(text, word_sense_map) if word_sense_map else text
    translated = smart_translate(to_translate, src_code, tgt_code)
    clean = strip_context_hints(translated)

    # Skip extra API calls if primary translation failed
    failed = clean.startswith("[Translation error:")
    roman = ""
    back = ""
    if not failed:
        if tgt_code not in ("en", "la"):
            roman = get_romanization(clean, tgt_code)
        if len(text) < 400:
            time.sleep(0.5)  # gap before back-translate to reduce rate limits
            back = smart_translate(clean, tgt_code, src_code)

    return jsonify({
        "translated": clean,
        "raw_with_hints": translated,
        "source_lang": src_lang,
        "source_code": src_code,
        "romanization": roman,
        "back_translation": back,
        "ambiguous": [
            {
                "word": w,
                "senses": list(AMBIGUOUS_WORDS[w]["senses"].keys()),
                "auto": auto_detect_sense(w, text),
                "default": AMBIGUOUS_WORDS[w]["default_sense"],
            }
            for w in ambig
        ],
    })


@app.route("/api/detect-lang", methods=["POST"])
def api_detect_lang():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "")[:300]
    if not text.strip():
        return jsonify({"code": "en", "name": "English"})
    code = detect_language(text)
    return jsonify({"code": code, "name": LANG_CODES_REVERSE.get(code, code)})


@app.route("/api/ambiguous", methods=["POST"])
def api_ambiguous():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or ""
    ambig = find_ambiguous_words(text)
    result = []
    for w in ambig:
        result.append({
            "word": w,
            "senses": list(AMBIGUOUS_WORDS[w]["senses"].keys()),
            "auto": auto_detect_sense(w, text),
            "default": AMBIGUOUS_WORDS[w]["default_sense"],
        })
    return jsonify({"ambiguous": result})


# ── API: TTS ───────────────────────────────────────────────────────────────


@app.route("/api/translation-status")
def api_translation_status():
    return jsonify(translation_status())

@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    lang = data.get("lang", "English")
    if not text:
        return jsonify({"error": "No text provided."}), 400
    code = LANG_MAP.get(lang, "en")
    b64 = get_tts_audio_b64(text, code)
    if not b64:
        return jsonify({"error": "TTS unavailable for this language or text."}), 400
    return jsonify({"audio_b64": b64, "mime": "audio/mp3"})


# ── API: PDF tools ─────────────────────────────────────────────────────────
@app.route("/api/pdf/merge", methods=["POST"])
def api_pdf_merge():
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Upload at least 2 PDF files."}), 400
    try:
        blobs = [f.read() for f in files]
        result = pdf_merge(blobs)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/split", methods=["POST"])
def api_pdf_split():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    mode = request.form.get("mode", "all")  # all | range
    try:
        data = f.read()
        if mode == "range":
            start = int(request.form.get("start", 1))
            end = int(request.form.get("end", 1))
            result = pdf_split_range(data, start, end)
            return send_file(io.BytesIO(result), mimetype="application/pdf",
                             as_attachment=True, download_name=f"pages_{start}-{end}.pdf")
        pages = pdf_split(data)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, content in pages:
                zf.writestr(name, content)
        buf.seek(0)
        return send_file(buf, mimetype="application/zip",
                         as_attachment=True, download_name="split_pages.zip")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/rotate", methods=["POST"])
def api_pdf_rotate():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    degrees = int(request.form.get("degrees", 90))
    try:
        result = pdf_rotate(f.read(), degrees)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="rotated.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/compress", methods=["POST"])
def api_pdf_compress():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        result = pdf_compress_simple(f.read())
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="compressed.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/watermark", methods=["POST"])
def api_pdf_watermark():
    f = request.files.get("file")
    text = request.form.get("text", "CONFIDENTIAL")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        result = pdf_add_watermark(f.read(), text)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="watermarked.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/protect", methods=["POST"])
def api_pdf_protect():
    f = request.files.get("file")
    password = request.form.get("password", "")
    if not f or not password:
        return jsonify({"error": "File and password required."}), 400
    try:
        result = pdf_protect(f.read(), password)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="protected.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/unlock", methods=["POST"])
def api_pdf_unlock():
    f = request.files.get("file")
    password = request.form.get("password", "")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        result = pdf_unlock(f.read(), password)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="unlocked.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/extract-text", methods=["POST"])
def api_pdf_extract_text():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        text = pdf_extract_text(f.read())
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/extract-images", methods=["POST"])
def api_pdf_extract_images():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        images = pdf_extract_images(f.read())
        if not images:
            return jsonify({"error": "No images found in PDF."}), 400
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, img_bytes in enumerate(images):
                zf.writestr(f"image_{i+1}.png", img_bytes)
        buf.seek(0)
        return send_file(buf, mimetype="application/zip",
                         as_attachment=True, download_name="pdf_images.zip")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/to-images", methods=["POST"])
def api_pdf_to_images():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        imgs = pdf_to_images(f.read())
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, img_bytes in enumerate(imgs):
                zf.writestr(f"page_{i+1}.png", img_bytes)
        buf.seek(0)
        return send_file(buf, mimetype="application/zip",
                         as_attachment=True, download_name="pdf_pages.zip")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/from-images", methods=["POST"])
def api_pdf_from_images():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Upload at least one image."}), 400
    try:
        blobs = [f.read() for f in files]
        result = images_to_pdf(blobs)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="from_images.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/info", methods=["POST"])
def api_pdf_info():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file."}), 400
    try:
        count = pdf_get_page_count(f.read())
        return jsonify({"pages": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Word ↔ PDF ────────────────────────────────────────────────────────
@app.route("/api/convert/word-to-pdf", methods=["POST"])
def api_word_to_pdf():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        result = word_to_pdf(f.read())
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="converted.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert/pdf-to-word", methods=["POST"])
def api_pdf_to_word():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400
    try:
        result = pdf_to_word(f.read())
        return send_file(io.BytesIO(result),
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         as_attachment=True, download_name="converted.docx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert/text-to-pdf", methods=["POST"])
def api_text_to_pdf():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided."}), 400
    try:
        result = text_to_pdf(text)
        return send_file(io.BytesIO(result), mimetype="application/pdf",
                         as_attachment=True, download_name="document.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert/text-to-docx", methods=["POST"])
def api_text_to_docx():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided."}), 400
    try:
        result = text_to_docx(text)
        return send_file(io.BytesIO(result),
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         as_attachment=True, download_name="document.docx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: OCR & Text↔Image ──────────────────────────────────────────────────
@app.route("/api/ocr", methods=["POST"])
def api_ocr():
    f = request.files.get("file")
    lang = request.form.get("lang", "English")
    if not f:
        return jsonify({"error": "No image uploaded."}), 400
    try:
        img = Image.open(io.BytesIO(f.read()))
        code = LANG_MAP.get(lang, "en")
        tess = TESSERACT_LANG_MAP.get(code, "eng")
        text = pytesseract.image_to_string(img, lang=tess)
        return jsonify({"text": text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/text-to-image", methods=["POST"])
def api_text_to_image():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided."}), 400
    try:
        result = text_to_image(
            text,
            width=int(data.get("width", 800)),
            height=int(data.get("height", 400)),
            bg_color=data.get("bg_color", "#0f1420"),
            text_color=data.get("text_color", "#e2e8f8"),
            font_size=int(data.get("font_size", 32)),
        )
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="text_image.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Image tools ───────────────────────────────────────────────────────
@app.route("/api/image/convert", methods=["POST"])
def api_image_convert():
    f = request.files.get("file")
    fmt = request.form.get("format", "PNG").upper()
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        result = image_convert_format(f.read(), fmt)
        mime = f"image/{fmt.lower()}" if fmt != "JPG" else "image/jpeg"
        ext = "jpg" if fmt == "JPG" else fmt.lower()
        return send_file(io.BytesIO(result), mimetype=mime,
                         as_attachment=True, download_name=f"converted.{ext}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/compress", methods=["POST"])
def api_image_compress():
    f = request.files.get("file")
    quality = int(request.form.get("quality", 70))
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        result = image_compress(f.read(), quality)
        return send_file(io.BytesIO(result), mimetype="image/jpeg",
                         as_attachment=True, download_name="compressed.jpg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/resize", methods=["POST"])
def api_image_resize():
    f = request.files.get("file")
    width = int(request.form.get("width", 800))
    height = int(request.form.get("height", 600))
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        result = image_resize(f.read(), width, height)
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="resized.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/rotate", methods=["POST"])
def api_image_rotate():
    f = request.files.get("file")
    degrees = int(request.form.get("degrees", 90))
    flip = request.form.get("flip", "none")
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        flip_h = flip == "horizontal"
        flip_v = flip == "vertical"
        result = image_rotate_flip(f.read(), degrees, flip_h, flip_v)
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="rotated.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/watermark", methods=["POST"])
def api_image_watermark():
    f = request.files.get("file")
    text = request.form.get("text", "Watermark")
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        result = image_add_watermark_text(f.read(), text)
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="watermarked.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/grayscale", methods=["POST"])
def api_image_grayscale():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        result = image_to_grayscale(f.read())
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="grayscale.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/filter", methods=["POST"])
def api_image_filter():
    f = request.files.get("file")
    filt = request.form.get("filter", "BLUR")
    if not f:
        return jsonify({"error": "No image."}), 400
    try:
        # processors expects title-case names like "Blur", "Sharpen"
        name_map = {
            "BLUR": "Blur", "SHARPEN": "Sharpen", "EDGE_ENHANCE": "Edge Enhance",
            "EMBOSS": "Emboss", "CONTOUR": "Contour", "SMOOTH": "Smooth",
        }
        filt_name = name_map.get(filt.upper(), filt)
        result = image_apply_filter(f.read(), filt_name)
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="filtered.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/qr", methods=["POST"])
def api_qr():
    data = request.get_json(silent=True) or {}
    content = data.get("data", "")
    if not content.strip():
        return jsonify({"error": "No data provided."}), 400
    try:
        result = generate_qr_code(
            content,
            box_size=int(data.get("box_size", 10)),
            fill_color=data.get("fill_color", "black"),
            back_color=data.get("back_color", "white"),
        )
        return send_file(io.BytesIO(result), mimetype="image/png",
                         as_attachment=True, download_name="qrcode.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Error handlers ─────────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large (max 80 MB)."}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
