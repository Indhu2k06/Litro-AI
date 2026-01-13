import os, uuid
import difflib
import json
import re
from flask import Flask, request, jsonify, url_for, render_template
from gtts import gTTS
from flask_cors import CORS
from preprocessing import preprocess_tamil_text

# Flask setup (serves static + templates)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder="static", template_folder=os.path.join(BASE_DIR, "templates"))
CORS(app)

# Load Thirukkural data
THIRUKKURAL_LIST = []
try:
    with open("../thirukkural.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        THIRUKKURAL_LIST = data.get("kural", [])
except Exception as e:
    print(f"Could not load Thirukkural data: {e}")

# Tamil literature data
TAMIL_LIT_DATA = {
    "thirukkural": "திருக்குறள் என்பது திருவள்ளுவர் எழுதிய தமிழ் இலக்கியம். இது 1330 குறள்கள் கொண்டது, அறம், பொருள், இன்பம் ஆகிய மூன்று பகுதிகளைக் கொண்டது.",
    "silappathikaram": "சிலப்பதிகாரம் தமிழ் இலக்கியத்தின் ஐந்து பெரிய காவியங்களில் ஒன்று. இளங்கோவடிகள் எழுதிய இந்த காவியம் கண்ணகியின் நீதிக்கான போராட்டத்தை விவரிக்கிறது.",
    "sangam poetry": "சங்க இலக்கியம் என்பது கி.மு. 300 முதல் கி.பி. 300 வரை எழுதப்பட்ட பழமையான தமிழ் பாடல்கள். இதில் காதல், போர், இயற்கை ஆகியவை முக்கியமான தலைப்புகள்.",
    "kambar": "கம்பர் தமிழ் கவிஞர். இவர் கம்பராமாயணம் என்ற காவியத்தை எழுதியவர், இது தமிழ் இலக்கியத்தில் முக்கியமான இடம் பெற்றுள்ளது.",
}

# ---- Preprocess endpoint (returns processed text) ----
@app.route("/preprocess", methods=["POST"])
def preprocess():
    data = request.json or {}
    text = data.get("text", "")
    processed = preprocess_tamil_text(text, query=text)
    return jsonify({"processed": processed})

# ---- Speak endpoint (returns audio for any text after preprocessing) ----
@app.route("/speak", methods=["POST"])
def speak():
    data = request.json or {}
    text = data.get("text", "")
    processed = preprocess_tamil_text(text, query=text)
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(app.static_folder, filename)
    try:
        tts = gTTS(processed, lang="ta")
        tts.save(filepath)
        audio_url = url_for("static", filename=filename, _external=True)
        return jsonify({"processed": processed, "audio_url": audio_url})
    except Exception as e:
        return jsonify({"processed": processed, "audio_url": None, "error": str(e)}), 500

@app.route("/litro", methods=["POST"])
def litro_ai():
    data = request.json
    query = data.get("query", "")

    if not query:
        return jsonify({
            "answer": "⚠️ உரை இல்லை (No input provided).",
            "audio_url": None,
            "meta": {"confidence": 0.0, "method": "none"}
        }), 400

    key = query.strip().lower()
    answer, method, confidence = None, "none", 0.0

    import re
    # ---- Detect Thirukkுறள் by number ----
    kural_match = re.search(r"(\d{1,4})", key)
    if "திருக்குறள்" in key or "kural" in key:
        if kural_match:
            kural_num = int(kural_match.group(1))
            kural_data = next((k for k in THIRUKKURAL_LIST if k.get("Number") == kural_num), None)
            if kural_data:
                answer = kural_data.get("Line1", "") + "\n" + kural_data.get("Line2", "")
                if kural_data.get("explanation"):
                    answer += "\n" + kural_data["explanation"]
                method, confidence = "number", 0.95
            else:
                answer, method, confidence = f"திருக்குறள் எண் {kural_num} கிடைக்கவில்லை.", "number", 0.8
        else:
            answer, method, confidence = "திருக்குறள் எண் குறிப்பிடவும் (1-1330).", "number", 0.3

    # ---- Fuzzy search for Kurals (by starting line/topic) ----
    if not answer and THIRUKKURAL_LIST:
        texts = {k["Number"]: (k["Line1"] + " " + k["Line2"]) for k in THIRUKKURAL_LIST}
        matches = difflib.get_close_matches(query, texts.values(), n=1, cutoff=0.4)
        if matches:
            best = matches[0]
            for k in THIRUKKURAL_LIST:
                if best in (k["Line1"] + " " + k["Line2"]):
                    answer = k["Line1"] + "\n" + k["Line2"]
                    if k.get("explanation"):
                        answer += "\n" + k["explanation"]
                    method, confidence = "fuzzy", difflib.SequenceMatcher(None, query, best).ratio()
                    break

    # ---- Tamil literature topics ----
    if not answer:
        if any(word in key for word in ["சிலப்பதிகாரம்", "silappathikaram"]):
            answer, method, confidence = TAMIL_LIT_DATA["silappathikaram"], "keyword", 0.9
        elif any(word in key for word in ["சங்க", "sangam"]):
            answer, method, confidence = TAMIL_LIT_DATA["sangam poetry"], "keyword", 0.9
        elif any(word in key for word in ["கம்பர்", "kambar"]):
            answer, method, confidence = TAMIL_LIT_DATA["kambar"], "keyword", 0.9
        elif any(word in key for word in ["திருக்குறள்", "kural"]):
            answer, method, confidence = "திருக்குறள் என்பது தமிழ் இலக்கியத்தின் முக்கியமான நூல்.", "keyword", 0.5

    # ---- Final fallback ----
    if not answer:
        answer, method, confidence = (
            "மன்னிக்கவும், இந்த கேள்விக்கு தகவல் இல்லை. திருக்குறள் எண், சிலப்பதிகாரம், சங்க இலக்கியம், கம்பர் ஆகியவற்றைப் பற்றி கேளுங்கள்.",
            "fallback", 0.2
        )

    # ---- Preprocess Tamil text ----
    try:
        processed_text = preprocess_tamil_text(answer, query=query)
    except Exception as e:
        return jsonify({"answer": f"⚠️ Preprocessing failed: {str(e)}", "audio_url": None,
                        "meta": {"confidence": confidence, "method": method}}), 500

    # ---- Generate Audio with gTTS ----
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(app.static_folder, filename)
    try:
        tts = gTTS(processed_text, lang="ta")
        tts.save(filepath)
        audio_url = url_for("static", filename=filename, _external=True)
    except Exception as e:
        audio_url = None
        processed_text += f"\n⚠️ TTS failed: {str(e)}"

    return jsonify({"answer": processed_text, "audio_url": audio_url,
                    "meta": {"confidence": confidence, "method": method}})
