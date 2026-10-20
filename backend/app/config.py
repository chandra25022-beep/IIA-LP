"""
Configuration for the IIA Vehicle Integration System.
All 5 database paths are defined here to keep them separate and identifiable.

DISTRIBUTED ARCHITECTURE:
  Master Laptop (this machine): owns capture.db  → runs on port 8000
  Laptop B:  owns insurance.db + registration.db → runs on port 8001
  Laptop C:  owns theft.db + ministry.db         → runs on port 8002
"""
import os
from pathlib import Path

# Project root — backend/app/config.py → backend/app → backend → project_root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Independent data source paths (each is its own SQLite database — by design)
DATA_DIR = BASE_DIR / "data"

DB_CAPTURE = str(DATA_DIR / "capture.db")            # Vehicle Capture DB      (MASTER)
DB_INSURANCE = str(DATA_DIR / "insurance.db")        # Vehicle Insurance DB     (LAPTOP B)
DB_REGISTRATION = str(DATA_DIR / "registration.db")  # Vehicle Registration DB  (LAPTOP B)
DB_THEFT = str(DATA_DIR / "theft.db")                # Theft/Security DB        (LAPTOP C)
DB_MINISTRY = str(DATA_DIR / "ministry.db")          # Ministry Reporting DB    (LAPTOP C)

# ─── Distributed Node URLs ────────────────────────────────────────────────────
# Set these in your environment or a .env file to the LAN IP of each laptop.
# Example:  NODE_B_URL=http://192.168.1.101:8001
#           NODE_C_URL=http://192.168.1.102:8002
NODE_B_URL = os.getenv("NODE_B_URL", "http://localhost:8001")  # Insurance + Registration
NODE_C_URL = os.getenv("NODE_C_URL", "http://localhost:8002")  # Theft + Ministry

# Databases owned locally by the MASTER (can write here directly)
LOCAL_DATABASES = {"capture"}

# Which node owns which databases (used for routing write requests)
DATABASE_NODE_MAP = {
    "capture":      "master",
    "insurance":    "node_b",
    "registration": "node_b",
    "theft":        "node_c",
    "ministry":     "node_c",
}

NODE_URLS = {
    "master": None,           # local
    "node_b": NODE_B_URL,
    "node_c": NODE_C_URL,
}

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
# Open CORS to ALL origins — required so friends on the same LAN can access
# the API from their own browser (their IP won't match localhost).
CORS_ORIGINS = ["*"]

# Schema mapping config
# This defines the GAV (Global-As-View) mapping between the global attribute
# "registration_number" and each source's local attribute name.
# This is the KEY information integration concept — same value, different names.
SCHEMA_MAPPING = {
    "registration_number": {
        "capture":      "plate_number",
        "insurance":    "registration_id",
        "registration": "vehicle_reg_no",
        "theft":        "vehicle_identifier",
        "ministry":     "vehicle_ref",
    }
}

# Fuzzy matching threshold for OCR error correction (0–100)
FUZZY_MATCH_THRESHOLD = 80

# Confidence threshold for accepting a fuzzy plate match
OCR_CONFIDENCE_THRESHOLD = 0.6
