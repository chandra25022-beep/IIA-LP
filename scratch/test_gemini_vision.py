import os
import urllib.request
import json
import base64
from pathlib import Path

API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
IMAGE_PATH = Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\test_assets\assets\test0.9.jpeg")

with open(IMAGE_PATH, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

prompt = """You are an expert Automated Number Plate Recognition (ANPR) and Vehicle Intelligence Vision AI.
Analyze this vehicle image in detail for an Information Integration & Entity Matching project.
Extract the vehicle's attributes and license plate details in strict JSON format.

{
  "plate_number": "normalized plate string without spaces, e.g. DL7CQ1939",
  "raw_plate_text": "raw plate as visible, e.g. DL 7CQ 1939",
  "make": "manufacturer e.g. Hyundai, Mercedes-Benz, Maruti Suzuki, Ford",
  "model": "model name e.g. Creta, C-Class, Swift, Focus, Scorpio",
  "color": "canonical vehicle color: BLACK, WHITE, SILVER, RED, BLUE, GREY",
  "vehicle_type": "vehicle class: SUV, SEDAN, HATCHBACK, TRUCK, MOTORCYCLE",
  "confidence": 0.95,
  "state_code": "DL, MH, UP, HR, or other",
  "ocr_ambiguities": ["any characters that could be confused due to reflection or angle, e.g. Q vs 0/O, 7 vs T"]
}
Return ONLY valid JSON.
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
payload = {
    "contents": [{
        "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
        ]
    }],
    "generationConfig": {
        "response_mime_type": "application/json"
    }
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw_text)
        print("=== GOOGLE AI GEMINI 2.5 FLASH VISION RESULT ===")
        print(json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)
