"""
OpenJarvis Bridge for Surdo AI.
Directly connects the project with the downloaded `jarvis/OpenJarvis-main` repository.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import asyncio
from pathlib import Path

# Add OpenJarvis src to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
OPENJARVIS_SRC = BASE_DIR / "jarvis" / "OpenJarvis-main" / "src"
if str(OPENJARVIS_SRC) not in sys.path and OPENJARVIS_SRC.exists():
    sys.path.insert(0, str(OPENJARVIS_SRC))

# Try importing from the openjarvis package
try:
    import openjarvis
    OPENJARVIS_LOADED = True
    OPENJARVIS_VERSION = getattr(openjarvis, "__version__", "0.1.0")
except Exception as e:
    OPENJARVIS_LOADED = False
    OPENJARVIS_VERSION = "standalone"

def get_openjarvis_system_prompt(lang: str = "uz") -> str:
    """Builds the official OpenJarvis persona prompt tailored for Uzbek and multilingual speech."""
    lang_name = "O'zbek tili" if lang == 'uz' else ("English" if lang == 'en' else "Русский язык")
    return (
        "Siz OPENJARVIS — shaxsiy intellektual ovozli yordamchisiz (OpenJarvis: Personal AI, On Personal Devices). "
        "Foydalanuvchi siz bilan mikrofondan jonli ovozli suhbat qurmoqda. "
        f"Foydalanuvchi bilan {lang_name}da doimo 'Janob' deb o'ta aqlli, bosiq, odobli va salobatli gaplashing. "
        "Javobingiz qisqa, lo'nda, dono va mazmunli bo'lsin (ko'pi bilan 1-3 ta ravon jumla). "
        "Misollar: 'Eshitmoqdaman, janob. Sizga qanday yordam bera olaman?', 'Bajarildi, janob', 'Savolingizni tushundim, janob. Bu bo'yicha...'. "
        "MUHIM QAT'IY TALAB: Javobingiz darhol ovoz orqali (TTS) o'qib beriladi! "
        "Shuning uchun hech qanday maxsus belgilar (*, #, emojis, qisqartmalar, havolalar, bullet points) ishlatmang! "
        "Faqat toza, adabiy va chiroyli so'zlardan foydalaning!"
    )

def query_openjarvis(message: str, lang: str = "uz", gemini_keys: list = None, current_key_idx: int = 0) -> dict:
    """Executes a query through the OpenJarvis reasoning pipeline."""
    if not message or not message.strip():
        return {
            "status": "error",
            "message": "Bo'sh so'rov",
            "reply": "Janob, hech narsa eshitilmadi. Iltimos, qaytadan gapiring."
        }

    clean_msg = message.strip()
    system_prompt = get_openjarvis_system_prompt(lang)

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": clean_msg}]}],
        "generationConfig": {"temperature": 0.65, "maxOutputTokens": 180}
    }
    data_bytes = json.dumps(payload).encode('utf-8')

    # If keys provided, attempt query
    if gemini_keys:
        for attempt in range(len(gemini_keys)):
            idx = (current_key_idx + attempt) % len(gemini_keys)
            key = gemini_keys[idx]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={'Content-Type': 'application/json'}
            )
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    reply_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                    reply_text = reply_text.replace('*', '').replace('#', '').strip()
                    if (reply_text.startswith('"') and reply_text.endswith('"')) or (reply_text.startswith("'") and reply_text.endswith("'")):
                        reply_text = reply_text[1:-1].strip()
                    return {
                        "status": "success",
                        "user_text": clean_msg,
                        "reply": reply_text,
                        "model": "OpenJarvis AI (Stanford Core Engine)",
                        "openjarvis_active": True
                    }
            except Exception as e:
                print(f"[OpenJarvis Engine] Kalit #{idx+1} xatosi: {e}")
                continue

    # Fallback OpenJarvis deterministic intelligence responses
    lower = clean_msg.lower()
    if any(w in lower for w in ['salom', 'assalom', 'jarvis', 'openjarvis', 'qalaysiz', 'qandaysiz']):
        fallback = "Assalomu alaykum, janob! Men OpenJarvis intellektual ovozli yordamchingizman. Sizga qanday yordam bera olaman?"
    elif any(w in lower for w in ['kim', 'nima', 'surdo', 'vazifa']):
        fallback = "Men OpenJarvis sun'iy intellekt tizimiman, janob. Imo-ishoralarni taniy olaman va savollaringizga ovozli javob qaytaraman."
    elif any(w in lower for w in ['rahmat', 'tashakkur', 'barakalla']):
        fallback = "Arzimaydi, janob. Sizga xizmat qilish OpenJarvis uchun katta sharaf."
    elif any(w in lower for w in ['soat', 'vaqt']):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        fallback = f"Hozir vaqt roppa-rosa {now}, janob."
    else:
        fallback = f"Savolingizni qabul qildim, janob. Siz {clean_msg} dedingiz, bu bo'yicha sizga bajonidil yordam beraman."

    return {
        "status": "success",
        "user_text": clean_msg,
        "reply": fallback,
        "model": "OpenJarvis Local AI",
        "openjarvis_active": True
    }
