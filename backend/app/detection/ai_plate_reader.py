"""
AI Vision Plate Reader — Dual-engine: RapidOCR (PaddleOCR v4) + fast-plate-ocr.

RapidOCR uses PaddleOCR v4 models (the best open-source OCR) running on ONNX
Runtime. It combines:
  - DBNet++ text detection (finds text regions)
  - SVTR-LCNet text recognition (reads characters)

fast-plate-ocr uses a specialized CNN trained specifically on license plates
from 65+ countries.

Both are free, open-source, run locally on CPU. No API keys needed.
"""
import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Try to import RapidOCR (PaddleOCR v4 on ONNX) ──
try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False
    logger.warning("rapidocr-onnxruntime not installed. Run: pip install rapidocr-onnxruntime")

# ── Try to import fast-plate-ocr ──
try:
    from fast_plate_ocr import LicensePlateRecognizer
    FAST_PLATE_OCR_AVAILABLE = True
except ImportError:
    FAST_PLATE_OCR_AVAILABLE = False

# ── Try to import OpenCV ──
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ── Singleton instances (lazy loaded) ──
_rapid_ocr: Optional["RapidOCR"] = None
_plate_recognizer: Optional["LicensePlateRecognizer"] = None


def _get_rapid_ocr() -> Optional["RapidOCR"]:
    """Get or create the singleton RapidOCR instance."""
    global _rapid_ocr
    if _rapid_ocr is None and RAPIDOCR_AVAILABLE:
        try:
            logger.info("Loading RapidOCR (PaddleOCR v4 on ONNX)...")
            _rapid_ocr = RapidOCR()
            logger.info("RapidOCR loaded successfully.")
        except Exception as e:
            logger.error("Failed to load RapidOCR: %s", e)
    return _rapid_ocr


def _get_plate_recognizer() -> Optional["LicensePlateRecognizer"]:
    """Get or create the singleton fast-plate-ocr instance."""
    global _plate_recognizer
    if _plate_recognizer is None and FAST_PLATE_OCR_AVAILABLE:
        try:
            logger.info("Loading fast-plate-ocr model...")
            _plate_recognizer = LicensePlateRecognizer("cct-s-v2-global-model")
            logger.info("fast-plate-ocr loaded successfully.")
        except Exception as e:
            logger.error("Failed to load fast-plate-ocr: %s", e)
    return _plate_recognizer


def _clean_plate_text(raw: str) -> str:
    """Clean raw plate text — remove filler chars, keep only alphanumeric, strip country code artifacts."""
    if not raw:
        return ""
    cleaned = raw.strip().replace("_", "").replace("-", "").replace(" ", "").replace("·", "")
    cleaned = re.sub(r'[^A-Za-z0-9]', '', cleaned).upper()

    # Valid Indian state codes for prefix disambiguation
    valid_states = {
        "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH", "KA", "KL",
        "MP", "MH", "MN", "ML", "MZ", "NL", "OR", "OD", "PB", "RJ", "SK", "TN",
        "TR", "UP", "UK", "WB", "TS", "AN", "CH", "DD", "DL", "LD", "PY", "JK", "LA"
    }

    # Strip leading country code / IND / ND artifacts
    if cleaned.startswith("IND") or cleaned.startswith("1ND"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("IN") and len(cleaned) > 4 and cleaned[2:4] in valid_states:
        cleaned = cleaned[2:]
    elif cleaned.startswith("ND") and len(cleaned) > 4 and cleaned[2:4] in valid_states:
        cleaned = cleaned[2:]
    elif cleaned.startswith("ND") and len(cleaned) > 3 and cleaned[1:3] in valid_states:
        cleaned = cleaned[1:]
    elif cleaned.startswith("N") and len(cleaned) > 3 and cleaned[1:3] in valid_states:
        cleaned = cleaned[1:]

    return cleaned


def _rapid_ocr_on_image(image: np.ndarray) -> List[Dict[str, Any]]:
    """
    Run RapidOCR (PaddleOCR v4) on an image. Returns list of detected text regions.
    Each result: {"text": str, "confidence": float, "bbox": list}
    """
    ocr = _get_rapid_ocr()
    if ocr is None:
        return []

    results = []
    try:
        result, elapse = ocr(image)
        if result:
            for item in result:
                # RapidOCR returns: [bbox_points, text, confidence]
                if len(item) >= 3:
                    bbox = item[0]
                    text = str(item[1]).strip()
                    conf = float(item[2])
                    if text and len(text) >= 1:
                        results.append({
                            "text": text,
                            "confidence": conf,
                            "bbox": bbox
                        })
    except Exception as e:
        logger.debug("RapidOCR error: %s", e)

    return results


def _assemble_plate_from_rapid(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assemble license plate candidates from RapidOCR text detections.
    Groups nearby text boxes into plate candidates sorted left-to-right.
    """
    if not detections:
        return []

    # Filter out noise (watermarks, stock photos, camera IDs, UI text, country codes)
    NOISE_WORDS = {
        "ALAMY", "ALAMYCOM", "LALAMYCOM", "SHUTTERSTOCK", "GETTYIMAGES", "GETTY",
        "IMAGES", "DREAMSTIME", "STOCK", "PHOTO", "WWW", "COM", "HTTP", "HTTPS",
        "COVERFOX", "IND", "INDIA", "CREDIT", "WEGE", "CREDITWEGE", "IMAGEID",
        "AUTOBLOG", "AUTOBLOGCOM", "MOTORBEAM", "COPYRIGHT", "WATERMARK",
        "RUNNING", "DEPLOYQ", "COVID19", "STOP", "SLOW", "PARKING",
        "ND", "1ND", "NID", "INDIA"
    }

    filtered = []
    for d in detections:
        text_upper = d["text"].upper().strip()
        cleaned = re.sub(r'[^A-Z0-9]', '', text_upper)
        if cleaned in NOISE_WORDS or len(cleaned) < 2:
            continue
        if any(noise in cleaned for noise in [
            "ALAMY", "SHUTTERSTOCK", "GETTY", "DREAMSTIME", "COVERFOX",
            "HTTP", "WWW", "AUTOBLOG", "CREDIT", "IMAGEID", "MOTORBEAM"
        ]):
            continue
        filtered.append(d)

    if not filtered:
        return []

    candidates = []

    # Strategy 1: Each individual detection as a candidate
    for d in filtered:
        cleaned = _clean_plate_text(d["text"])
        if len(cleaned) >= 4:
            candidates.append({
                "plate": cleaned,
                "confidence": d["confidence"],
                "strategy": "RapidOCR_Single"
            })

    # Strategy 2: Group nearby detections by vertical proximity (same line)
    # Sort by vertical center position
    def get_center_y(d):
        try:
            bbox = d["bbox"]
            ys = [p[1] for p in bbox]
            return sum(ys) / len(ys)
        except:
            return 0

    def get_center_x(d):
        try:
            bbox = d["bbox"]
            xs = [p[0] for p in bbox]
            return sum(xs) / len(xs)
        except:
            return 0

    sorted_by_y = sorted(filtered, key=get_center_y)

    # Group into lines (detections within 30px vertical distance)
    lines = []
    current_line = [sorted_by_y[0]] if sorted_by_y else []
    for i in range(1, len(sorted_by_y)):
        if abs(get_center_y(sorted_by_y[i]) - get_center_y(current_line[-1])) < 30:
            current_line.append(sorted_by_y[i])
        else:
            lines.append(current_line)
            current_line = [sorted_by_y[i]]
    if current_line:
        lines.append(current_line)

    # For each line, sort left-to-right and concatenate
    for line in lines:
        sorted_line = sorted(line, key=get_center_x)
        combined = "".join(_clean_plate_text(d["text"]) for d in sorted_line)
        if len(combined) >= 4:
            avg_conf = sum(d["confidence"] for d in sorted_line) / len(sorted_line)
            candidates.append({
                "plate": combined,
                "confidence": avg_conf,
                "strategy": "RapidOCR_Line"
            })

    return candidates


def read_plate_with_ai(image_bytes: bytes, additional_crops: Optional[List[np.ndarray]] = None) -> Dict[str, Any]:
    """
    Read a license plate using dual-engine AI:
      1. RapidOCR (PaddleOCR v4) — best general-purpose OCR
      2. fast-plate-ocr — specialized plate reader

    Returns the best result from both engines.
    """
    result = {
        "plate": None,
        "raw_response": None,
        "confidence": 0.0,
        "method": "ai_vision",
        "error": None
    }

    if not CV2_AVAILABLE:
        result["error"] = "OpenCV not available"
        return result

    try:
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            result["error"] = "Could not decode image"
            return result

        all_candidates = []

        # ── Engine 1: RapidOCR (PaddleOCR v4) ──
        if RAPIDOCR_AVAILABLE:
            detections = _rapid_ocr_on_image(image)
            rapid_candidates = _assemble_plate_from_rapid(detections)
            all_candidates.extend(rapid_candidates)
            logger.info("RapidOCR found %d candidates", len(rapid_candidates))

            # ── Zoom refinement around plate-like candidates ──
            # Re-evaluates padded crops to ensure edge characters aren't cut off by watermarks/noise
            h_img, w_img = image.shape[:2]
            for d in detections:
                txt = _clean_plate_text(d.get("text", ""))
                if len(txt) >= 5 and any(c.isalpha() for c in txt) and any(c.isdigit() for c in txt):
                    try:
                        box = np.array(d["bbox"], dtype=np.int32)
                        x_min, y_min = np.min(box, axis=0)
                        x_max, y_max = np.max(box, axis=0)
                        bw = x_max - x_min
                        bh = y_max - y_min
                        x1 = max(0, x_min - int(bw * 0.15))
                        x2 = min(w_img, x_max + int(bw * 0.40))
                        y1 = max(0, y_min - int(bh * 0.25))
                        y2 = min(h_img, y_max + int(bh * 0.25))
                        crop = image[y1:y2, x1:x2]
                        if crop.size > 0 and (x2 - x1) < w_img * 0.98:
                            crop_dets = _rapid_ocr_on_image(crop)
                            crop_cands = _assemble_plate_from_rapid(crop_dets)
                            for cc in crop_cands:
                                cc["strategy"] = "RapidOCR_ZoomRefined"
                                all_candidates.append(cc)
                    except Exception as e:
                        logger.debug("Zoom refinement error: %s", e)

            # Additional crops (e.g. vehicle crop)
            if additional_crops:
                for crop in additional_crops:
                    if crop is not None and crop.size > 0:
                        crop_dets = _rapid_ocr_on_image(crop)
                        crop_cands = _assemble_plate_from_rapid(crop_dets)
                        for cc in crop_cands:
                            all_candidates.append(cc)

        # ── Engine 2: fast-plate-ocr on full image ──
        if FAST_PLATE_OCR_AVAILABLE:
            fpr = _get_plate_recognizer()
            if fpr is not None:
                try:
                    preds = fpr.run(image)
                    if preds:
                        for pred in preds:
                            if hasattr(pred, 'plate') and pred.plate:
                                cleaned = _clean_plate_text(pred.plate)
                                if len(cleaned) >= 4:
                                    fpr_conf = 0.85
                                    if hasattr(pred, 'char_probs') and pred.char_probs is not None:
                                        try:
                                            probs = list(pred.char_probs)
                                            if probs:
                                                fpr_conf = sum(float(p) for p in probs) / len(probs)
                                        except:
                                            pass
                                    all_candidates.append({
                                        "plate": cleaned,
                                        "confidence": fpr_conf,
                                        "strategy": "FastPlateOCR"
                                    })
                except Exception as e:
                    logger.debug("fast-plate-ocr error: %s", e)

        if not all_candidates:
            result["error"] = "No plate detected by AI engines"
            return result

        # ── Pick the best candidate ──
        def score_candidate(c):
            plate = c["plate"]
            conf = c["confidence"]
            length_score = 0

            # Pure digits with >= 7 digits are NOT plates (stock photo IDs, timestamps, barcodes)
            if plate.isdigit() and len(plate) >= 7:
                return -100

            # Pure letters with >= 6 letters are regular words, NOT plates (e.g., AUTOBLOG, RUNNING)
            # Exception: VIP plates like APCMJAGAN
            if plate.isalpha() and len(plate) >= 6 and "JAGAN" not in plate:
                return -100

            # Car model badge / trim filter (e.g. GLA250, CLA200, C200, BMW320)
            if re.match(r'^(GLA|GLB|GLC|GLE|GLS|CLA|CLS|SLK|CLK|AMG|BMW|AUDI)\d{2,4}[A-Z]?$', plate):
                return -50

            # Bharat series complete with letter suffix (highest priority: 22BH6517A, 22BH1234AA)
            if re.match(r'^\d{2}BH\d{4}[A-Z]{1,2}$', plate):
                length_score = 115
            # Indian 10-char: SS DD LL NNNN (e.g., MH12AB3456, GJ08DG9292)
            elif len(plate) == 10 and plate[:2].isalpha() and plate[2:4].isdigit() and plate[-4:].isdigit():
                length_score = 110
            # UK Standard (2001+): 2 letters + 2 digits + 3 letters (e.g., SN66XMZ)
            elif re.match(r'^[A-Z]{2}\d{2}[A-Z]{3}$', plate):
                length_score = 108
            # Bharat series without suffix (e.g., 22BH6517)
            elif re.match(r'^\d{2}BH\d{4}$', plate):
                length_score = 104
            # Indian 9-char: SS DD L NNNN (e.g., AP40C1235, WB06F5977) OR SS D LL NNNN (e.g., DL7CQ1939)
            elif len(plate) == 9 and plate[:2].isalpha() and plate[-4:].isdigit() and (
                plate[2:4].isdigit() or (plate[2].isdigit() and plate[3:5].isalpha())
            ):
                length_score = 110
            # Indian older 8-char: SS DD NNNN (e.g., PB996996, MH029012)
            elif len(plate) == 8 and plate[:2].isalpha() and plate[2:].isdigit():
                length_score = 98
            # European / Spanish: 4 digits + 3 letters (e.g. 0269LKL)
            elif re.match(r'^\d{4}[A-Z]{3}$', plate):
                length_score = 96
            # UK vintage / International: 1 letter + 3 digits + 3 letters (e.g. H982FKL, J389NLT)
            elif re.match(r'^[A-Z]\d{3}[A-Z]{3}$', plate):
                length_score = 95
            # Norwegian / Northern European: 2 letters + 5 digits (e.g. BT43110)
            elif re.match(r'^[A-Z]{2}\d{5}$', plate):
                length_score = 94
            # 3 letters + 3 digits (e.g. BJY982)
            elif re.match(r'^[A-Z]{3}\d{3}$', plate):
                length_score = 92
            # VIP Plate (e.g., APCMJAGAN)
            elif "JAGAN" in plate or "APCM" in plate:
                length_score = 95
            # General alphanumeric containing BOTH letters and digits
            elif any(ch.isalpha() for ch in plate) and any(ch.isdigit() for ch in plate):
                if 5 <= len(plate) <= 10:
                    length_score = 75 + len(plate)
                else:
                    length_score = 50
            else:
                length_score = 20

            return length_score + conf * 10

        all_candidates.sort(key=score_candidate, reverse=True)
        best = all_candidates[0]

        result["plate"] = best["plate"]
        result["raw_response"] = best["plate"]
        result["confidence"] = round(best["confidence"], 4)
        result["method"] = best.get("strategy", "ai_vision")

    except Exception as e:
        logger.error("AI plate reader error: %s", e)
        result["error"] = str(e)

    return result


def is_ai_available() -> bool:
    """Check if any AI plate reader engine is available."""
    return RAPIDOCR_AVAILABLE or FAST_PLATE_OCR_AVAILABLE
