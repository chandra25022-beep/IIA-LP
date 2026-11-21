import os
import json
import cv2
from pathlib import Path
import sys

sys.path.insert(0, str(Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\backend")))
from app.detection.anpr_pipeline import ANPRPipeline
from app.integration.entity_resolver import normalize_plate

anpr = ANPRPipeline()
assets_dir = Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\test_assets\assets")

images = sorted([f for f in assets_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']])
print(f"Scanning {len(images)} asset images locally...")

extracted = []
for img in images:
    try:
        with open(img, "rb") as f:
            res = anpr.process_image_bytes(f.read())
        
        plate = res.get("plate") or res.get("raw_ocr") or ""
        color = res.get("detected_color") or "WHITE"
        vtype = res.get("vehicle_type") or "Car"
        conf = res.get("ocr_confidence") or 0.85

        print(f"[{img.name}] -> Plate: '{plate}' | Color: {color} | Type: {vtype} | Conf: {conf:.2f}")
        extracted.append({
            "filename": img.name,
            "plate": plate,
            "color": color,
            "vehicle_type": vtype,
            "confidence": conf,
            "path": f"test_assets/assets/{img.name}"
        })
    except Exception as e:
        print(f"[{img.name}] Error: {e}")

out_path = Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\data\extracted_assets.json")
with open(out_path, "w") as f:
    json.dump(extracted, f, indent=2)

print(f"\nDone! Extracted profiles saved to {out_path}")
