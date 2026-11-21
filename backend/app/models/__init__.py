"""
Models Package — License Plate Recognition & AI Vision Models
Exposes:
  - GoogleVisionEngine: Google Gemini Multimodal Vision AI (Make, Model, Color, Type, Plate)
  - read_plate_dual_engine: Local ONNX-based PaddleOCR v4 + fast-plate-ocr
  - ANPRPipeline: Complete end-to-end ANPR Pipeline
  - OCREngine: Multi-engine OCR fallback system
"""
from ..detection.google_vision_engine import GoogleVisionEngine
from ..detection.ai_plate_reader import read_plate_dual_engine
from ..detection.anpr_pipeline import ANPRPipeline
from ..detection.ocr_engine import OCREngine

__all__ = [
    "GoogleVisionEngine",
    "read_plate_dual_engine",
    "ANPRPipeline",
    "OCREngine",
]
