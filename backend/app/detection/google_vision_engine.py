"""
Google AI Vision Engine — Powered by Google Gemini Multimodal Vision API
Extracts License Plate, Vehicle Make, Model, Color, Vehicle Type, and OCR ambiguities.

Used for IIA Phase 2:
- ANPR Plate Extraction under Noise
- Contextual Vehicle Attribute Extraction (Make, Model, Color, Type)
- Contextual Data Cleansing against Distributed Federated Registries
"""
import os
import json
import base64
import hashlib
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
    _base = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(_base / ".env")
    load_dotenv(_base / "backend" / ".env")
except Exception:
    pass

logger = logging.getLogger(__name__)

DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY", "")
PREFERRED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

# In-memory cache by image content hash (instant 0ms response on re-scans)
_VISION_CACHE: Dict[str, Dict[str, Any]] = {}


class GoogleVisionEngine:
    """Multimodal Vision Engine utilizing Google Gemini AI Vision for ANPR & contextual attributes."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DEFAULT_API_KEY

    def analyze_vehicle_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Send vehicle image to Google Gemini Vision and return structured ANPR + contextual data.
        Includes SHA-256 caching for zero-latency instant retrieval on repeated scans.
        """
        if not image_bytes:
            return {"success": False, "error": "Empty image bytes"}

        # Check Cache
        img_hash = hashlib.sha256(image_bytes).hexdigest()
        if img_hash in _VISION_CACHE:
            cached = dict(_VISION_CACHE[img_hash])
            cached["cached"] = True
            return cached

        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """You are an Automated Number Plate Recognition (ANPR) and Vehicle Intelligence Vision AI.
Analyze this vehicle image in detail for an Information Integration & Entity Matching project.
Extract the vehicle's attributes and license plate details in strict JSON format:

{
  "plate_number": "normalized plate string without spaces or special chars, e.g. DL7CQ1939",
  "raw_plate_text": "raw plate as visible on vehicle, e.g. DL 7CQ 1939",
  "make": "manufacturer e.g. Hyundai, Mercedes-Benz, Maruti Suzuki, Ford, Mahindra",
  "model": "model name e.g. Creta, C-Class, Swift, Focus, Scorpio",
  "color": "canonical vehicle color: BLACK, WHITE, SILVER, RED, BLUE, GREY",
  "vehicle_type": "vehicle class: SUV, SEDAN, HATCHBACK, TRUCK, MOTORCYCLE",
  "confidence": 0.95,
  "state_code": "DL, MH, UP, HR, or other",
  "ocr_ambiguities": ["any characters that could be confused due to reflection or angle, e.g. Q vs 0/O, 7 vs T"]
}
Return ONLY valid JSON.
"""
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": img_b64}}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for model in PREFERRED_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    raw_text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Strip markdown code blocks if present
                    if raw_text.startswith("```"):
                        lines = raw_text.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        raw_text = "\n".join(lines).strip()
                    result = json.loads(raw_text)
                    result["engine"] = f"Google AI Vision ({model})"
                    result["success"] = True
                    result["cached"] = False
                    if result.get("plate_number"):
                        import re
                        result["plate_number"] = re.sub(r'[^A-Z0-9]', '', str(result["plate_number"]).upper())
                    if result.get("color"):
                        result["color"] = str(result["color"]).strip().upper()
                    if result.get("vehicle_type"):
                        result["vehicle_type"] = str(result["vehicle_type"]).strip().upper()
                    # Store in cache
                    _VISION_CACHE[img_hash] = result
                    return result
            except Exception as e:
                logger.warning(f"Google Vision model {model} attempt: {e}. Trying fallback...")
                continue

        return {
            "success": False,
            "error": "Google Vision cloud service busy or rate-limited; local dual-engine fallback active.",
            "plate_number": "",
            "raw_plate_text": "",
            "make": "",
            "model": "",
            "color": "",
            "vehicle_type": "",
            "confidence": 0.0,
            "ocr_ambiguities": []
        }
