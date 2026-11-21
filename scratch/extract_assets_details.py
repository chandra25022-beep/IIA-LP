import os
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\backend")))
from app.detection.google_vision_engine import GoogleVisionEngine

engine = GoogleVisionEngine()
assets_dir = Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\test_assets\assets")

images = sorted([f for f in assets_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']])
print(f"Total asset images found: {len(images)}")

extracted_assets = []
for img in images:
    with open(img, "rb") as f:
        data = f.read()
    res = engine.analyze_vehicle_image(data)
    info = {
        "filename": img.name,
        "path": f"test_assets/assets/{img.name}",
        "plate": res.get("plate_number") or "",
        "make": res.get("make") or "",
        "model": res.get("model") or "",
        "color": res.get("color") or "WHITE",
        "vehicle_type": res.get("vehicle_type") or "Car",
        "confidence": res.get("confidence") or 0.90,
    }
    print(f"[{img.name}] -> Plate: '{info['plate']}' | Make: {info['make']} | Model: {info['model']} | Color: {info['color']}")
    extracted_assets.append(info)

out_file = Path(r"f:\M Tech IIITD\M Tech 3rd Sem\IIA\Project part B\Car_Project\Car_Project\data\extracted_assets.json")
with open(out_file, "w") as f:
    json.dump(extracted_assets, f, indent=2)

print(f"\nSaved {len(extracted_assets)} extracted asset profiles to {out_file}")
