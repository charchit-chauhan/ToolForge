"""
LinguaAI Toolkit — All-in-one document, image, and language utility suite.
Combines: Translator (with disambiguation engine), PDF tools (merge/split/
compress/rotate/watermark/protect), Word↔PDF conversion, Image↔Text (OCR +
text-to-image), Image format/compression tools, and Text↔Speech.
"""

import streamlit as st
import requests
import html
import time
import base64
import re
import io
import os
from pathlib import Path
from datetime import datetime

from PIL import Image
import pytesseract

from processors import (
    pdf_merge, pdf_split, pdf_split_range, pdf_rotate, pdf_compress_simple,
    pdf_add_watermark, pdf_protect, pdf_unlock, pdf_extract_text,
    pdf_extract_images, pdf_to_images, images_to_pdf, pdf_get_page_count,
    pdf_to_word, word_to_pdf, text_to_docx, text_to_pdf, docx_extract_text,
    image_convert_format, image_compress, image_resize, image_rotate_flip,
    image_add_watermark_text, image_to_grayscale, image_apply_filter,
    text_to_image, generate_qr_code, WORKDIR,
)

lang_map = {
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
LANG_CODES_REVERSE = {v: k for k, v in lang_map.items()}

TESSERACT_LANG_MAP = {
    "en": "eng", "hi": "hin", "fr": "fra", "de": "deu", "es": "spa",
    "zh": "chi_sim", "ja": "jpn", "ar": "ara", "pt": "por", "ru": "rus",
    "it": "ita", "ko": "kor", "auto": "eng",
}

# ════════════════════════════════════════════════
#  WORD-SENSE DISAMBIGUATION DICTIONARY (from translator)
# ════════════════════════════════════════════════
AMBIGUOUS_WORDS = {
    "bat": {"senses": {
        "Animal (flying mammal)": {"hint": "the flying mammal animal", "keywords": ["flying","cave","nocturnal","mammal","wing","sonar","vampire","fruit bat"]},
        "Cricket/Baseball bat": {"hint": "a cricket or baseball bat (sports equipment)", "keywords": ["cricket","baseball","hit","swing","sport","wicket","run","innings","score"]},
        "Verb: to bat": {"hint": "a verb meaning to hit or strike", "keywords": ["batting","batted","eyelid","blink"]},
    }, "default_sense": "Animal (flying mammal)"},
    "bats": {"senses": {
        "Animals (flying mammals)": {"hint": "flying mammal animals (plural)", "keywords": ["flying","cave","nocturnal","mammal","wing","sonar","vampire","fruit","colony"]},
        "Cricket/Baseball bats": {"hint": "cricket or baseball bats (plural)", "keywords": ["cricket","baseball","hit","swing","willow","rubber"]},
        "Verb: bats": {"hint": "a verb (he/she bats)", "keywords": ["he bats","she bats","batting","average"]},
        "Crazy/insane (slang)": {"hint": "crazy or insane (informal slang)", "keywords": ["crazy","mad","insane","nuts","mental"]},
    }, "default_sense": "Animals (flying mammals)"},
    "bank": {"senses": {
        "Financial institution": {"hint": "a financial institution", "keywords": ["money","account","loan","deposit","withdraw","interest","finance","savings"]},
        "River bank": {"hint": "the bank/shore of a river or lake", "keywords": ["river","lake","stream","shore","water","flood","fish","boat"]},
        "Verb: to bank": {"hint": "a verb meaning to tilt or rely on", "keywords": ["banked","banking","turn","aircraft","tilt","rely","count on"]},
    }, "default_sense": "Financial institution"},
    "crane": {"senses": {
        "Bird": {"hint": "a crane bird", "keywords": ["bird","fly","migration","flock","nest","feather","beak","wetland"]},
        "Construction crane": {"hint": "a construction crane machine", "keywords": ["construction","lift","building","machine","operator","site","load","hoist"]},
        "Verb: to crane": {"hint": "a verb meaning to stretch one's neck", "keywords": ["neck","head","look","peer","stretch","craning"]},
    }, "default_sense": "Construction crane"},
    "spring": {"senses": {
        "Season": {"hint": "the season", "keywords": ["summer","winter","autumn","fall","season","flower","bloom","warm","april","march"]},
        "Coil spring": {"hint": "a mechanical coil spring", "keywords": ["coil","metal","bounce","compress","elastic","mattress","mechanical","steel"]},
        "Water spring": {"hint": "a natural water spring", "keywords": ["water","natural","source","well","mineral","hot spring","geyser"]},
        "Verb: to spring": {"hint": "a verb meaning to jump or leap", "keywords": ["jump","leap","spring up","sprung","sprang","pounce","surprise"]},
    }, "default_sense": "Season"},
    "fly": {"senses": {
        "Insect": {"hint": "the insect", "keywords": ["insect","bug","swat","buzz","housefly","mosquito","pest","wings"]},
        "Verb: to fly": {"hint": "a verb meaning to travel through the air", "keywords": ["plane","airplane","aircraft","pilot","airport","flight","soar","bird","kite"]},
        "Trouser fly": {"hint": "the zipper flap on trousers", "keywords": ["trouser","zipper","pants","button","clothing"]},
    }, "default_sense": "Verb: to fly"},
    "light": {"senses": {
        "Illumination": {"hint": "illumination or brightness", "keywords": ["sun","lamp","bright","dark","shine","glow","beam","torch","candle"]},
        "Not heavy": {"hint": "not heavy (adjective)", "keywords": ["heavy","weight","carry","lift","feather","kg","gram","pound"]},
        "Pale color": {"hint": "a pale/soft color", "keywords": ["color","colour","shade","pale","blue","green","pink","tone"]},
        "Verb: to light": {"hint": "a verb meaning to ignite", "keywords": ["fire","candle","match","ignite","flame","burn","kindle"]},
    }, "default_sense": "Illumination"},
    "match": {"senses": {
        "Sports match": {"hint": "a sports game or competition", "keywords": ["cricket","football","game","play","score","team","win","lose","tournament","final"]},
        "Fire match": {"hint": "a matchstick used to light fire", "keywords": ["fire","light","flame","burn","candle","strike","ignite","box"]},
        "Verb: to match": {"hint": "a verb meaning to correspond or pair", "keywords": ["pair","suit","fit","correspond","colour","color","pattern","identical"]},
    }, "default_sense": "Verb: to match"},
}

# ════════════════════════════════════════════════
#  CORE TRANSLATION ENGINE
# ════════════════════════════════════════════════
def google_translate_fallback(text: str, src: str, tgt: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": text}
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return html.unescape("".join(part[0] for part in data[0] if part[0]))

def detect_language(text: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        detected_code = data[2] if len(data) > 2 else None
        return LANG_CODES_REVERSE.get(detected_code, detected_code or "Unknown")
    except Exception:
        return "Unknown"

def smart_translate(text: str, src_code: str, tgt_code: str):
    result = google_translate_fallback(text, src_code, tgt_code)
    return result, "Google Translate"

def find_ambiguous_words(text: str) -> list:
    words_in_text = set(re.findall(r'\b\w+\b', text.lower()))
    return [w for w in AMBIGUOUS_WORDS if w in words_in_text]

def auto_detect_sense(word: str, text: str):
    entry = AMBIGUOUS_WORDS.get(word.lower())
    if not entry:
        return None
    text_lower = text.lower()
    best_sense, best_score = None, 0
    for sense_name, sense_data in entry["senses"].items():
        score = sum(1 for kw in sense_data["keywords"] if kw in text_lower)
        if score > best_score:
            best_score, best_sense = score, sense_name
    return best_sense if best_score >= 1 else None

def build_disambiguated_text(original: str, word_sense_map: dict) -> str:
    if not word_sense_map:
        return original
    hint_parts = [f"[Context: the word '{w}' here means {hint}]" for w, (_, hint) in word_sense_map.items()]
    return " ".join(hint_parts) + " " + original

def strip_context_hints(text: str) -> str:
    return re.sub(r'\[Context:[^\]]*\]\s*', '', text).strip()

def get_tts_audio_b64(text: str, lang_code: str):
    url = "https://translate.google.com/translate_tts"
    params = {"ie": "UTF-8", "q": text[:200], "tl": lang_code, "client": "gtx"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.content:
            return base64.b64encode(resp.content).decode()
    except Exception:
        pass
    return None

def show_tts_player(text: str, lang_code: str, label: str = "🔊 Listen"):
    b64 = get_tts_audio_b64(text, lang_code)
    if b64:
        st.markdown(f"**{label}**")
        st.markdown(f'<audio controls style="width:100%;margin-top:6px"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    else:
        st.caption("⚠️ TTS not available for this language.")

def get_romanization(text: str, src_code: str):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": src_code, "tl": "en", "dt": ["t", "rm"], "q": text}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        parts = [seg[3] for seg in data[0] if seg and len(seg) > 3 and seg[3]]
        return " ".join(parts) if parts else None
    except Exception:
        return None

def back_translate(text: str, tgt_code: str, src_code: str = "en") -> str:
    try:
        result, _ = smart_translate(text, tgt_code, src_code)
        return result
    except Exception:
        return "Back-translation failed."

def similarity_score(a: str, b: str) -> int:
    a, b = a.lower().strip(), b.lower().strip()
    if not a or not b:
        return 0
    a_words, b_words = set(a.split()), set(b.split())
    if not a_words:
        return 0
    return int(len(a_words & b_words) / len(a_words) * 100)

def translate_to_multiple(text: str, src_code: str, targets: list) -> dict:
    results = {}
    for lang_name in targets:
        tgt_code = lang_map[lang_name]
        try:
            t, engine = smart_translate(text, src_code, tgt_code)
            results[lang_name] = {"text": t, "engine": engine, "code": tgt_code}
        except Exception as e:
            results[lang_name] = {"text": f"Error: {e}", "engine": "—", "code": tgt_code}
        time.sleep(0.1)
    return results

def ocr_image_local(image: Image.Image, lang_code: str = "eng") -> str:
    """Local Tesseract OCR — no external API, works offline."""
    try:
        return pytesseract.image_to_string(image, lang=lang_code).strip()
    except Exception:
        # Fallback to English if language pack missing
        return pytesseract.image_to_string(image, lang="eng").strip()

# ════════════════════════════════════════════════
#  STREAMLIT APP
# ════════════════════════════════════════════════
st.set_page_config(page_title="LinguaAI Toolkit", layout="wide", page_icon="🧰")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,700;0,900;1,300;1,700&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');

:root {
  --bg: #080b12; --surface: #0f1420; --surface2: #161d2e; --surface3: #1e2740;
  --border: #1f2d4a; --border2: #2a3d60;
  --teal: #00c9a7; --teal-dim: #00896f; --teal-glow: rgba(0,201,167,0.15);
  --coral: #ff6b6b; --gold: #ffd166; --sky: #74c0fc; --violet: #b89bff;
  --text: #e2e8f8; --text2: #a0aec8; --muted: #4a5878;
  --success: #00c9a7; --warn: #ffd166; --danger: #ff6b6b;
  --r: 12px; --r-sm: 8px; --r-lg: 18px;
}
* { box-sizing: border-box; }
html, body, [class*="css"], [class*="st-"] {
  font-family: 'Outfit', sans-serif !important;
  background: var(--bg) !important; color: var(--text) !important;
}
.main, section.main { background: var(--bg) !important; }
.block-container { padding: 0 2rem 4rem !important; max-width: 1240px !important; }

.hero-wrap {
  background: linear-gradient(160deg, #0f1d35 0%, #080b12 55%);
  border-bottom: 1px solid var(--border);
  padding: 2.4rem 3rem 2rem; position: relative; overflow: hidden;
  margin: 0 -2rem 2rem;
}
.hero-wrap::before {
  content: ''; position: absolute; top: -60px; right: -60px;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(0,201,167,0.12) 0%, transparent 65%);
  border-radius: 50%; pointer-events: none;
}
.hero-wrap::after {
  content: ''; position: absolute; bottom: -80px; left: 10%;
  width: 260px; height: 260px;
  background: radial-gradient(circle, rgba(184,155,255,0.08) 0%, transparent 65%);
  border-radius: 50%; pointer-events: none;
}
.hero-inner { position: relative; z-index: 1; }
.hero-eyebrow { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: var(--teal); letter-spacing: 0.22em; text-transform: uppercase; margin-bottom: 0.6rem; }
.hero-title { font-family: 'Fraunces', serif; font-size: 3.2rem; font-weight: 900; line-height: 0.95; letter-spacing: -0.03em; color: var(--text); margin-bottom: 0.6rem; }
.hero-title em { font-style: italic; font-weight: 300; background: linear-gradient(120deg, var(--teal), var(--violet)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-sub { font-size: 0.9rem; font-weight: 300; color: var(--text2); max-width: 560px; line-height: 1.6; }

.tool-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r-lg); padding: 1.3rem 1.4rem; height: 100%;
  transition: all 0.18s; cursor: default;
}
.tool-card:hover { border-color: var(--teal); transform: translateY(-2px); }
.tool-icon { font-size: 1.6rem; margin-bottom: 0.5rem; }
.tool-name { font-family: 'Fraunces', serif; font-weight: 700; font-size: 1.05rem; color: var(--text); margin-bottom: 0.3rem; }
.tool-desc { font-size: 0.78rem; color: var(--text2); line-height: 1.4; }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 1.5rem 1.7rem; margin-bottom: 1rem; }
.card-accent { border-top: 2px solid var(--teal); }
.card-label { font-family: 'DM Mono', monospace; font-size: 0.65rem; font-weight: 500; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.7rem; }
.card-result { background: var(--surface2); border: 1px solid var(--border2); border-radius: var(--r); padding: 1.2rem 1.4rem; font-size: 1.02rem; font-weight: 300; line-height: 1.75; color: var(--text); min-height: 70px; border-left: 3px solid var(--teal); white-space: pre-wrap; }
.engine-pill { display: inline-flex; align-items: center; gap: 0.4rem; background: var(--surface3); border: 1px solid var(--border2); border-radius: 20px; padding: 0.18rem 0.7rem; font-family: 'DM Mono', monospace; font-size: 0.62rem; color: var(--teal); letter-spacing: 0.06em; margin-top: 0.6rem; }
.engine-pill::before { content: '●'; font-size: 0.4rem; }

div[data-testid="stTabs"] { border-bottom: 1px solid var(--border) !important; margin-bottom: 1.5rem !important; }
div[data-testid="stTabs"] button { font-family: 'Outfit', sans-serif !important; font-size: 0.8rem !important; font-weight: 500 !important; letter-spacing: 0.03em !important; color: var(--muted) !important; border: none !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; padding: 0.6rem 1rem !important; background: transparent !important; transition: all 0.18s !important; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--teal) !important; border-bottom: 2px solid var(--teal) !important; }
div[data-testid="stTabs"] button:hover { color: var(--text) !important; }

div[data-testid="stSelectbox"] > div > div { background: var(--surface2) !important; border: 1px solid var(--border2) !important; border-radius: var(--r-sm) !important; color: var(--text) !important; font-family: 'Outfit', sans-serif !important; font-size: 0.88rem !important; }
div[data-testid="stSelectbox"] > div > div:focus-within { border-color: var(--teal) !important; box-shadow: 0 0 0 3px var(--teal-glow) !important; }
div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label, div[data-testid="stNumberInput"] label, div[data-testid="stTextInput"] label, div[data-testid="stSlider"] label, div[data-testid="stFileUploader"] label { font-family: 'DM Mono', monospace !important; font-size: 0.65rem !important; font-weight: 500 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; color: var(--muted) !important; }

div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { background: var(--surface2) !important; border: 1px solid var(--border2) !important; border-radius: var(--r-sm) !important; color: var(--text) !important; font-family: 'Outfit', sans-serif !important; font-size: 0.95rem !important; font-weight: 300 !important; line-height: 1.7 !important; caret-color: var(--teal) !important; transition: all 0.18s !important; }
div[data-testid="stTextArea"] textarea:focus, div[data-testid="stTextInput"] input:focus { border-color: var(--teal) !important; box-shadow: 0 0 0 3px var(--teal-glow) !important; outline: none !important; }

div[data-testid="stButton"] > button { background: var(--teal) !important; color: #050810 !important; border: none !important; border-radius: var(--r-sm) !important; font-family: 'Outfit', sans-serif !important; font-weight: 600 !important; font-size: 0.86rem !important; letter-spacing: 0.03em !important; padding: 0.58rem 1.5rem !important; transition: all 0.16s !important; box-shadow: 0 0 18px rgba(0,201,167,0.28) !important; }
div[data-testid="stButton"] > button:hover { background: #00e0ba !important; box-shadow: 0 0 28px rgba(0,201,167,0.42) !important; transform: translateY(-1px) !important; }
div[data-testid="stDownloadButton"] > button { background: transparent !important; color: var(--text2) !important; border: 1px solid var(--border2) !important; border-radius: var(--r-sm) !important; font-family: 'Outfit', sans-serif !important; font-weight: 400 !important; font-size: 0.82rem !important; box-shadow: none !important; padding: 0.45rem 1rem !important; }
div[data-testid="stDownloadButton"] > button:hover { border-color: var(--teal) !important; color: var(--teal) !important; opacity: 1 !important; }

div[data-testid="stCheckbox"] label, div[data-testid="stRadio"] label { font-size: 0.84rem !important; color: var(--text2) !important; }
div[data-testid="stCheckbox"] span[data-testid="stCheckboxChecked"] { background: var(--teal) !important; border-color: var(--teal) !important; }
div[data-testid="stSlider"] div[role="slider"] { background: var(--teal) !important; }
div[data-testid="stAlert"] { border-radius: var(--r-sm) !important; font-size: 0.84rem !important; border: 1px solid var(--border) !important; }
div[data-testid="stExpander"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; margin-bottom: 0.5rem !important; }
div[data-testid="stExpander"] summary { font-size: 0.84rem !important; font-weight: 500 !important; color: var(--text2) !important; padding: 0.75rem 1.1rem !important; }
div[data-testid="stExpander"] summary:hover { color: var(--teal) !important; }
div[data-testid="stMetric"] { background: var(--surface2) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; padding: 1rem 1.2rem !important; }
div[data-testid="stMetric"] label { font-family: 'DM Mono', monospace !important; font-size: 0.62rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; color: var(--muted) !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-family: 'Fraunces', serif !important; font-size: 1.8rem !important; color: var(--teal) !important; }
div[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, var(--teal-dim), var(--teal)) !important; border-radius: 4px !important; }
div[data-testid="stProgressBar"] > div { background: var(--surface2) !important; border-radius: 4px !important; height: 4px !important; }
div[data-testid="stFileUploader"] { background: var(--surface2) !important; border: 2px dashed var(--border2) !important; border-radius: var(--r) !important; padding: 1.1rem !important; transition: border-color 0.18s !important; }
div[data-testid="stFileUploader"]:hover { border-color: var(--teal) !important; }
section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
section[data-testid="stSidebar"] * { color: var(--text) !important; }
div[data-testid="stCaptionContainer"] p, small { color: var(--muted) !important; font-size: 0.74rem !important; }
::-webkit-scrollbar { width: 4px; height: 4px; } ::-webkit-scrollbar-track { background: var(--bg); } ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }
hr { border-color: var(--border) !important; opacity: 0.5 !important; }
h1, h2, h3 { font-family: 'Fraunces', serif !important; color: var(--text) !important; }
h3 { font-size: 1.05rem !important; font-weight: 700 !important; margin-bottom: 0.75rem !important; }
.disambig-panel { background: rgba(0,201,167,0.04); border: 1px solid rgba(0,201,167,0.2); border-left: 3px solid var(--teal); border-radius: var(--r); padding: 1rem 1.2rem; margin: 0.8rem 0; }
.score-bar-bg { background: var(--surface3); border-radius: 4px; height: 6px; overflow: hidden; margin: 0.4rem 0; }
.score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s; }
.section-title { font-family: 'Fraunces', serif; font-size: 1.5rem; font-weight: 700; color: var(--text); margin-bottom: 0.3rem; }
.section-sub { font-size: 0.85rem; color: var(--text2); margin-bottom: 1.2rem; }
.file-result-row { display:flex; align-items:center; justify-content:space-between; background:var(--surface2); border:1px solid var(--border2); border-radius:var(--r-sm); padding:0.6rem 1rem; margin-bottom:0.4rem; }
</style>
""", unsafe_allow_html=True)

# Session state
for key, default in [
    ("history", []), ("favorites", []), ("ocr_text", ""), ("active_module", "home"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── HERO ──
st.markdown("""
<div class="hero-wrap">
  <div class="hero-inner">
    <div class="hero-eyebrow">// All-in-One Document &amp; Language Suite</div>
    <div class="hero-title">Lingua<em>AI</em> Toolkit</div>
    <div class="hero-sub">Translate, convert, compress, and transform — PDF, Word, images, and text, all powered by AI in one place.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0 0.8rem; border-bottom:1px solid var(--border); margin-bottom:1rem;">
      <div style="font-family:'Fraunces',serif;font-size:1.3rem;font-weight:900;color:var(--text);">Lingua<span style="color:var(--teal);font-style:italic;">AI</span></div>
      <div style="font-family:'DM Mono',monospace;font-size:0.58rem;color:var(--muted);letter-spacing:0.14em;text-transform:uppercase;margin-top:0.2rem;">Toolkit Suite</div>
    </div>
    """, unsafe_allow_html=True)

    module = st.radio("Module", [
        "🏠 Home", "🌐 Translator", "📄 PDF Tools", "🔁 Word ⇄ PDF",
        "🖼️ Image ⇄ Text", "🎨 Image Tools", "🔊 Text ⇄ Speech",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;color:var(--muted);letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">Session</div>', unsafe_allow_html=True)
    st.metric("Translations", len(st.session_state.history))
    st.metric("Favorites", len(st.session_state.favorites))


# ════════════════════════════════════════════════
#  HOME DASHBOARD
# ════════════════════════════════════════════════
if module == "🏠 Home":
    st.markdown('<div class="section-title">Choose a tool</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Everything you need for documents, images, and language — in one toolkit.</div>', unsafe_allow_html=True)

    tools = [
        ("🌐", "Translator", "100+ languages with word-sense disambiguation, TTS, romanization, and quality checks."),
        ("📄", "PDF Tools", "Merge, split, rotate, compress, watermark, encrypt, and extract from PDFs."),
        ("🔁", "Word ⇄ PDF", "Convert Word documents to PDF and back, or build new ones from plain text."),
        ("🖼️", "Image ⇄ Text", "Extract text from images with OCR, or render text onto an image canvas."),
        ("🎨", "Image Tools", "Convert formats, compress, resize, rotate, watermark, filter, and generate QR codes."),
        ("🔊", "Text ⇄ Speech", "Convert text to natural speech audio in dozens of languages."),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(tools):
        with cols[i % 3]:
            st.markdown(f"""
<div class="tool-card">
  <div class="tool-icon">{icon}</div>
  <div class="tool-name">{name}</div>
  <div class="tool-desc">{desc}</div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Pick a module from the sidebar to get started.")


# ════════════════════════════════════════════════
#  TRANSLATOR MODULE
# ════════════════════════════════════════════════
elif module == "🌐 Translator":
    st.markdown('<div class="section-title">Translator</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">100+ languages, word-sense aware, with audio and pronunciation.</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Language Pair</div>', unsafe_allow_html=True)
    col1, col_arr, col2, col_swap = st.columns([5, 0.6, 5, 1.5])
    with col1:
        src_lang = st.selectbox("From", list(lang_map.keys()), index=0)
    with col_arr:
        st.markdown('<div style="text-align:center;padding-top:1.6rem;color:var(--border2);font-size:1.2rem;">→</div>', unsafe_allow_html=True)
    with col2:
        tgt_lang = st.selectbox("To", list(lang_map.keys()), index=1)
    with col_swap:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⇄ Swap", use_container_width=True):
            st.session_state["_swap"] = (tgt_lang, src_lang)
            st.rerun()

    opt1, opt2 = st.columns(2)
    with opt1:
        auto_detect = st.checkbox("🔍 Auto-detect language", value=False)
    with opt2:
        formality = st.select_slider("Tone", options=["Casual", "Neutral", "Formal"], value="Neutral")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Input Text</div>', unsafe_allow_html=True)
    text_input = st.text_area("Input text", height=150, placeholder="Type or paste text to translate…", label_visibility="collapsed", key="translate_input")
    if text_input:
        wc, cc = len(text_input.split()), len(text_input)
        st.markdown(f'<div style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:var(--muted);">{cc} chars · {wc} words</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Disambiguation
    ambig_words = find_ambiguous_words(text_input) if text_input.strip() else []
    word_sense_map = {}
    if ambig_words:
        st.markdown('<div class="disambig-panel">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-weight:600;color:var(--warn);margin-bottom:0.6rem;">⚠️ Ambiguous word(s): {", ".join(ambig_words)}</div>', unsafe_allow_html=True)
        for word in ambig_words:
            entry = AMBIGUOUS_WORDS[word]
            sense_names = list(entry["senses"].keys())
            auto_sense = auto_detect_sense(word, text_input)
            default_idx = sense_names.index(auto_sense) if auto_sense in sense_names else sense_names.index(entry["default_sense"])
            if auto_sense:
                st.caption(f"🤖 Auto-detected: {auto_sense}")
            chosen = st.radio(f"What does **{word}** mean?", sense_names, index=default_idx, key=f"sense_{word}")
            word_sense_map[word] = (chosen, entry["senses"][chosen]["hint"])
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 Translate"):
        src_code, tgt_code = lang_map[src_lang], lang_map[tgt_lang]
        if not auto_detect and src_lang == tgt_lang:
            st.warning("Source and target languages must be different.")
        elif not text_input.strip():
            st.warning("Please enter text to translate.")
        else:
            with st.spinner("Translating..."):
                try:
                    detected_name = None
                    if auto_detect:
                        detected_name = detect_language(text_input)
                        st.info(f"🔍 Detected: **{detected_name}**")
                        src_code = "auto"
                    prefix = {"Formal": "In a formal tone: ", "Casual": "In a casual tone: ", "Neutral": ""}[formality]
                    text_to_translate = prefix + text_input
                    if word_sense_map:
                        text_to_translate = build_disambiguated_text(text_to_translate, word_sense_map)
                        result = strip_context_hints(google_translate_fallback(text_to_translate, src_code if src_code != "auto" else "en", tgt_code))
                        engine_used = "Google Translate (disambiguated)"
                    else:
                        result, engine_used = smart_translate(text_to_translate, src_code, tgt_code)

                    st.session_state.history.append({
                        "src": src_lang if not auto_detect else (detected_name or "Auto"), "tgt": tgt_lang,
                        "original": text_input, "translated": result,
                        "time": datetime.now().strftime("%H:%M"), "engine": engine_used,
                    })

                    st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-label">{tgt_lang} — Translation</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-result">{html.escape(result)}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="engine-pill">{engine_used}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    a1, a2, a3 = st.columns(3)
                    with a1:
                        if st.checkbox("🔊 Hear translation", value=True):
                            show_tts_player(result, tgt_code if tgt_code != "auto" else "en")
                    with a2:
                        if st.checkbox("🔤 Romanize"):
                            roman = get_romanization(result, tgt_code)
                            st.info(roman or "Not available for this script.")
                    with a3:
                        st.download_button("⬇️ Export", data=f"[Original]\n{text_input}\n\n[{tgt_lang}]\n{result}",
                                           file_name="translation.txt", mime="text/plain")
                except Exception as e:
                    st.error(f"Error: {e}")


# ════════════════════════════════════════════════
#  PDF TOOLS MODULE
# ════════════════════════════════════════════════
elif module == "📄 PDF Tools":
    st.markdown('<div class="section-title">PDF Tools</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Merge, split, rotate, compress, watermark, protect, and extract from PDFs.</div>', unsafe_allow_html=True)

    pdf_tool = st.selectbox("Choose a PDF operation:", [
        "Merge PDFs", "Split PDF", "Rotate Pages", "Compress PDF",
        "Add Watermark", "Protect (Add Password)", "Unlock (Remove Password)",
        "Extract Text", "Extract Images", "PDF → Images", "Images → PDF",
    ])
    st.markdown("---")

    # ── Merge ──
    if pdf_tool == "Merge PDFs":
        files = st.file_uploader("Upload 2+ PDFs to merge (in order)", type=["pdf"], accept_multiple_files=True)
        if files and len(files) >= 2:
            st.caption(f"{len(files)} files selected, total {sum(pdf_get_page_count(f.getvalue()) for f in files)} pages")
            if st.button("🔀 Merge PDFs"):
                with st.spinner("Merging…"):
                    result = pdf_merge([f.getvalue() for f in files])
                st.success(f"Merged into {pdf_get_page_count(result)} pages.")
                st.download_button("⬇️ Download Merged PDF", data=result, file_name="merged.pdf", mime="application/pdf")
        elif files:
            st.warning("Upload at least 2 PDFs to merge.")

    # ── Split ──
    elif pdf_tool == "Split PDF":
        file = st.file_uploader("Upload a PDF to split", type=["pdf"])
        if file:
            fb = file.getvalue()
            n = pdf_get_page_count(fb)
            st.caption(f"{n} pages detected")
            split_mode = st.radio("Split mode:", ["Every page separately", "Custom page range"])
            if split_mode == "Every page separately":
                if st.button("✂️ Split"):
                    with st.spinner("Splitting…"):
                        parts = pdf_split(fb)
                    st.success(f"Split into {len(parts)} files.")
                    import zipfile
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as zf:
                        for name, data in parts:
                            zf.writestr(name, data)
                    st.download_button("⬇️ Download All (ZIP)", data=zip_buf.getvalue(), file_name="split_pages.zip", mime="application/zip")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    start = st.number_input("Start page", min_value=1, max_value=n, value=1)
                with c2:
                    end = st.number_input("End page", min_value=1, max_value=n, value=n)
                if st.button("✂️ Extract Range"):
                    result = pdf_split_range(fb, int(start), int(end))
                    st.success(f"Extracted pages {start}-{end}.")
                    st.download_button("⬇️ Download", data=result, file_name=f"pages_{start}-{end}.pdf", mime="application/pdf")

    # ── Rotate ──
    elif pdf_tool == "Rotate Pages":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            degrees = st.select_slider("Rotation angle", options=[90, 180, 270], value=90)
            if st.button("🔄 Rotate All Pages"):
                result = pdf_rotate(fb, degrees)
                st.success("Rotated.")
                st.download_button("⬇️ Download Rotated PDF", data=result, file_name="rotated.pdf", mime="application/pdf")

    # ── Compress ──
    elif pdf_tool == "Compress PDF":
        file = st.file_uploader("Upload a PDF to compress", type=["pdf"])
        if file:
            fb = file.getvalue()
            quality = st.slider("Image quality (lower = smaller file)", 10, 95, 60)
            if st.button("🗜️ Compress"):
                with st.spinner("Compressing…"):
                    result = pdf_compress_simple(fb)
                orig_kb, new_kb = len(fb)/1024, len(result)/1024
                pct = round((1 - len(result)/len(fb)) * 100) if len(fb) else 0
                c1, c2, c3 = st.columns(3)
                c1.metric("Original", f"{orig_kb:.0f} KB")
                c2.metric("Compressed", f"{new_kb:.0f} KB")
                c3.metric("Saved", f"{pct}%")
                st.download_button("⬇️ Download Compressed PDF", data=result, file_name="compressed.pdf", mime="application/pdf")

    # ── Watermark ──
    elif pdf_tool == "Add Watermark":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            wm_text = st.text_input("Watermark text", value="CONFIDENTIAL")
            opacity = st.slider("Opacity", 0.1, 1.0, 0.3)
            if st.button("💧 Add Watermark"):
                result = pdf_add_watermark(fb, wm_text, opacity)
                st.success("Watermark added.")
                st.download_button("⬇️ Download Watermarked PDF", data=result, file_name="watermarked.pdf", mime="application/pdf")

    # ── Protect ──
    elif pdf_tool == "Protect (Add Password)":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            pwd = st.text_input("Set a password", type="password")
            if st.button("🔒 Protect PDF"):
                if not pwd:
                    st.warning("Enter a password first.")
                else:
                    result = pdf_protect(fb, pwd)
                    st.success("PDF is now password-protected.")
                    st.download_button("⬇️ Download Protected PDF", data=result, file_name="protected.pdf", mime="application/pdf")

    # ── Unlock ──
    elif pdf_tool == "Unlock (Remove Password)":
        file = st.file_uploader("Upload a password-protected PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            pwd = st.text_input("Enter the current password", type="password")
            if st.button("🔓 Unlock PDF"):
                try:
                    result = pdf_unlock(fb, pwd)
                    st.success("Password removed.")
                    st.download_button("⬇️ Download Unlocked PDF", data=result, file_name="unlocked.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Could not unlock — check the password. ({e})")

    # ── Extract Text ──
    elif pdf_tool == "Extract Text":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            if st.button("📋 Extract Text"):
                text = pdf_extract_text(fb)
                st.markdown('<div class="card"><div class="card-label">Extracted Text</div></div>', unsafe_allow_html=True)
                st.text_area("Extracted text", text, height=300, label_visibility="collapsed")
                st.download_button("⬇️ Download as .txt", data=text, file_name="extracted_text.txt", mime="text/plain")

    # ── Extract Images ──
    elif pdf_tool == "Extract Images":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            if st.button("🖼️ Extract Images"):
                with st.spinner("Extracting…"):
                    imgs = pdf_extract_images(fb)
                if not imgs:
                    st.info("No embedded images found in this PDF.")
                else:
                    st.success(f"Found {len(imgs)} image(s).")
                    cols = st.columns(4)
                    for i, (name, data) in enumerate(imgs):
                        cols[i % 4].image(data, caption=name, use_container_width=True)
                    import zipfile
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w") as zf:
                        for name, data in imgs:
                            zf.writestr(name, data)
                    st.download_button("⬇️ Download All (ZIP)", data=zip_buf.getvalue(), file_name="extracted_images.zip", mime="application/zip")

    # ── PDF to Images ──
    elif pdf_tool == "PDF → Images":
        file = st.file_uploader("Upload a PDF", type=["pdf"])
        if file:
            fb = file.getvalue()
            dpi = st.select_slider("Resolution (DPI)", options=[72, 100, 150, 200, 300], value=150)
            if st.button("🖼️ Convert to Images"):
                with st.spinner("Rendering pages…"):
                    imgs = pdf_to_images(fb, dpi=dpi)
                st.success(f"Converted {len(imgs)} page(s).")
                cols = st.columns(3)
                for i, (name, data) in enumerate(imgs):
                    cols[i % 3].image(data, caption=name, use_container_width=True)
                import zipfile
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    for name, data in imgs:
                        zf.writestr(name, data)
                st.download_button("⬇️ Download All (ZIP)", data=zip_buf.getvalue(), file_name="pdf_pages.zip", mime="application/zip")

    # ── Images to PDF ──
    elif pdf_tool == "Images → PDF":
        files = st.file_uploader("Upload images (in order)", type=["jpg", "jpeg", "png", "bmp", "webp"], accept_multiple_files=True)
        if files:
            st.caption(f"{len(files)} image(s) selected")
            cols = st.columns(5)
            for i, f in enumerate(files):
                cols[i % 5].image(f.getvalue(), use_container_width=True)
            if st.button("📄 Combine into PDF"):
                result = images_to_pdf([f.getvalue() for f in files])
                st.success(f"Created a {pdf_get_page_count(result)}-page PDF.")
                st.download_button("⬇️ Download PDF", data=result, file_name="combined.pdf", mime="application/pdf")


# ════════════════════════════════════════════════
#  WORD ⇄ PDF MODULE
# ════════════════════════════════════════════════
elif module == "🔁 Word ⇄ PDF":
    st.markdown('<div class="section-title">Word ⇄ PDF Converter</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Convert between Word documents and PDFs, or build new files from plain text.</div>', unsafe_allow_html=True)

    conv_tool = st.selectbox("Choose a conversion:", [
        "Word (.docx) → PDF", "PDF → Word (.docx)", "Plain Text → PDF", "Plain Text → Word (.docx)",
    ])
    st.markdown("---")

    if conv_tool == "Word (.docx) → PDF":
        file = st.file_uploader("Upload a .docx file", type=["docx"])
        if file:
            fb = file.getvalue()
            if st.button("📄 Convert to PDF"):
                with st.spinner("Converting…"):
                    try:
                        result = word_to_pdf(fb)
                        st.success(f"Converted to a {pdf_get_page_count(result)}-page PDF.")
                        st.download_button("⬇️ Download PDF", data=result, file_name=f"{Path(file.name).stem}.pdf", mime="application/pdf")
                    except Exception as e:
                        st.error(f"Conversion failed: {e}")

    elif conv_tool == "PDF → Word (.docx)":
        file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if file:
            fb = file.getvalue()
            st.caption(f"{pdf_get_page_count(fb)} page(s) detected")
            if st.button("📝 Convert to Word"):
                with st.spinner("Converting (preserving layout)…"):
                    try:
                        result = pdf_to_word(fb)
                        st.success("Converted to Word document.")
                        st.download_button("⬇️ Download .docx", data=result, file_name=f"{Path(file.name).stem}.docx",
                                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    except Exception as e:
                        st.error(f"Conversion failed: {e}")

    elif conv_tool == "Plain Text → PDF":
        title = st.text_input("Document title (optional)", value="")
        text = st.text_area("Paste your text:", height=250)
        if st.button("📄 Create PDF"):
            if not text.strip():
                st.warning("Enter some text first.")
            else:
                result = text_to_pdf(text, title=title)
                st.success("PDF created.")
                st.download_button("⬇️ Download PDF", data=result, file_name="document.pdf", mime="application/pdf")

    elif conv_tool == "Plain Text → Word (.docx)":
        title = st.text_input("Document title (optional)", value="")
        text = st.text_area("Paste your text:", height=250)
        if st.button("📝 Create Word Doc"):
            if not text.strip():
                st.warning("Enter some text first.")
            else:
                result = text_to_docx(text, title=title)
                st.success("Word document created.")
                st.download_button("⬇️ Download .docx", data=result, file_name="document.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ════════════════════════════════════════════════
#  IMAGE ⇄ TEXT MODULE
# ════════════════════════════════════════════════
elif module == "🖼️ Image ⇄ Text":
    st.markdown('<div class="section-title">Image ⇄ Text</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Extract text from images with OCR, or render text onto a styled image canvas.</div>', unsafe_allow_html=True)

    direction = st.radio("Direction", ["🖼️ → 📝  Image to Text (OCR)", "📝 → 🖼️  Text to Image"], horizontal=True)
    st.markdown("---")

    if "Image to Text" in direction:
        img_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp", "webp"])
        if img_file:
            st.image(img_file.getvalue(), caption="Uploaded image", use_container_width=False, width=400)
            ocr_lang = st.selectbox("Text language in image", ["English (best support)", "Auto / Other (uses online OCR)"])
            if st.button("🔍 Extract Text"):
                with st.spinner("Running OCR…"):
                    img = Image.open(io.BytesIO(img_file.getvalue()))
                    if ocr_lang.startswith("English"):
                        extracted = pytesseract.image_to_string(img).strip()
                    else:
                        # Fallback to online OCR for non-English / better accuracy
                        b64_img = base64.b64encode(img_file.getvalue()).decode()
                        try:
                            resp = requests.post("https://api.ocr.space/parse/image",
                                data={"base64Image": f"data:image/png;base64,{b64_img}", "OCREngine": 2},
                                headers={"apikey": "helloworld"}, timeout=20)
                            parsed = resp.json().get("ParsedResults", [])
                            extracted = parsed[0].get("ParsedText", "").strip() if parsed else ""
                        except Exception:
                            extracted = pytesseract.image_to_string(img).strip()

                if extracted:
                    st.session_state.ocr_text = extracted
                    st.markdown('<div class="card card-accent"><div class="card-label">Extracted Text</div></div>', unsafe_allow_html=True)
                    st.text_area("OCR result", extracted, height=180, label_visibility="collapsed")
                    st.download_button("⬇️ Download as .txt", data=extracted, file_name="extracted.txt", mime="text/plain")
                else:
                    st.warning("No text detected. Try a clearer image.")

    else:  # Text to Image
        text = st.text_area("Enter text to render as an image:", height=120, placeholder="Your text here…")
        c1, c2, c3 = st.columns(3)
        with c1:
            width = st.number_input("Width (px)", 300, 2000, 800)
        with c2:
            height = st.number_input("Height (px)", 200, 2000, 400)
        with c3:
            font_size = st.slider("Font size", 16, 72, 32)
        c4, c5 = st.columns(2)
        with c4:
            bg_color = st.color_picker("Background color", "#0f1420")
        with c5:
            text_color = st.color_picker("Text color", "#e2e8f8")
        if st.button("🎨 Generate Image"):
            if not text.strip():
                st.warning("Enter some text first.")
            else:
                result = text_to_image(text, width, height, bg_color, text_color, font_size)
                st.image(result, caption="Generated image")
                st.download_button("⬇️ Download PNG", data=result, file_name="text_image.png", mime="image/png")

# ════════════════════════════════════════════════
#  IMAGE TOOLS MODULE
# ════════════════════════════════════════════════
elif module == "🎨 Image Tools":
    st.markdown('<div class="section-title">Image Tools</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Convert, compress, resize, rotate, watermark, filter, or generate QR codes.</div>', unsafe_allow_html=True)

    img_tool = st.selectbox("Choose an image operation:", [
        "Convert Format", "Compress", "Resize", "Rotate / Flip",
        "Add Text Watermark", "Grayscale", "Apply Filter", "Generate QR Code",
    ])
    st.markdown("---")

    if img_tool == "Generate QR Code":
        data = st.text_input("Text or URL to encode:", placeholder="https://example.com")
        c1, c2 = st.columns(2)
        with c1:
            fill = st.color_picker("Foreground", "#000000")
        with c2:
            back = st.color_picker("Background", "#ffffff")
        if st.button("🔲 Generate QR Code"):
            if not data.strip():
                st.warning("Enter some text or a URL.")
            else:
                result = generate_qr_code(data, fill_color=fill, back_color=back)
                st.image(result, caption="QR Code", width=250)
                st.download_button("⬇️ Download PNG", data=result, file_name="qrcode.png", mime="image/png")
    else:
        img_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "bmp", "webp"])
        if img_file:
            fb = img_file.getvalue()
            st.image(fb, caption="Original", width=300)

            if img_tool == "Convert Format":
                target = st.selectbox("Convert to:", ["PNG", "JPEG", "WEBP", "BMP"])
                quality = st.slider("Quality (JPEG/WEBP)", 10, 100, 90) if target in ("JPEG", "WEBP") else 100
                if st.button("🔄 Convert"):
                    result = image_convert_format(fb, target, quality)
                    st.success(f"Converted to {target}.")
                    st.download_button(f"⬇️ Download .{target.lower()}", data=result,
                                       file_name=f"converted.{target.lower()}", mime=f"image/{target.lower()}")

            elif img_tool == "Compress":
                quality = st.slider("Quality", 10, 95, 60)
                max_dim = st.checkbox("Also limit max dimension")
                max_d = st.number_input("Max width/height (px)", 100, 4000, 1200) if max_dim else None
                if st.button("🗜️ Compress"):
                    result = image_compress(fb, quality, max_d)
                    pct = round((1 - len(result)/len(fb)) * 100)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Original", f"{len(fb)/1024:.0f} KB")
                    c2.metric("Compressed", f"{len(result)/1024:.0f} KB")
                    c3.metric("Saved", f"{pct}%")
                    st.download_button("⬇️ Download Compressed", data=result, file_name="compressed.jpg", mime="image/jpeg")

            elif img_tool == "Resize":
                orig_img = Image.open(io.BytesIO(fb))
                st.caption(f"Original: {orig_img.width} × {orig_img.height}px")
                c1, c2 = st.columns(2)
                with c1:
                    w = st.number_input("Width", 10, 5000, orig_img.width)
                with c2:
                    h = st.number_input("Height", 10, 5000, orig_img.height)
                keep_aspect = st.checkbox("Keep aspect ratio", value=True)
                if st.button("📐 Resize"):
                    result = image_resize(fb, int(w), int(h), keep_aspect)
                    new_img = Image.open(io.BytesIO(result))
                    st.success(f"Resized to {new_img.width} × {new_img.height}px.")
                    st.image(result, caption="Resized", width=300)
                    st.download_button("⬇️ Download", data=result, file_name="resized.png", mime="image/png")

            elif img_tool == "Rotate / Flip":
                rotate_deg = st.select_slider("Rotate", options=[0, 90, 180, 270], value=0)
                c1, c2 = st.columns(2)
                with c1:
                    flip_h = st.checkbox("Flip horizontal")
                with c2:
                    flip_v = st.checkbox("Flip vertical")
                if st.button("🔄 Apply"):
                    result = image_rotate_flip(fb, rotate_deg, flip_h, flip_v)
                    st.image(result, caption="Result", width=300)
                    st.download_button("⬇️ Download", data=result, file_name="rotated.png", mime="image/png")

            elif img_tool == "Add Text Watermark":
                wm_text = st.text_input("Watermark text", value="SAMPLE")
                position = st.selectbox("Position", ["center", "bottom-right", "top-left"])
                opacity = st.slider("Opacity", 0, 255, 150)
                if st.button("💧 Add Watermark"):
                    result = image_add_watermark_text(fb, wm_text, opacity, position)
                    st.image(result, caption="Watermarked", width=300)
                    st.download_button("⬇️ Download", data=result, file_name="watermarked.png", mime="image/png")

            elif img_tool == "Grayscale":
                if st.button("⚫ Convert to Grayscale"):
                    result = image_to_grayscale(fb)
                    st.image(result, caption="Grayscale", width=300)
                    st.download_button("⬇️ Download", data=result, file_name="grayscale.png", mime="image/png")

            elif img_tool == "Apply Filter":
                filter_name = st.selectbox("Filter", ["Blur", "Sharpen", "Edge Enhance", "Contour", "Emboss", "Smooth"])
                if st.button("✨ Apply Filter"):
                    result = image_apply_filter(fb, filter_name)
                    st.image(result, caption=f"{filter_name} applied", width=300)
                    st.download_button("⬇️ Download", data=result, file_name="filtered.png", mime="image/png")

# ════════════════════════════════════════════════
#  TEXT ⇄ SPEECH MODULE
# ════════════════════════════════════════════════
elif module == "🔊 Text ⇄ Speech":
    st.markdown('<div class="section-title">Text ⇄ Speech</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Convert text into natural-sounding speech audio in dozens of languages.</div>', unsafe_allow_html=True)

    tts_text = st.text_area("Enter text to speak:", height=150, placeholder="Type something to hear it spoken aloud…")
    tts_lang_name = st.selectbox("Language / accent:", list(lang_map.keys()), index=0)

    if st.button("🔊 Generate Speech"):
        if not tts_text.strip():
            st.warning("Enter some text first.")
        else:
            with st.spinner("Generating audio…"):
                tts_code = lang_map[tts_lang_name]
                b64 = get_tts_audio_b64(tts_text, tts_code)
            if b64:
                st.markdown('<div class="card card-accent"><div class="card-label">Generated Audio</div></div>', unsafe_allow_html=True)
                st.markdown(f'<audio controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
                audio_bytes = base64.b64decode(b64)
                st.download_button("⬇️ Download MP3", data=audio_bytes, file_name="speech.mp3", mime="audio/mp3")
            else:
                st.error("Could not generate audio for this language.")

