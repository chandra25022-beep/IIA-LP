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

# Table names per database (primary tables)
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

# Phase 3: FK-PK related tables per database
DB_RELATED_TABLES = {
    "capture": {
        "primary": "vehicle_capture",
        "related": {
            "cameras": {"fk": "camera_id", "pk": "camera_id"},
            "capture_alerts": {"fk": "capture_id", "pk": "capture_id"},
            "operator_logs": {"fk": "capture_id", "pk": "capture_id"},
        }
    },
    "registration": {
        "primary": "vehicle_registration",
        "related": {
            "vehicle_owners": {"fk": "owner_id", "pk": "owner_id"},
            "vehicle_specs": {"fk": "reg_serial", "pk": "reg_serial"},
            "rto_transactions": {"fk": "reg_serial", "pk": "reg_serial"},
            "fitness_certificates": {"fk": "reg_serial", "pk": "reg_serial"},
        }
    },
    "insurance": {
        "primary": "insurance_policies",
        "fallback_primary": "insurance_records",
        "related": {
            "insurance_claims": {"fk": "policy_id", "pk": "policy_id"},
            "policy_endorsements": {"fk": "policy_id", "pk": "policy_id"},
            "premium_payments": {"fk": "policy_id", "pk": "policy_id"},
        }
    },
    "theft": {
        "primary": "vehicle_security_records",
        "related": {
            "investigation_details": {"fk": "case_id", "pk": "case_id"},
            "recovery_records": {"fk": "case_id", "pk": "case_id"},
            "suspect_info": {"fk": "case_id", "pk": "case_id"},
        }
    },
    "ministry": {
        "primary": "transport_reports",
        "related": {
            "enforcement_actions": {"fk": "report_id", "pk": "report_id"},
            "compliance_history": {"fk": "report_id", "pk": "report_id"},
            "blacklisted_vehicles": {"fk": "vehicle_ref", "pk": "vehicle_ref", "direct_key": True},
        }
    },
}

# API settings
NODE_HOST = os.getenv("NODE_HOST", "0.0.0.0")
NODE_PORT = int(os.getenv("NODE_PORT", "8001"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
CORS_ORIGINS = ["*"]
