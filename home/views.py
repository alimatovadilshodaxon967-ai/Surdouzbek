from django.shortcuts import render
from django.views import View
import cv2
import numpy as np
import os
import base64
import json
import urllib.request
import urllib.error
import asyncio
import mediapipe as mp
try:
    from keras.models import Sequential
    from keras.layers import LSTM, Dense
    from keras.callbacks import TensorBoard
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse


# Create your views here.

class HomaPageView(View):
    def get(self, request):
        context = {}
        return render(request, "index.html", context)

    
def webcam():
    mp_holistic = mp.solutions.holistic 
    mp_drawing = mp.solutions.drawing_utils 

    def mediapipe_detection(image, model):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
        image.flags.writeable = False                  
        results = model.process(image)                 
        image.flags.writeable = True                  
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 
        return image, results

    def draw_landmarks(image, results):
        mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION) 
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS) 
        mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS) 
        mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS) 

    def draw_styled_landmarks(image, results):
        # Draw face connections
        mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION, 
                                mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1), 
                                mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1)
                                ) 
        # Draw pose connections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4), 
                                mp_drawing.DrawingSpec(color=(80,44,121), thickness=2, circle_radius=2)
                                ) 
        # Draw left hand connections
        mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                                mp_drawing.DrawingSpec(color=(121,22,76), thickness=2, circle_radius=4), 
                                mp_drawing.DrawingSpec(color=(121,44,250), thickness=2, circle_radius=2)
                                ) 
        # Draw right hand connections  
        mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                ) 

    actions = np.array(['hello', 'thanks', 'iloveyou'])
    model = None

    if HAS_KERAS and os.path.exists('action.h5'):
        try:
            model = Sequential()
            model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30,1662)))
            model.add(LSTM(128, return_sequences=True, activation='relu'))
            model.add(LSTM(64, return_sequences=False, activation='relu'))
            model.add(Dense(64, activation='relu'))
            model.add(Dense(32, activation='relu'))
            model.add(Dense(actions.shape[0], activation='softmax'))
            model.load_weights('action.h5')
        except Exception as e:
            print("Model load error:", e)
            model = None

    colors = [(245,117,16), (117,245,16), (16,117,245)]
    def prob_viz(res, actions, input_frame, colors):
        output_frame = input_frame.copy()
        for num, prob in enumerate(res):
            cv2.rectangle(output_frame, (0,60+num*40), (int(prob*100), 90+num*40), colors[num], -1)
            cv2.putText(output_frame, actions[num], (0, 85+num*40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
            
        return output_frame

    def extract_keypoints(results):
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
        face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468*3)
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)
        return np.concatenate([pose, face, lh, rh])

    # 1. New detection variables
    sequence = []
    sentence = []
    threshold = 0.8

    cap = cv2.VideoCapture(0)
    try:
        with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(blank_frame, "Kamera ulanmadi yoki band", (100, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                    _, buffer = cv2.imencode('.jpg', blank_frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')
                    continue

                # Make detections
                image, results = mediapipe_detection(frame, holistic)

                # Draw landmarks
                draw_styled_landmarks(image, results)

                # 2. Prediction logic
                if model is not None:
                    keypoints = extract_keypoints(results)
                    sequence.append(keypoints)
                    sequence = sequence[-30:]

                    if len(sequence) == 30:
                        res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]

                        # 3. Viz logic
                        if res[np.argmax(res)] > threshold:
                            if len(sentence) > 0:
                                if actions[np.argmax(res)] != sentence[-1]:
                                    sentence.append(actions[np.argmax(res)])
                            else:
                                sentence.append(actions[np.argmax(res)])

                        if len(sentence) > 5:
                            sentence = sentence[-5:]

                        image = prob_viz(res, actions, image, colors)

                    cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
                    cv2.putText(image, ' '.join(sentence), (3, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                else:
                    cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
                    cv2.putText(image, "Surdo AI - Imo-ishoralar aniqlanmoqda", (10, 28),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                _, buffer = cv2.imencode('.jpg', image)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    finally:
        cap.release()

import asyncio
from asgiref.sync import sync_to_async

async def async_webcam():
    gen = webcam()
    get_next = sync_to_async(lambda: next(gen, None), thread_sensitive=False)
    while True:
        try:
            frame = await get_next()
            if frame is None:
                break
            yield frame
            await asyncio.sleep(0.01)
        except Exception as e:
            print("Streaming error:", e)
            break

class VideoPageView(View):
    async def get(self, request):
        return StreamingHttpResponse(async_webcam(), content_type='multipart/x-mixed-replace; boundary=frame')
          
class CameraPageView(View):
    def get(self, request):
        return render(request, "camera.html", {})
    
class VoicePageView(View):
    def get(self, request):
        context = {}
        return render(request, "voice.html", context)

VOICE_AUDIO_CACHE = {}

VOICELAB_API_KEYS = [
    "vlk_jymjsVHzrXt8jTp1WtrtvH3ps1ICwZ81lLUIH81Eboc",   # 1-Yangi kalit (Faol)
    "vlk_YVdii2PwwrYLGDS1bXJ4xbdEG0Qs6RnaIZZcJVIRbMg",   # 2-Zaxira kalit (Faol)
    "vlk_qQ4O4WlnQ-cPw23_PiBkZ8NK1Tj8Ywmu-GeltcH6VqQ",   # 3-Zaxira kalit (Faol)
    "vlk_WkCzoxnsKdJ3ffT3Gt-abjO9YNeyLtGY1TZlCS1VhYg",   # 4-Zaxira kalit (Faol)
    "vlk_sS-lIYDMWPqIaO8_iegg9D1n9SePqvNy0q6vthHk4YM",   # 5-Zaxira kalit (Faol)
    "vlk_Syrv5hJm2hEgsUxLNQ3cKhhmxClgFMICUduHf0EZgcc",   # 6-Zaxira kalit (Faol)
    "vlk_-Xishu-yP9pksI8QS_EXV8G6vJNu7VTI3Jr9NGy1s6k",   # 7-Zaxira kalit (Faol)
    "vlk_Vb_xPvvMYRgNW8T0r08jL1wj_JWyKOjVg5nVv852Ppw",   # 8-Zaxira kalit (Faol)
    "vlk_3JUy_pjdKLCP2gXDgQd-pPfnbbBjbRHpA8qQhRMoL38",   # 9-Zaxira kalit (Faol)
    "vlk_x7y5QaqzTurjgFKNHJ5nFAK9D8One9XaJJV7x9FGdu4",   # 10-Zaxira kalit (Zaxira)
]
def get_current_voicelab_key():
    global VOICELAB_API_KEYS
    if not VOICELAB_API_KEYS:
        return None
    return VOICELAB_API_KEYS[0]

def remove_and_switch_voicelab_key(failed_key):
    """
    Limiti/krediti tugagan yoki xato bergan VoiceLab kalitini ro'yxatdan BUTUNLAY O'CHIRIB TASHLAYDI
    va navbatdagi faol kalitni qaytaradi.
    """
    global VOICELAB_API_KEYS
    if failed_key in VOICELAB_API_KEYS:
        VOICELAB_API_KEYS.remove(failed_key)
        print(f"[VoiceLab Purge] Limiti/Krediti tugagan kalit ({failed_key[:12]}...) ro'yxatdan BUTUNLAY O'CHIRILDI! Qolgan kalitlar: {len(VOICELAB_API_KEYS)}")
    if VOICELAB_API_KEYS:
        return VOICELAB_API_KEYS[0]
    return None

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def call_groq_api(messages, max_tokens=250, temperature=0.6):
    """Groq Cloud LPU orqali o'ta tezkor (0.3-0.8s) matn va javob generatsiyasi."""
    if not GROQ_API_KEY:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "SurdoAI/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            reply = data['choices'][0]['message']['content'].strip()
            reply = reply.replace('*', '').replace('#', '').strip()
            if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                reply = reply[1:-1].strip()
            return reply
    except Exception as e:
        print(f"[Groq Cloud API] Xatolik yoki limit: {e}. Zaxira Gemini tizimiga o'tilmoqda...")
        return None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

OPENROUTER_MODELS = [
    "recursive/flint-v1.0:free",
    "liquid/lfm-2.5-2.6b:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free"
]

def call_openrouter_api(messages, max_tokens=250, temperature=0.6):
    """OpenRouter orqali zaxira multi-AI modellariga ulanish."""
    if not OPENROUTER_API_KEY:
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    for m in OPENROUTER_MODELS:
        payload = {
            "model": m,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:8000",
                "X-Title": "Surdo AI",
                "User-Agent": "SurdoAI/1.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=4.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                choice = data['choices'][0]
                msg = choice['message']
                reply = msg.get('content') or msg.get('reasoning') or ''
                reply = reply.strip()
                if reply:
                    reply = reply.replace('*', '').replace('#', '').strip()
                    if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                        reply = reply[1:-1].strip()
                    return reply
        except Exception as e:
            print(f"[OpenRouter API] Model {m} xatolik: {e}. Keyingi zaxiraga o'tilmoqda...")
            continue
    return None

def call_ollama_api(messages, model="qwen2.5:1.5b", max_tokens=200):
    """Lokal kompyuterdagi Ollama orqali 100% oflayn (internetsiz) generatsiya."""
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.6
        }
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            reply = data.get('message', {}).get('content', '').strip()
            reply = reply.replace('*', '').replace('#', '').strip()
            if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
                reply = reply[1:-1].strip()
            return reply
    except Exception:
        return None

GEMINI_API_KEYS = [
    # 1-Asosiy kalit (Faol va yangi kvotali)
    os.getenv("GEMINI_API_KEY", base64.b64decode("QVEuQWI4Uk42S0xvOGQ0Qmw3MlpRZl9TNkFya3VDTHdMaUc4RVZEVkxwVnVXdUU1MEh3bGc=").decode("utf-8")),
    # 2-Zaxira kalit
    os.getenv("GEMINI_BACKUP_KEY", base64.b64decode("QVEuQWI4Uk42TEhER05tQU9BdzNBck16cjJhcGFxcHV4Y0Nqc1JYUXRuUmxPc2FwdjJld3c=").decode("utf-8")),
    # 3-Zaxira kalit
    os.getenv("GEMINI_BACKUP_KEY_2", base64.b64decode("QVEuQWI4Uk42SUI2M2xPM3NwaG1wZHYwTmhZMUgyT0JMc0FxanpvYUE1WFF0OGxFc2lTR1E=").decode("utf-8")),
    # 4-Zaxira kalit
    os.getenv("GEMINI_BACKUP_KEY_3", base64.b64decode("QVEuQWI4Uk42SUFpS1JBdmp2WklfQV85R3Z5WjRab09JOTM1S01VcjZVX01uLXhPLVZoTnc=").decode("utf-8")),
    # 5-Zaxira kalit (Yangi qo'shilgan)
    os.getenv("GEMINI_BACKUP_KEY_4", base64.b64decode("QVEuQWI4Uk42S1N1cGFRaVIyOGN4QlZwQ3lpZzFWNG5IOU9LdDlQd3lVUnJkRmdHaHViVHc=").decode("utf-8")),
    # 6-Zaxira kalit (Yangi qo'shilgan)
    os.getenv("GEMINI_BACKUP_KEY_5", base64.b64decode("QVEuQWI4Uk42S2Z0aFpCcjRuWnlkWDN6ZDdvSnU0SV9UMnlhMjFVREFqZXFjelpCQjl1b3c=").decode("utf-8")),
]
def get_current_gemini_key():
    global GEMINI_API_KEYS
    if not GEMINI_API_KEYS:
        return None
    return GEMINI_API_KEYS[0]

def is_gemini_quota_exhausted(http_err):
    """
    Kalitning so'rov limiti/kvotasi to'liq tugaganda (HTTP 429 yoki RESOURCE_EXHAUSTED/QUOTA_EXCEEDED) True qaytaradi.
    """
    if isinstance(http_err, urllib.error.HTTPError):
        if http_err.code in (429, 403, 400):
            return True
        try:
            body = http_err.read().decode('utf-8', errors='ignore')
            if any(term in body for term in ['RESOURCE_EXHAUSTED', 'QUOTA_EXCEEDED', 'rate limit', '429', 'API_KEY_INVALID']):
                return True
        except Exception:
            pass
    return False

def remove_and_switch_gemini_key(failed_key):
    """
    Kvotasi to'liq tugagan Gemini kalitini ro'yxatdan BUTUNLAY O'CHIRIB TASHLAYDI
    va navbatdagi faol zaxira kalitni qaytaradi.
    """
    global GEMINI_API_KEYS
    if failed_key in GEMINI_API_KEYS:
        GEMINI_API_KEYS.remove(failed_key)
        print(f"[Gemini Purge] Kvotasi tugagan kalit ({failed_key[:12]}...) ro'yxatdan BUTUNLAY O'CHIRILDI! Qolgan zaxira kalitlar: {len(GEMINI_API_KEYS)}")
    if GEMINI_API_KEYS:
        return GEMINI_API_KEYS[0]
    return None

VOICELAB_VOICES = {
    "abdulhay": "voice_M-p5iz9z_kPWNm_C0cFqbC6X",             # Abdulhay Otaxo'jayev (Dublyaj)
    "madina": "voice_4ef06e6b-2229-4023-ad66-c2a7a2b736ff",   # Madina — Honey (Shirali ayol)
    "amir": "voice_8bae02c6-d078-4757-9d62-0fce6da23cf7",     # Amir — Storyteller (Shirali erkak)
    "javohir": "voice_fa56cecf-9b0b-45ba-9ec3-494efb5b301f",  # Javohir — Presenter (Ta'limiy diktor)
    "kamola": "voice_47260d60-5635-4fb0-904d-0f3c19c04ce6",   # Kamola — Silk (Mayin qiz)
    "dilnoza": "voice_f7179d1c-07ab-4b3d-b5be-84dcf2935388",  # Dilnoza — Velvet (Baxmal)
    "jasur": "voice_ba303813-3023-48aa-a454-4b5705669d35",    # Jasur — Noir (Sokin erkak)
    "safiya": "voice_2785aabd-21b5-4cc7-9845-2230186ef7d9",   # Safiya — Reassuring guide
    "shohruxmirzo": "voice_jABVrmH-0x6pbYefNCuYfH6H",         # Shohruxmirzo (Ta'limiy)
    "nozima": "voice_3602ec76-5393-43b6-9e0d-784328cb77ba",   # Nozima — Soft (Mayin)
    "sardor": "voice_xdQMoRJkjHbPIB-jounXzKq8",               # Sardor
    "botir": "voice_5e592ada-eca8-42e3-98fa-469c1c8fc999",    # Botir — Strimer
    "gulya": "voice_7b350d91-4e56-4bc3-869c-8cd6ba646c3c",    # Gulya — Strimer
    "rustam": "voice_be56058a-8f15-48bb-904b-4fe92531d5b1",   # Rustam — Anime
}

class TTSView(View):
    async def get(self, request):
        import hashlib
        import os
        import json
        import urllib.request
        import asyncio
        import wave
        import io
        from django.conf import settings

        text = request.GET.get('text', '').strip()
        voice = request.GET.get('voice', 'abdulhay').lower()
        lang = request.GET.get('lang', 'uz').lower()
        if not text:
            return HttpResponse(status=400)

        loop = asyncio.get_event_loop()

        # 1. Google Gemini AI Ovoz sintezi (Haqiqiy Google Gemini TTS)
        requested_gemini_cache_key = None
        if 'gemini' in voice or 'google' in voice:
            cache_key = hashlib.md5(f"gemini_{voice}_{text}".encode('utf-8')).hexdigest()
            requested_gemini_cache_key = cache_key
            cache_dir = os.path.join(settings.BASE_DIR, 'static', 'audio_cache')
            os.makedirs(cache_dir, exist_ok=True)
            disk_file = os.path.join(cache_dir, f"{cache_key}.wav")

            if cache_key in VOICE_AUDIO_CACHE:
                return HttpResponse(VOICE_AUDIO_CACHE[cache_key], content_type="audio/wav")

            if os.path.exists(disk_file):
                try:
                    with open(disk_file, 'rb') as f:
                        data = f.read()
                    VOICE_AUDIO_CACHE[cache_key] = data
                    return HttpResponse(data, content_type="audio/wav")
                except Exception:
                    pass

            def try_gemini():
                # Google Gemini TTS ovoz konfiguratsiyasi (Puck / Kore / Aoede)
                vname = "Puck" if ("puck" in voice or "erkak" in voice or "sardor" in voice) else "Aoede"
                payload = {
                    'contents': [{'parts': [{'text': f'Read aloud: {text}'}]}],
                    'generationConfig': {
                        'responseModalities': ['AUDIO'],
                        'speechConfig': {
                            'voiceConfig': {
                                'prebuiltVoiceConfig': {
                                    'voiceName': vname
                                }
                            }
                        }
                    }
                }
                data_bytes = json.dumps(payload).encode('utf-8')
                last_err = None

                # Maksimal 1 ta tezkor urinish (3.0s timeout) - agar kechiksa darhol VoiceLab zaxiraga o'tadi
                for attempt in range(1):
                    key = get_current_gemini_key()
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={key}"
                    req = urllib.request.Request(
                        url,
                        data=data_bytes,
                        headers={'Content-Type': 'application/json'}
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=3.0) as resp:
                            res = json.loads(resp.read().decode('utf-8'))
                            part = res['candidates'][0]['content']['parts'][0]
                            pcm_bytes = base64.b64decode(part['inlineData']['data'])
                            wav_io = io.BytesIO()
                            with wave.open(wav_io, 'wb') as wav_file:
                                wav_file.setnchannels(1)
                                wav_file.setsampwidth(2)
                                wav_file.setframerate(24000)
                                wav_file.writeframes(pcm_bytes)
                            return wav_io.getvalue()
                    except urllib.error.HTTPError as http_err:
                        last_err = http_err
                        if is_gemini_quota_exhausted(http_err):
                            remove_and_switch_gemini_key(key)
                        break
                    except Exception as e:
                        last_err = e
                        break

                if last_err:
                    raise last_err
                return None

            try:
                audio_stream = await loop.run_in_executor(None, try_gemini)
                if audio_stream:
                    VOICE_AUDIO_CACHE[cache_key] = audio_stream
                    try:
                        with open(disk_file, 'wb') as df:
                            df.write(audio_stream)
                    except Exception:
                        pass
                    return HttpResponse(audio_stream, content_type="audio/wav")
            except Exception as gemini_err:
                print(f"[Gemini TTS] Tezkor uzilish ({gemini_err}). O'ta tezkor VoiceLab milliy ovoziga o'tildi!")

        # 2. VoiceLab.uz dagi ovoz ID sini aniqlash
        if voice.startswith("voice_"):
            voicelab_id = voice
        elif voice in VOICELAB_VOICES:
            voicelab_id = VOICELAB_VOICES[voice]
        else:
            # Agar mos kelmasa, moslikni qidiramiz yoki standart Abdulhay qilib olamiz
            matched = None
            for key, vid in VOICELAB_VOICES.items():
                if key in voice:
                    matched = vid
                    break
            voicelab_id = matched or VOICELAB_VOICES["abdulhay"]

        # Kesh tekshirish (Disk va Xotira)
        cache_key = hashlib.md5(f"voicelab_{text}_{voicelab_id}".encode('utf-8')).hexdigest()
        cache_dir = os.path.join(settings.BASE_DIR, 'static', 'audio_cache')
        os.makedirs(cache_dir, exist_ok=True)
        disk_file = os.path.join(cache_dir, f"{cache_key}.wav")

        if cache_key in VOICE_AUDIO_CACHE:
            return HttpResponse(VOICE_AUDIO_CACHE[cache_key], content_type="audio/wav")

        if os.path.exists(disk_file):
            try:
                with open(disk_file, 'rb') as f:
                    data = f.read()
                VOICE_AUDIO_CACHE[cache_key] = data
                return HttpResponse(data, content_type="audio/wav")
            except Exception:
                pass

        # Faqat VoiceLab.uz API orqali ovoz sintezi
        def try_voicelab():
            url = "https://api.voicelab.uz/v1/tts"
            payload = json.dumps({
                "text": text,
                "voice_id": voicelab_id,
                "language": "uz"
            }).encode("utf-8")

            last_err = None

            # Har qanday limit/kredit tugaganda kalit BUTUNLAY RO'YXATDAN O'CHIRILIB, keyingisiga uzilishsiz o'tiladi
            while VOICELAB_API_KEYS:
                api_key = VOICELAB_API_KEYS[0]
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                try:
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        return resp.read()
                except urllib.error.HTTPError as http_err:
                    last_err = http_err
                    if http_err.code in (401, 402, 403, 429):
                        print(f"[VoiceLab API] HTTP {http_err.code} (Kredit yoki limit tugadi) — kalit BUTUNLAY O'CHIRILMOQDA: {api_key[:12]}...")
                    else:
                        print(f"[VoiceLab API] HTTP {http_err.code} xatosi — kalit o'chirilmoqda: {api_key[:12]}...")
                    remove_and_switch_voicelab_key(api_key)
                    continue
                except Exception as e:
                    last_err = e
                    print(f"[VoiceLab API] Aloqa/Timeout xatosi: {e}. Kalit ro'yxatdan o'chirilib zaxiraga o'tilmoqda...")
                    remove_and_switch_voicelab_key(api_key)
                    continue

            if last_err:
                raise last_err
            return None

        try:
            audio_stream = await loop.run_in_executor(None, try_voicelab)
            if audio_stream:
                VOICE_AUDIO_CACHE[cache_key] = audio_stream
                if requested_gemini_cache_key:
                    VOICE_AUDIO_CACHE[requested_gemini_cache_key] = audio_stream
                    gemini_disk_file = os.path.join(cache_dir, f"{requested_gemini_cache_key}.wav")
                    try:
                        with open(gemini_disk_file, 'wb') as gdf:
                            gdf.write(audio_stream)
                    except Exception:
                        pass
                try:
                    with open(disk_file, 'wb') as df:
                        df.write(audio_stream)
                except Exception:
                    pass
                return HttpResponse(audio_stream, content_type="audio/wav")
        except Exception as vl_err:
            print("VoiceLab API xatoligi:", vl_err, "Edge-TTS zaxirasiga o'tilmoqda...")

        # 3. Zaxira: Microsoft Edge TTS (uz-UZ-MadinaNeural / uz-UZ-SardorNeural)
        try:
            import edge_tts
            edge_voice = 'uz-UZ-MadinaNeural'
            if lang == 'ru':
                edge_voice = 'ru-RU-SvetlanaNeural'
            elif lang == 'en':
                edge_voice = 'en-US-JennyNeural'
            elif any(k in voice.lower() for k in ['puck', 'sardor', 'erkak', 'abdulhay']):
                edge_voice = 'uz-UZ-SardorNeural'

            communicate = edge_tts.Communicate(text, edge_voice)
            chunks = []
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    chunks.append(chunk['data'])
            edge_audio = b''.join(chunks)
            if edge_audio:
                VOICE_AUDIO_CACHE[cache_key] = edge_audio
                try:
                    with open(disk_file, 'wb') as df:
                        df.write(edge_audio)
                except Exception:
                    pass
                return HttpResponse(edge_audio, content_type="audio/mpeg")
        except Exception as edge_err:
            print("Edge-TTS zaxira xatosi:", edge_err)

        return HttpResponse("TTS xizmatlarida vaqtincha uzilish", status=503)


class GestureListView(View):
    def get(self, request):
        from .models import SignGesture
        include_daktil = request.GET.get('include_daktil', 'false').lower() == 'true'
        qs = SignGesture.objects.filter(is_active=True)
        if not include_daktil:
            qs = qs.exclude(category='Daktil')
        gestures = list(qs.values(
            'id', 'slug', 'name', 'category', 'hand_type', 'icon', 
            'spoken_text', 'description', 'audio_key', 'finger_pattern'
        ))
        from django.http import JsonResponse
        return JsonResponse({
            'status': 'success',
            'count': len(gestures),
            'gestures': gestures
        }, json_dumps_params={'ensure_ascii': False})


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class GestureMatchView(View):
    def post(self, request):
        from .models import SignGesture
        from django.http import JsonResponse
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        pattern = data.get('finger_pattern', '').strip()
        slug = data.get('slug', '').strip()

        gesture = None
        if slug:
            gesture = SignGesture.objects.filter(slug=slug, is_active=True).exclude(category='Daktil').first()
        elif pattern:
            gesture = SignGesture.objects.filter(finger_pattern=pattern, is_active=True).exclude(category='Daktil').first()

        if gesture:
            return JsonResponse({
                'match': True,
                'gesture': {
                    'id': gesture.id,
                    'slug': gesture.slug,
                    'name': gesture.name,
                    'category': gesture.category,
                    'hand_type': gesture.hand_type,
                    'icon': gesture.icon,
                    'spoken_text': gesture.spoken_text,
                    'description': gesture.description,
                    'audio_key': gesture.audio_key
                }
            }, json_dumps_params={'ensure_ascii': False})

        return JsonResponse({'match': False, 'message': 'Imo-ishora topilmadi'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class AIGrammarView(View):
    async def post(self, request):
        import json
        import urllib.request
        from django.http import JsonResponse
        import asyncio

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        raw_words = body.get('words', [])
        if isinstance(raw_words, str):
            words = [w.strip() for w in raw_words.split(',') if w.strip()]
        else:
            words = [str(w).strip() for w in raw_words if str(w).strip()]

        lang = body.get('lang', 'uz').lower()
        if not words:
            default_empty = {
                'en': "Hello! Please perform some gestures first.",
                'ru': "Здравствуйте! Пожалуйста, покажите жесты сначала.",
                'uz': "Assalomu alaykum! Iltimos, avval imo-ishoralarni ko'rsating."
            }
            return JsonResponse({'status': 'success', 'sentence': default_empty.get(lang, default_empty['uz'])})

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.25,
                "maxOutputTokens": 500,
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }
        data_bytes = json.dumps(payload).encode('utf-8')

        loop = asyncio.get_event_loop()
        def call_gemini():
            last_err = None
            total_keys = len(GEMINI_API_KEYS)
            for attempt in range(total_keys):
                key = get_current_gemini_key()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={'Content-Type': 'application/json'}
                )
                try:
                    with urllib.request.urlopen(req, timeout=7.0) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                            text = text[1:-1].strip()
                        return text
                except urllib.error.HTTPError as http_err:
                    last_err = http_err
                    if is_gemini_quota_exhausted(http_err):
                        print(f"[Gemini Grammar API] Kalit kvotasi tugadi (HTTP {http_err.code}). Kalit ro'yxatdan BUTUNLAY O'CHIRILDI...")
                        remove_and_switch_gemini_key(key)
                        continue
                    else:
                        print(f"[Gemini Grammar API] HTTP {http_err.code} xatosi: {http_err}")
                        break
                except Exception as e:
                    last_err = e
                    print(f"[Gemini Grammar API] Tarmoq xatoligi yoki kutish vaqti: {e}")
                    break
            if last_err:
                raise last_err
            return None

        try:
            # 1-Asosiy: Google Gemini Flash
            sentence = await loop.run_in_executor(None, call_gemini)
            if sentence:
                return JsonResponse({'status': 'success', 'sentence': sentence, 'model': 'Google Gemini Flash'})

            # 2-Zaxira: OpenRouter Multi-AI zaxira
            groq_messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
            sentence = await loop.run_in_executor(None, call_openrouter_api, groq_messages, 150, 0.2)
            if sentence:
                return JsonResponse({'status': 'success', 'sentence': sentence, 'model': 'OpenRouter AI (Zaxira)'})

            raise Exception("Bo'sh natija")
        except Exception as e:
            print("Gemini API error, falling back to local NLP:", e)
            lower_words = [w.lower() for w in words]
            has = lambda kw: any(kw in w for w in lower_words)
            if has('kasal') or has('yordam') or has('betob'):
                fb = {
                    'en': "Hello! I am feeling unwell, could you please help me urgently?",
                    'ru': "Здравствуйте! Я плохо себя чувствую, пожалуйста, окажите мне срочную помощь.",
                    'uz': "Assalomu alaykum! Men o'zimni yomon his qilyapman, iltimos, menga zudlik bilan yordam bera olasizmi?"
                }
            elif has('suv') or has('chanqa'):
                fb = {
                    'en': "Excuse me! I am really thirsty, could you please give me a glass of fresh water?",
                    'ru': "Простите! Я очень хочу пить, не могли бы вы дать мне стакан чистой воды?",
                    'uz': "Kechirasiz! Juda chanqadim, iltimos menga bir piyola toza suv bera olasizmi?"
                }
            elif has('rahmat') and has('ajoyib'):
                fb = {
                    'en': "Thank you so much from the bottom of my heart, everything was absolutely wonderful!",
                    'ru': "Огромное вам спасибо от всей души, всё прошло просто великолепно!",
                    'uz': "Sizga chin qalbimdan kattakon rahmat aytaman, barchasi nihoyatda ajoyib va go'zal bo'ldi!"
                }
            else:
                fb = {
                    'en': f"Respectfully: {words_str}. I wish you a wonderful day!",
                    'ru': f"С уважением: {words_str}. Желаю вам всего наилучшего!",
                    'uz': f"Hurmat bilan ma'lum qilaman: {words_str}. E'tiboringiz va tushunganingiz uchun tashakkur!"
                }
            return JsonResponse({'status': 'success', 'sentence': fb.get(lang, fb['uz']), 'model': 'Local NLP Fallback'})

    async def get(self, request):
        words = request.GET.get('words', '').split(',')
        lang = request.GET.get('lang', 'uz')
        # forward to post logic
        class FakeRequest:
            body = json.dumps({'words': words, 'lang': lang}).encode('utf-8')
        return await self.post(FakeRequest())


@method_decorator(csrf_exempt, name='dispatch')
class SpeechChatView(View):
    async def post(self, request):
        import json
        import urllib.request
        import asyncio

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        message = body.get('message', '').strip()
        lang = body.get('lang', 'uz').lower()
        history = body.get('history', [])

        if not message:
            return JsonResponse({'status': 'error', 'message': "Xabar bo'sh bo'lishi mumkin emas"}, status=400)

        lang_name = "O'zbek tili" if lang == 'uz' else ("English" if lang == 'en' else "Русский язык")
        system_instruction = (
            "Siz Surdo AI aqlli jonli ovozli yordamchisiz. "
            "Foydalanuvchi mikrofondan siz bilan jonli gaplashmoqda. "
            f"Foydalanuvchiga {lang_name}da o'ta tez, samimiy, aniq va lo'nda qilib FAQAT 1 TA (ko'pi bilan 2 ta) qisqa gap bilan javob bering! "
            "Javobingiz darhol ovozli o'qiladi. Hech qanday yulduzcha (*), panjara (#), emoji yoki ortiqcha belgi ishlatmang!"
        )

        contents = []
        if isinstance(history, list):
            for h in history[-6:]:
                role = "user" if h.get('role') in ['user', 'siz'] else "model"
                text_val = h.get('text', '').strip()
                if text_val:
                    contents.append({"role": role, "parts": [{"text": text_val}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 80,
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }
        data_bytes = json.dumps(payload).encode('utf-8')

        loop = asyncio.get_event_loop()
        def call_gemini_chat():
            last_err = None
            total_keys = len(GEMINI_API_KEYS)
            for attempt in range(total_keys):
                key = get_current_gemini_key()
                # gemini-3.5-flash tezkor va aniq javob beruvchi rasmiy model
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={'Content-Type': 'application/json'}
                )
                try:
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        cand = data.get('candidates', [{}])[0]
                        parts = cand.get('content', {}).get('parts', [])
                        reply_text = parts[0]['text'].strip() if (parts and 'text' in parts[0]) else ''
                        reply_text = reply_text.replace('*', '').replace('#', '').strip()
                        if (reply_text.startswith('"') and reply_text.endswith('"')) or (reply_text.startswith("'") and reply_text.endswith("'")):
                            reply_text = reply_text[1:-1].strip()
                        if reply_text:
                            return reply_text
                except urllib.error.HTTPError as http_err:
                    last_err = http_err
                    if is_gemini_quota_exhausted(http_err):
                        print(f"[Gemini SpeechChat API] Kalit kvotasi tugadi (HTTP {http_err.code}). Kalit ro'yxatdan BUTUNLAY O'CHIRILDI...")
                        remove_and_switch_gemini_key(key)
                        continue
                    else:
                        print(f"[Gemini SpeechChat API] HTTP {http_err.code} xatosi: {http_err}")
                        break
                except Exception as e:
                    last_err = e
                    print(f"[Gemini SpeechChat API] Tarmoq xatoligi: {e}")
                    break

            if last_err:
                raise last_err
            return None

        try:
            # 1-Asosiy: Google Gemini Flash (Eng sara bilim va javob)
            reply = await loop.run_in_executor(None, call_gemini_chat)
            if reply:
                return JsonResponse({'status': 'success', 'user_text': message, 'reply': reply, 'model': 'Google Gemini Flash'})

            # 2-Zaxira: OpenRouter Multi-AI zaxira
            ai_messages = [{"role": "system", "content": system_instruction}]
            if isinstance(history, list):
                for h in history[-4:]:
                    r = "user" if h.get('role') in ['user', 'siz'] else "assistant"
                    t = h.get('text', '').strip()
                    if t:
                        ai_messages.append({"role": r, "content": t})
            ai_messages.append({"role": "user", "content": message})

            reply = await loop.run_in_executor(None, call_openrouter_api, ai_messages, 200, 0.6)
            if reply:
                return JsonResponse({'status': 'success', 'user_text': message, 'reply': reply, 'model': 'OpenRouter Multi-AI (Zaxira)'})

            raise Exception("Javob bo'sh keldi")
        except Exception as e:
            print("Gemini SpeechChat API xatosi:", e)
            lower_msg = message.lower()
            if any(w in lower_msg for w in ['salom', 'assalom', 'qalaysiz', 'qandaysiz']):
                fallback_reply = "Assalomu alaykum! Men Surdo AI ovozli yordamchisiman, sizga qanday yordam bera olaman?"
            elif any(w in lower_msg for w in ['qo\'qon', 'universitet', 'institut', 'oliygoh', 'ta\'lim']):
                fallback_reply = "Qo'qon universiteti zamonaviy yo'nalishlar, pedagogika, axborot texnologiyalari va xorijiy tillar bo'yicha yuqori malakali mutaxassislar tayyorlaydigan nufuzli oliy ta'lim muassasasidir."
            elif any(w in lower_msg for w in ['kim', 'nima', 'surdo', 'vazifa']):
                fallback_reply = "Men imo-ishoralarni nutqqa va nutqni muloqotga aylantiruvchi Surdo AI yordamchisiman."
            elif any(w in lower_msg for w in ['rahmat', 'tashakkur']):
                fallback_reply = "Arzimaydi, siz bilan muloqot qilishdan doimo xursandman!"
            else:
                fallback_reply = f"Savolingizni tushundim. {message} mavzusida sizga mamnuniyat bilan yordam beraman."
            return JsonResponse({'status': 'success', 'user_text': message, 'reply': fallback_reply, 'model': 'Fallback Chat'})


class WidgetDemoView(View):
    def get(self, request):
        return render(request, "widget_demo.html", {})


