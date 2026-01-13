
import re
import difflib

# Tamil character sets
uyir = "அஆஇஈஉஊஎஏஐஒஓஔ"
mei = "க் ங் ச் ஞ் ட் ண் த் ந் ப் ம் ய் ர் ல் வ் ழ் ள் ற் ன்".split()

# 1. Sandhi Splitter
def auto_split_sandhi(word: str) -> str:
    for m in mei:
        for u in uyir:
            pattern = m + u
            fixed = m + "-" + u
            if pattern in word:
                word = word.replace(pattern, fixed)
    return word

def split_sandhi_sentence(text: str) -> str:
    words = text.split()
    return " ".join(auto_split_sandhi(w) for w in words)

# 2. Number Normalizer
tamil_numbers = {
    "0": "பூஜ்யம்", "1": "ஒன்று", "2": "இரண்டு", "3": "மூன்று", "4": "நான்கு",
    "5": "ஐந்து", "6": "ஆறு", "7": "ஏழு", "8": "எட்டு", "9": "ஒன்பது",
    "10": "பத்து", "100": "நூறு", "1000": "ஆயிரம்"
}

def normalize_numbers(text: str) -> str:
    for num, word in tamil_numbers.items():
        text = re.sub(rf"\b{num}\b", word, text)
    return text

# 3. Thirukkுறள் Detection
def detect_thirukkural(query: str) -> int | None:
    match = re.search(r"திருக்குறள்\s*(\d+)", query)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 1330:
            return num
    return None

# 4. Thirukkுறள் Formatter
def format_thirukkural(line1: str, line2: str, number: int = None) -> str:
    header = f"திருக்குறள் {number}\n" if number else ""
    return f"{header}{line1},\n{line2}"

# 5. Pause Inserter
def insert_pauses(text: str) -> str:
    pause_words = ["ஆனால்", "எனவே", "அதனால்", "அல்லது"]
    for w in pause_words:
        text = text.replace(w, w + ",")
    return text

# 6. Main Preprocessor
def preprocess_tamil_text(text: str, query: str = "") -> str:
    if not text or text.strip() == "":
        return "⚠️ உரை இல்லை (No text provided)."

    # Step 1: Normalize numbers
    text = normalize_numbers(text)

    # Step 2: Sandhi splitting
    text = split_sandhi_sentence(text)

    # Step 3: Insert pauses
    text = insert_pauses(text)

    return text.strip()
