# Detection package init
from .anpr_pipeline import ANPRPipeline
from .ocr_engine import read_plate_text, EASYOCR_AVAILABLE

__all__ = ["ANPRPipeline", "read_plate_text", "EASYOCR_AVAILABLE"]
