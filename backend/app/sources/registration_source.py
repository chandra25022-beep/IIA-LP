"""
Vehicle Registration Source Connector / Wrapper

Database: registration.db
Purpose: Government/RTO vehicle registration records.
         Designed independently by the transport department IT team.

KEY DESIGN DECISION (Information Integration):
  This DB uses 'vehicle_reg_no' to identify a vehicle.
  Other DBs use: plate_number / registration_id / vehicle_identifier / vehicle_ref
  Schema mapping: vehicle_reg_no ↔ all other identifiers (via global schema)
"""
import sqlite3
from typing import Any, Dict, List, Optional
from .base_source import BaseSource
from ..config import DB_REGISTRATION


class RegistrationSource(BaseSource):
    """
    Wrapper for the Vehicle Registration Database (RTO/Government system).
    Designed by the transport department — independently of other sources.
    """

    # LOCAL attribute name for the vehicle identifier
    LOCAL_KEY = "vehicle_reg_no"

    def __init__(self):
        super().__init__(DB_REGISTRATION, "registration")

    def _create_schema(self, conn: sqlite3.Connection):
        """
        Registration schema — designed by government transport department.
        Uses 'vehicle_reg_no' as the vehicle identifier.
        Note: 'plate_number' and 'registration_id' do NOT exist here.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_registration (
                reg_serial          INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_reg_no      TEXT UNIQUE NOT NULL,
                owner_name          TEXT NOT NULL,
                owner_contact       TEXT,
                owner_address       TEXT,
                registration_date   TEXT NOT NULL,
                manufacturer        TEXT,
                model_name          TEXT,
                vehicle_class       TEXT,
                registered_color    TEXT,
                fuel_type           TEXT,
                engine_number       TEXT,
                chassis_number      TEXT,
                seating_capacity    INTEGER,
                registration_status TEXT DEFAULT 'ACTIVE',
                rto_office          TEXT,
                fitness_valid_until TEXT,
                tax_valid_until     TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_vno ON vehicle_registration(vehicle_reg_no)")

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Query using local key 'vehicle_reg_no'.
        Mediator maps global 'registration_number' → 'vehicle_reg_no'.
        """
        results = self.execute_query(
            "SELECT * FROM vehicle_registration WHERE vehicle_reg_no = ?",
            (registration_number,)
        )
        return results[0] if results else None

    def get_vehicle_details(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """Get complete vehicle details including owner info."""
        return self.get_by_registration(registration_number)

    def get_statistics(self) -> Dict[str, Any]:
        results = self.execute_query(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN registration_status='ACTIVE' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN registration_status='SUSPENDED' THEN 1 ELSE 0 END) as suspended,
                SUM(CASE WHEN registration_status='EXPIRED' THEN 1 ELSE 0 END) as expired
               FROM vehicle_registration"""
        )
        return results[0] if results else {}
