"""
Vehicle Capture Source Connector / Wrapper

Database: capture.db
Purpose: Records captured vehicles on the road (ANPR camera system).
         This DB was designed by the traffic surveillance team independently.

KEY DESIGN DECISION (Information Integration):
  This DB uses 'plate_number' to identify a vehicle.
  Other databases use different names for the same value:
    - Insurance DB: 'registration_id'
    - Registration DB: 'vehicle_reg_no'
    - Theft DB: 'vehicle_identifier'
    - Ministry DB: 'vehicle_ref'
  The Mediator handles this heterogeneity via schema mapping.
"""
import sqlite3
from typing import Any, Dict, List, Optional
from .base_source import BaseSource
from ..config import DB_CAPTURE


class CaptureSource(BaseSource):
    """
    Wrapper for the Vehicle Capture Database.
    Represents ANPR cameras capturing vehicles on the road.
    """

    # The local attribute name for the vehicle identifier in this source
    LOCAL_KEY = "plate_number"

    def __init__(self):
        super().__init__(DB_CAPTURE, "capture")

    def _create_schema(self, conn: sqlite3.Connection):
        """
        Vehicle capture schema — designed by traffic surveillance team.
        Uses 'plate_number' as the vehicle identifier.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_capture (
                capture_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number        TEXT NOT NULL,
                detected_vehicle_type TEXT,
                detected_color      TEXT,
                capture_timestamp   TEXT NOT NULL,
                capture_location    TEXT,
                image_path          TEXT,
                detection_confidence REAL DEFAULT 0.0,
                ocr_confidence      REAL DEFAULT 0.0,
                camera_id           TEXT,
                lane_number         INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_plate ON vehicle_capture(plate_number)")

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Query using the local key 'plate_number'.
        The mediator passes the globally normalized registration_number;
        this wrapper maps it to its local attribute name.
        """
        results = self.execute_query(
            "SELECT * FROM vehicle_capture WHERE plate_number = ? ORDER BY capture_timestamp DESC LIMIT 1",
            (registration_number,)
        )
        return results[0] if results else None

    def get_all_captures(self, registration_number: str) -> List[Dict[str, Any]]:
        """Return all capture events for a given plate (for history view)."""
        return self.execute_query(
            "SELECT * FROM vehicle_capture WHERE plate_number = ? ORDER BY capture_timestamp DESC",
            (registration_number,)
        )

    def search_fuzzy(self, partial_plate: str) -> List[Dict[str, Any]]:
        """Fuzzy plate search for OCR error recovery."""
        return self.execute_query(
            "SELECT DISTINCT plate_number, detected_vehicle_type, detected_color FROM vehicle_capture WHERE plate_number LIKE ?",
            (f"%{partial_plate}%",)
        )

    def insert_capture(self, data: Dict[str, Any]) -> int:
        """Insert a new vehicle capture event (called by ANPR pipeline)."""
        return self.execute_write(
            """INSERT INTO vehicle_capture
               (plate_number, detected_vehicle_type, detected_color, capture_timestamp,
                capture_location, image_path, detection_confidence, ocr_confidence, camera_id, lane_number)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("plate_number"),
                data.get("detected_vehicle_type"),
                data.get("detected_color"),
                data.get("capture_timestamp"),
                data.get("capture_location"),
                data.get("image_path"),
                data.get("detection_confidence", 0.0),
                data.get("ocr_confidence", 0.0),
                data.get("camera_id"),
                data.get("lane_number"),
            )
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Dashboard statistics."""
        results = self.execute_query(
            "SELECT COUNT(*) as total, COUNT(DISTINCT plate_number) as unique_plates FROM vehicle_capture"
        )
        return results[0] if results else {"total": 0, "unique_plates": 0}
