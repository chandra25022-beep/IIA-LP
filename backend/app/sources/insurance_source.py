"""
Vehicle Insurance Source Connector / Wrapper

Database: insurance.db
Purpose: Stores vehicle insurance policy records from insurance providers.
         Designed independently by the insurance company IT team.

KEY DESIGN DECISION (Information Integration):
  This DB uses 'registration_id' to identify a vehicle.
  The Capture DB uses 'plate_number' for the same underlying value.
  Schema mapping: registration_id ↔ plate_number (via global schema)
"""
import sqlite3
from typing import Any, Dict, List, Optional
from .base_source import BaseSource
from ..config import DB_INSURANCE


class InsuranceSource(BaseSource):
    """
    Wrapper for the Vehicle Insurance Database.
    Represents an insurance provider's policy management system.
    """

    # LOCAL attribute name for the vehicle identifier in this source
    # This INTENTIONALLY differs from CaptureSource.LOCAL_KEY = "plate_number"
    LOCAL_KEY = "registration_id"

    def __init__(self):
        super().__init__(DB_INSURANCE, "insurance")

    def _create_schema(self, conn: sqlite3.Connection):
        """
        Insurance schema — designed by insurance company team.
        Uses 'registration_id' as the vehicle identifier.
        Note: no field called 'plate_number' exists here.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS insurance_records (
                policy_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id     TEXT NOT NULL,
                insurer_name        TEXT NOT NULL,
                policy_number       TEXT UNIQUE NOT NULL,
                policy_start_date   TEXT NOT NULL,
                policy_expiry_date  TEXT NOT NULL,
                insurance_status    TEXT NOT NULL DEFAULT 'ACTIVE',
                vehicle_category    TEXT,
                premium_amount      REAL,
                nominee_name        TEXT,
                coverage_type       TEXT DEFAULT 'COMPREHENSIVE',
                claim_count         INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ins_regid ON insurance_records(registration_id)")

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Query using the local key 'registration_id'.
        Mediator maps global 'registration_number' → local 'registration_id'.
        """
        results = self.execute_query(
            """SELECT * FROM insurance_records
               WHERE registration_id = ?
               ORDER BY policy_expiry_date DESC LIMIT 1""",
            (registration_number,)
        )
        return results[0] if results else None

    def get_all_policies(self, registration_number: str) -> List[Dict[str, Any]]:
        """Return all insurance policies (including historical) for a vehicle."""
        return self.execute_query(
            "SELECT * FROM insurance_records WHERE registration_id = ? ORDER BY policy_start_date DESC",
            (registration_number,)
        )

    def check_insurance_status(self, registration_number: str) -> str:
        """
        Returns: 'ACTIVE', 'EXPIRED', 'CANCELLED', 'NOT_FOUND'
        """
        record = self.get_by_registration(registration_number)
        if not record:
            return "NOT_FOUND"
        return record.get("insurance_status", "UNKNOWN")

    def get_statistics(self) -> Dict[str, Any]:
        results = self.execute_query(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN insurance_status='ACTIVE' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN insurance_status='EXPIRED' THEN 1 ELSE 0 END) as expired,
                SUM(CASE WHEN insurance_status='CANCELLED' THEN 1 ELSE 0 END) as cancelled
               FROM insurance_records"""
        )
        return results[0] if results else {}
