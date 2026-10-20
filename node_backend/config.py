"""
Node Backend Configuration
==========================
This file is for the NODE backend (Laptop B or Laptop C).

Set environment variables before running:
  NODE_DATABASES=insurance,registration    (for Laptop B)
  NODE_DATABASES=theft,ministry            (for Laptop C)
  NODE_PORT=8001                           (for Laptop B)
  NODE_PORT=8002                           (for Laptop C)
"""
import os
from pathlib import Path

# Root of THIS file -> node_backend/ -> project_root
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Which databases this node owns — set via env var
# Laptop B: NODE_DATABASES=insurance,registration
# Laptop C: NODE_DATABASES=theft,ministry
_raw = os.getenv("NODE_DATABASES", "insurance,registration")
NODE_DATABASES = [d.strip() for d in _raw.split(",") if d.strip()]

# Database file paths
DB_FILES = {
    "capture":      str(DATA_DIR / "capture.db"),
    "insurance":    str(DATA_DIR / "insurance.db"),
    "registration": str(DATA_DIR / "registration.db"),
    "theft":        str(DATA_DIR / "theft.db"),
    "ministry":     str(DATA_DIR / "ministry.db"),
}

# Table names per database
DB_TABLES = {
    "capture":      "vehicle_capture",
    "insurance":    "insurance_records",
    "registration": "vehicle_registration",
    "theft":        "vehicle_security_records",
    "ministry":     "transport_reports",
}

# Local key (vehicle identifier column) per database
DB_LOCAL_KEY = {
    "capture":      "plate_number",
    "insurance":    "registration_id",
    "registration": "vehicle_reg_no",
    "theft":        "vehicle_identifier",
    "ministry":     "vehicle_ref",
}

# API settings
NODE_HOST = os.getenv("NODE_HOST", "0.0.0.0")
NODE_PORT = int(os.getenv("NODE_PORT", "8001"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
CORS_ORIGINS = ["*"]
