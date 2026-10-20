"""
Vehicle Theft/Security Source Connector / Wrapper

Database: theft.db
Purpose: Records of stolen, recovered, scrapped, and suspicious vehicles.
         Designed independently by the police/crime department.

KEY DESIGN DECISION (Information Integration):
  This DB uses 'vehicle_identifier' to identify a vehicle.
  This name differs from all other sources — intentional heterogeneity.
  Schema mapping: vehicle_identifier ↔ plate_number / registration_id / vehicle_reg_no
"""
import sqlite3
from typing import Any, Dict, List, Optional
from .base_source import BaseSource
from ..config import DB_THEFT


class TheftSource(BaseSource):
    """
    Wrapper for the Vehicle Theft/Security Database.
    Represents police/crime department records of stolen/suspicious vehicles.
    """

    # LOCAL attribute name — different from all other sources
    LOCAL_KEY = "vehicle_identifier"

    def __init__(self):
        super().__init__(DB_THEFT, "theft")

    def _create_schema(self, conn: sqlite3.Connection):
        """
        Theft/security schema — designed by police department IT team.
        Uses 'vehicle_identifier' as the vehicle key.
        No 'plate_number', 'registration_id', or 'vehicle_reg_no' here.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_security_records (
                case_id             INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_identifier  TEXT NOT NULL,
                case_type           TEXT NOT NULL,
                case_status         TEXT NOT NULL DEFAULT 'OPEN',
                reported_date       TEXT,
                recovery_date       TEXT,
                police_reference    TEXT,
                fir_number          TEXT,
                police_station      TEXT,
                shredding_certificate TEXT,
                shredding_status    TEXT DEFAULT 'NOT_SCRAPPED',
                remarks             TEXT,
                updated_at          TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_theft_vid ON vehicle_security_records(vehicle_identifier)")

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Query using local key 'vehicle_identifier'.
        Returns the most recent/active security record.
        """
        results = self.execute_query(
            """SELECT * FROM vehicle_security_records
               WHERE vehicle_identifier = ?
               ORDER BY reported_date DESC LIMIT 1""",
            (registration_number,)
        )
        return results[0] if results else None

    def get_all_cases(self, registration_number: str) -> List[Dict[str, Any]]:
        """Get all security cases for a vehicle."""
        return self.execute_query(
            "SELECT * FROM vehicle_security_records WHERE vehicle_identifier = ? ORDER BY reported_date DESC",
            (registration_number,)
        )

    def is_stolen(self, registration_number: str) -> bool:
        """Check if vehicle has an active STOLEN status."""
        results = self.execute_query(
            """SELECT * FROM vehicle_security_records
               WHERE vehicle_identifier = ? AND case_type = 'STOLEN' AND case_status = 'OPEN'""",
            (registration_number,)
        )
        return len(results) > 0

    def is_scrapped(self, registration_number: str) -> bool:
        """Check if vehicle is scrapped/shredded."""
        results = self.execute_query(
            """SELECT * FROM vehicle_security_records
               WHERE vehicle_identifier = ? AND case_type IN ('SCRAPPED', 'SHREDDED')""",
            (registration_number,)
        )
        return len(results) > 0

    def get_statistics(self) -> Dict[str, Any]:
        results = self.execute_query(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN case_type='STOLEN' AND case_status='OPEN' THEN 1 ELSE 0 END) as stolen,
                SUM(CASE WHEN case_type='RECOVERED' THEN 1 ELSE 0 END) as recovered,
                SUM(CASE WHEN case_type IN ('SCRAPPED','SHREDDED') THEN 1 ELSE 0 END) as scrapped,
                SUM(CASE WHEN case_type='SUSPICIOUS' THEN 1 ELSE 0 END) as suspicious
               FROM vehicle_security_records"""
        )
        return results[0] if results else {}
