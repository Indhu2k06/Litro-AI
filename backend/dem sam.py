from preprocessing import preprocess_tamil_text, detect_thirukkural, format_thirukkural, search_kural

# Small demo dataset (you can expand later)
dataset = [
    {"number": 1, "line1": "அகர முதல எழுத்தெல்லாம்", "line2": "ஆதி பகவன் முதற்றே உலகு"},
    {"number": 133, "line1": "சிற்றின்பம் சேர்தல் பெரிது", "line2": "பெரிதல்ல மற்றின்பம் எல்லாம் தறிந்து"},
    {"number": 250, "line1": "அன்புடையார் எல்லாரும் உடன்பிறப்பார்", "line2": "என்பது இயம்புத லின்"}
]

# Example user queries
queries = [
    "திருக்குறள் 133 சொல்லுங்கள்",
    "அகர முதல எழுத்து வரும் குறள்",
    "அன்பு குறள் வேண்டும்",
    "நான் 100 பக்கங்கள் படித்தேன்",
    "ஆனால் வாழ்க்கை எளிதல்ல"
]


from gtts import gTTS
import os

for q in queries:
    print("👉 User Query:", q)

    # Case 1: Detect exact Kural number
    num = detect_thirukkural(q)
    processed = None
    if num:
        k = next((k for k in dataset if k["number"] == num), None)
        if k:
            text = format_thirukkural(k["line1"], k["line2"], num)
            processed = preprocess_tamil_text(text, q)
            print("✅ Output:\n", processed)
            tts = gTTS(processed, lang="ta")
            filename = f"output_{num}.mp3"
            tts.save(filename)
            os.system(f'start {filename}')
            print("----")
            continue

#----------------------------------------------------------------------------------------
    k = search_kural(q, dataset)
    if k:
        text = format_thirukkural(k["line1"], k["line2"], k["number"])
        processed = preprocess_tamil_text(text, q)
        print("✅ Output:\n", processed)
        tts = gTTS(processed, lang="ta")
        filename = f"output_{k['number']}.mp3"
        tts.save(filename)
        os.system(f'start {filename}')
    else:
        # Case 3: Normal Tamil text (not a Kural)
        processed = preprocess_tamil_text(q, q)
        print("✅ Output:\n", processed)
        tts = gTTS(processed, lang="ta")
        filename = "output_text.mp3"
        tts.save(filename)
        os.system(f'start {filename}')
    print("----")
