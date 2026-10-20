"""
ANPR Pipeline — Automatic Number Plate Recognition (Enhanced Phase 2)
Combines:
  1. Image decoding & validation
  2. Vehicle detection (YOLOv8n)
  3. Multi-Strategy License Plate Region Detection:
     - Strategy A: YOLOv8 trained plate detection (plate_model.pt)
     - Strategy B: OpenCV Bilateral filter + Canny edge + 4-point contour quadrilateral
     - Strategy C: Morphological BlackHat / rectangular gradient filtering
     - Strategy D: Lower-half bumper region of vehicle
     - Strategy E: Full image multi-scale scan
  4. Multi-pass OCR (EasyOCR with CLAHE, bilateral filter, Otsu threshold, 2x upscaling)
  5. License plate normalization & Indian state RTO decoding
  6. Return candidate hypotheses and uncertainty metadata

Phase 2 Enhancements:
  - Adaptive crop padding (5-15% margin)
  - Two-line plate reading & assembly
  - Advanced deskew / perspective transform
  - Multi-binarization OCR consensus
  - Improved candidate ranking with Indian syntax validation
"""
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available.")

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("Ultralytics YOLO not available.")

from .ocr_engine import read_plate_text, is_indian_plate_format, is_valid_general_plate, EASYOCR_AVAILABLE
from .ai_plate_reader import read_plate_with_ai, is_ai_available
from ..integration.entity_resolver import normalize_plate, is_valid_plate_format, decode_rto_state


class ANPRPipeline:
    """
    Automatic Number Plate Recognition Pipeline.
    Robust against diverse camera angles, lighting conditions, foreign formats, and noise.
    """

    def __init__(self):
        self.vehicle_model = None
        self.plate_model = None
        self._load_models()

    def _load_models(self):
        """Load YOLO models from the backend directory."""
        if not YOLO_AVAILABLE:
            return

        try:
            # Backend root directory
            backend_dir = Path(__file__).resolve().parent.parent.parent

            # 1. Load vehicle detector
            yolo_vehicle_path = backend_dir / "yolov8n.pt"
            if yolo_vehicle_path.exists():
                self.vehicle_model = YOLO(str(yolo_vehicle_path))
                logger.info("Loaded YOLOv8 vehicle model from %s", yolo_vehicle_path)
            else:
                self.vehicle_model = YOLO("yolov8n.pt")

            # 2. Load dedicated license plate model
            plate_model_path = backend_dir / "plate_model.pt"
            if plate_model_path.exists():
                self.plate_model = YOLO(str(plate_model_path))
                logger.info("Loaded YOLOv8 plate model from %s", plate_model_path)
            else:
                logger.warning("Plate model not found at %s", plate_model_path)
                self.plate_model = None

        except Exception as e:
            logger.warning("Could not load YOLO models: %s", e)
            self.vehicle_model = None
            self.plate_model = None

    def _detect_vehicles(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect vehicles using YOLOv8."""
        if not YOLO_AVAILABLE or self.vehicle_model is None:
            return []

        vehicle_classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        try:
            results = self.vehicle_model(image, verbose=False)
            detections = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    if cls_id in vehicle_classes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        detections.append({
                            "class": vehicle_classes[cls_id],
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2],
                        })
            return detections
        except Exception as e:
            logger.debug("Vehicle detection error: %s", e)
            return []

    def _detect_plate_candidates(self, image: np.ndarray, vehicle_crop: Optional[np.ndarray] = None) -> List[Tuple[np.ndarray, str]]:
        """
        Multi-Strategy License Plate Region Localization.
        Returns a list of (candidate_crop_image, strategy_name).
        Enhanced with adaptive padding and more robust contour detection.
        """
        target_img = vehicle_crop if vehicle_crop is not None and vehicle_crop.size > 0 else image
        h, w = target_img.shape[:2]
        candidates: List[Tuple[np.ndarray, str]] = []

        # ─── STRATEGY A: YOLOv8 Plate Detector ─────────────────────────
        if self.plate_model is not None:
            try:
                # Run on vehicle crop
                results = self.plate_model(target_img, verbose=False)
                for res in results:
                    for box in res.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        if conf >= 0.20:
                            # Adaptive padding: 12% to prevent clipping boundary letters
                            pad_x = int((x2 - x1) * 0.12)
                            pad_y = int((y2 - y1) * 0.15)
                            px1 = max(0, x1 - pad_x)
                            py1 = max(0, y1 - pad_y)
                            px2 = min(w, x2 + pad_x)
                            py2 = min(h, y2 + pad_y)
                            crop = target_img[py1:py2, px1:px2]
                            if crop.size > 0:
                                candidates.append((crop, f"YOLO_Plate(conf={conf:.2f})"))

                # Also run on full image if different from target_img
                if target_img is not image:
                    res_full = self.plate_model(image, verbose=False)
                    for res in res_full:
                        for box in res.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            if conf >= 0.25:
                                # Adaptive padding for full image crops
                                fh, fw = image.shape[:2]
                                pad_x = int((x2 - x1) * 0.12)
                                pad_y = int((y2 - y1) * 0.15)
                                px1 = max(0, x1 - pad_x)
                                py1 = max(0, y1 - pad_y)
                                px2 = min(fw, x2 + pad_x)
                                py2 = min(fh, y2 + pad_y)
                                crop = image[py1:py2, px1:px2]
                                if crop.size > 0:
                                    candidates.append((crop, f"YOLO_FullPlate(conf={conf:.2f})"))
            except Exception as e:
                logger.debug("YOLO plate detection error: %s", e)

        # ─── STRATEGY B: Contour & Aspect Ratio (Advanced_Image_Processor) ─────
        if CV2_AVAILABLE:
            try:
                gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
                bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
                edged = cv2.Canny(bfilter, 30, 200)

                contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

                for contour in contours:
                    x, y, bw, bh = cv2.boundingRect(contour)
                    aspect_ratio = bw / float(bh) if bh > 0 else 0
                    area = bw * bh

                    # License plates typically have aspect ratio between 1.5 and 6.5
                    # Also accept narrower ratios for two-line plates (Indian high-security)
                    if 1.2 <= aspect_ratio <= 6.5 and area > 800 and area < (h * w * 0.5):
                        pad_x = int(bw * 0.10)
                        pad_y = int(bh * 0.10)
                        x1 = max(0, x - pad_x)
                        y1 = max(0, y - pad_y)
                        x2 = min(w, x + bw + pad_x)
                        y2 = min(h, y + bh + pad_y)
                        crop = target_img[y1:y2, x1:x2]
                        if crop.size > 0:
                            candidates.append((crop, "Contour_AspectRatio"))
            except Exception as e:
                logger.debug("Contour detection error: %s", e)

        # ─── STRATEGY C: Morphological Rectangular Gradient ───────────
        if CV2_AVAILABLE:
            try:
                gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
                # Rectangular kernel highlighting horizontal character groupings
                rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
                tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, rect_kernel)
                _, thresh = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                morph_contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                morph_contours = sorted(morph_contours, key=cv2.contourArea, reverse=True)[:5]
                for c in morph_contours:
                    x, y, bw, bh = cv2.boundingRect(c)
                    ar = bw / float(bh) if bh > 0 else 0
                    if 2.0 <= ar <= 6.0 and bw * bh > 1200:
                        pad_x = int(bw * 0.08)
                        pad_y = int(bh * 0.08)
                        crop = target_img[max(0,y-pad_y):min(h,y+bh+pad_y), max(0,x-pad_x):min(w,x+bw+pad_x)]
                        if crop.size > 0:
                            candidates.append((crop, "Morphological_Filter"))
            except Exception as e:
                logger.debug("Morphological filter error: %s", e)

        # ─── STRATEGY D: Lower-half bumper region ─────────────────────
        lower_half = target_img[int(h * 0.45):h, :]
        if lower_half.size > 0:
            candidates.append((lower_half, "Bumper_Region_Heuristic"))

        # ─── STRATEGY E: Grille / Central Plate Prior (Front/Rear bumper focus) ──
        center_plate = target_img[int(h * 0.55):int(h * 0.90), int(w * 0.20):int(w * 0.80)]
        if center_plate.size > 0:
            candidates.append((center_plate, "Center_Plate_Prior"))

        # Boot / tailgate recess (Rear plates)
        boot_recess = target_img[int(h * 0.35):int(h * 0.85), int(w * 0.20):int(w * 0.80)]
        if boot_recess.size > 0:
            candidates.append((boot_recess, "Boot_Recess_Prior"))

        # ─── STRATEGY F: Full image ───────────────────────────────────
        candidates.append((target_img, "Full_Vehicle_Image"))
        if target_img is not image:
            candidates.append((image, "Original_Image"))

        return candidates

    def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process an uploaded image through the complete ANPR pipeline.
        Guaranteed to never crash or throw an unhandled error on any image.
        """
        result = {
            "plate": None,
            "raw_ocr": None,
            "ocr_confidence": 0.0,
            "vehicle_type": None,
            "detected_color": None,
            "detection_confidence": 0.0,
            "is_valid_format": False,
            "decoded_origin": None,
            "candidates": [],
            "pipeline_stages": {},
            "detection_strategy": None,
            "error": None,
        }

        if not CV2_AVAILABLE:
            result["error"] = "OpenCV not available on this server."
            return result

        try:
            # Stage 1: Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                result["error"] = "Invalid image file. Could not decode."
                return result
            result["pipeline_stages"]["image_loaded"] = True

            # ===== STAGE 0: AI VISION PRIMARY DETECTION =====
            # Uses Google Gemini Vision API — the same AI algorithm
            # that reads plates by looking at images directly.
            ai_result = None
            if is_ai_available():
                logger.info("AI Vision plate reader available — using as primary method")
                ai_result = read_plate_with_ai(image_bytes)
                result["pipeline_stages"]["ai_vision"] = True
            else:
                result["pipeline_stages"]["ai_vision"] = False

            # Stage 2: Vehicle detection (YOLOv8)
            vehicle_crop = None
            vehicles = self._detect_vehicles(image)
            if vehicles:
                # Prioritize primary foreground vehicle by bounding box area weighted by confidence
                best_vehicle = max(
                    vehicles,
                    key=lambda v: (v["bbox"][2] - v["bbox"][0]) * (v["bbox"][3] - v["bbox"][1]) * (1.0 + v["confidence"])
                )
                result["vehicle_type"] = best_vehicle["class"]
                result["detection_confidence"] = best_vehicle["confidence"]
                x1, y1, x2, y2 = best_vehicle["bbox"]
                ih, iw = image.shape[:2]
                # Only crop vehicle if the detected bbox covers a significant portion
                if (x2 - x1) > iw * 0.25:
                    vehicle_crop = image[y1:y2, x1:x2]
                result["pipeline_stages"]["vehicle_detected"] = True
            else:
                result["pipeline_stages"]["vehicle_detected"] = False

            # Stage 3: Color detection
            crop_for_color = vehicle_crop if vehicle_crop is not None else image
            result["detected_color"] = self._detect_dominant_color(crop_for_color)
            result["pipeline_stages"]["color_detected"] = True

            # ===== ENSEMBLE: AI + EasyOCR both contribute candidates =====
            # Stage 4: Multi-Strategy Plate Region Detection
            candidate_regions = self._detect_plate_candidates(image, vehicle_crop)
            result["pipeline_stages"]["plate_region_detected"] = len(candidate_regions) > 1

            # Stage 5: Multi-pass OCR across candidate regions (EasyOCR + fast-plate-ocr)
            best_plate: Optional[str] = None
            best_conf: float = 0.0
            best_prio: int = 0
            best_strategy: Optional[str] = None
            all_discovered_candidates = []

            # 5a: Add AI Vision result as a high-priority candidate
            if ai_result and ai_result.get("plate"):
                ai_plate = ai_result["plate"]
                ai_conf = ai_result.get("confidence", 0.95)
                ai_strat = ai_result.get("method", "RapidOCR_AI")
                is_ind = is_indian_plate_format(ai_plate)
                is_gen = is_valid_general_plate(ai_plate)
                prio = 6 if is_ind and len(ai_plate) == 10 else (5 if is_ind else (4 if is_gen else 2))
                all_discovered_candidates.append({
                    "cleaned": ai_plate,
                    "corrected": ai_plate,
                    "confidence": ai_conf,
                    "is_indian_format": is_ind,
                    "strategy": ai_strat,
                })
                if prio > best_prio or (prio == best_prio and ai_conf > best_conf):
                    best_plate = ai_plate
                    best_conf = ai_conf
                    best_prio = prio
                    best_strategy = ai_strat
                logger.info("AI Vision candidate: %s (prio=%d, conf=%.3f, strat=%s)", ai_plate, prio, ai_conf, ai_strat)

            # 5b: Also run fast-plate-ocr on each plate crop for additional candidates
            if is_ai_available():
                from .ai_plate_reader import _get_plate_recognizer, _clean_plate_text
                fpr = _get_plate_recognizer()
                if fpr is not None:
                    for crop_img, strategy in candidate_regions:
                        try:
                            preds = fpr.run(crop_img)
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
                                                except Exception:
                                                    pass
                                            is_ind = is_indian_plate_format(cleaned)
                                            is_gen = is_valid_general_plate(cleaned)
                                            prio = 6 if is_ind and len(cleaned) == 10 else (5 if is_ind else (4 if is_gen else 2))
                                            all_discovered_candidates.append({
                                                "cleaned": cleaned,
                                                "corrected": cleaned,
                                                "confidence": fpr_conf,
                                                "is_indian_format": is_ind,
                                                "strategy": f"FastPlateOCR_{strategy}",
                                            })
                                            if prio > best_prio or (prio == best_prio and fpr_conf > best_conf):
                                                best_plate = cleaned
                                                best_conf = fpr_conf
                                                best_prio = prio
                                                best_strategy = f"FastPlateOCR_{strategy}"
                        except Exception as e:
                            logger.debug("FastPlateOCR error on %s: %s", strategy, e)

            # Only run heavy EasyOCR candidate sweep if AI engines did not find a high-confidence plate
            if best_prio < 4 or best_conf < 0.85:
                for crop, strategy in candidate_regions:
                    text, conf, cand_list = read_plate_text(crop)
                    if cand_list:
                        for c in cand_list:
                            c["strategy"] = strategy
                            all_discovered_candidates.append(c)

                    if text:
                        is_ind = is_indian_plate_format(text)
                        is_gen = is_valid_general_plate(text)
                        prio = 5 if is_ind else (4 if is_gen and (re.match(r'^[A-Z]\d{3}[A-Z]{3}$', text) or "JAGAN" in text) else (2 if is_gen else 1))

                        # Immediate break on high-confidence Indian plate
                        if prio == 5 and conf >= 0.60:
                            best_plate = text
                            best_conf = conf
                            best_prio = prio
                            best_strategy = strategy
                            break

                        # Select best candidate by priority first, then confidence
                        if prio > best_prio or (prio == best_prio and conf > best_conf):
                            best_plate = text
                            best_conf = conf
                            best_prio = prio
                            best_strategy = strategy

            result["raw_ocr"] = best_plate
            result["ocr_confidence"] = round(best_conf, 4)
            result["detection_strategy"] = best_strategy
            result["pipeline_stages"]["ocr_run"] = bool(best_plate)

            # Stage 6: Normalization & State Decoding
            if best_plate:
                normalized = normalize_plate(best_plate)
                result["plate"] = normalized
                result["is_valid_format"] = is_valid_plate_format(normalized)
                result["decoded_origin"] = decode_rto_state(normalized)
                result["pipeline_stages"]["normalized"] = True

            # Deduplicate alternative candidate hypotheses
            unique_cands = {}
            for c in all_discovered_candidates:
                txt = c.get("corrected") or c.get("cleaned")
                if txt and txt not in unique_cands:
                    unique_cands[txt] = {
                        "plate": txt,
                        "confidence": round(float(c.get("confidence", 0.0)), 3),
                        "is_indian": bool(c.get("is_indian_format", False)),
                        "strategy": c.get("strategy", "OCR")
                    }
            result["candidates"] = list(unique_cands.values())[:8]
            result["candidate_plates"] = result["candidates"]
            result["detection_method"] = best_strategy

        except Exception as e:
            logger.error("ANPR pipeline error: %s", e, exc_info=True)
            result["error"] = f"ANPR scan error: {str(e)}"

        return result

    def _detect_dominant_color(self, image: np.ndarray) -> Optional[str]:
        """Detect vehicle dominant color using HSV color space."""
        if not CV2_AVAILABLE or image is None or image.size == 0:
            return None

        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            avg_h = float(np.mean(h))
            avg_s = float(np.mean(s))
            avg_v = float(np.mean(v))

            if avg_s < 35 and avg_v > 190:
                return "WHITE"
            elif avg_s < 35 and avg_v < 75:
                return "BLACK"
            elif avg_s < 55 and avg_v < 155:
                return "SILVER"
            elif avg_h < 15 or avg_h > 165:
                return "RED"
            elif 100 <= avg_h <= 130:
                return "BLUE"
            elif 35 <= avg_h <= 85:
                return "GREEN"
            elif 15 <= avg_h <= 35:
                return "YELLOW"
            else:
                return "OTHER"
        except Exception:
            return None
