"""
Ministry of Transportation Source Connector / Wrapper

Database: ministry.db
Purpose: Reports submitted to the Ministry of Transportation for uninsured,
         expired, stolen, or suspicious vehicles.
         Designed independently by the Ministry IT team.

KEY DESIGN DECISION (Information Integration):
  This DB uses 'vehicle_ref' to identify a vehicle.
  This name differs from all other sources — intentional heterogeneity.
  Schema mapping: vehicle_ref ↔ plate_number / registration_id / vehicle_reg_no / vehicle_identifier

NOTE: This is a SIMULATED academic system. It does NOT connect to any
      real government database.
"""
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from .base_source import BaseSource
from ..config import DB_MINISTRY


class MinistrySource(BaseSource):
    """
    Wrapper for the Ministry of Transportation Reporting Database.
    Simulated academic system for reporting uninsured/suspicious vehicles.
    """

    # LOCAL attribute name — unique to this source
    LOCAL_KEY = "vehicle_ref"

    def __init__(self):
        super().__init__(DB_MINISTRY, "ministry")

    def _create_schema(self, conn: sqlite3.Connection):
        """
        Ministry reporting schema — designed by Ministry IT team.
        Uses 'vehicle_ref' as the vehicle identifier.
        No relation to 'plate_number', 'registration_id', etc.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transport_reports (
                report_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_ref     TEXT NOT NULL,
                report_type     TEXT NOT NULL,
                report_date     TEXT NOT NULL,
                reason          TEXT,
                severity        TEXT DEFAULT 'MEDIUM',
                report_status   TEXT DEFAULT 'PENDING',
                submitted_by    TEXT,
                action_taken    TEXT,
                resolution_date TEXT,
                notes           TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_min_vref ON transport_reports(vehicle_ref)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_min_status ON transport_reports(report_status)")

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Query using local key 'vehicle_ref'.
        Mediator maps global 'registration_number' → 'vehicle_ref'.
        Returns most recent report.
        """
        results = self.execute_query(
            "SELECT * FROM transport_reports WHERE vehicle_ref = ? ORDER BY report_date DESC LIMIT 1",
            (registration_number,)
        )
        return results[0] if results else None

    def get_all_reports(self, registration_number: str) -> List[Dict[str, Any]]:
        """Get all ministry reports for a vehicle."""
        return self.execute_query(
            "SELECT * FROM transport_reports WHERE vehicle_ref = ? ORDER BY report_date DESC",
            (registration_number,)
        )

    def create_report(self, vehicle_ref: str, report_type: str, reason: str,
                      severity: str = "HIGH", submitted_by: str = "SYSTEM") -> int:
        """
        Create a new Ministry report (e.g., for an uninsured vehicle).
        This is the simulated reporting action.
        """
        return self.execute_write(
            """INSERT INTO transport_reports
               (vehicle_ref, report_type, report_date, reason, severity, report_status, submitted_by)
               VALUES (?, ?, ?, ?, ?, 'PENDING', ?)""",
            (vehicle_ref, report_type, datetime.now().isoformat(), reason, severity, submitted_by)
        )

    def get_all_pending_reports(self) -> List[Dict[str, Any]]:
        """Dashboard: get all pending reports across all vehicles."""
        return self.execute_query(
            "SELECT * FROM transport_reports WHERE report_status = 'PENDING' ORDER BY report_date DESC"
        )

    def get_all_reports_paginated(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        return self.execute_query(
            "SELECT * FROM transport_reports ORDER BY report_date DESC LIMIT ? OFFSET ?",
            (limit, skip)
        )

    def update_report_status(self, report_id: int, status: str, action_taken: str = None) -> bool:
        """Update report status (PENDING → RESOLVED, ACTIONED, etc.)"""
        self.execute_write(
            """UPDATE transport_reports
               SET report_status = ?, action_taken = ?, resolution_date = ?
               WHERE report_id = ?""",
            (status, action_taken, datetime.now().isoformat(), report_id)
        )
        return True

    def get_statistics(self) -> Dict[str, Any]:
        results = self.execute_query(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN report_status='PENDING' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN report_status='RESOLVED' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN report_type='UNINSURED_VEHICLE' THEN 1 ELSE 0 END) as uninsured_reports,
                SUM(CASE WHEN report_type='EXPIRED_INSURANCE' THEN 1 ELSE 0 END) as expired_reports,
                SUM(CASE WHEN report_type='STOLEN_VEHICLE' THEN 1 ELSE 0 END) as stolen_reports
               FROM transport_reports"""
        )
        return results[0] if results else {}
