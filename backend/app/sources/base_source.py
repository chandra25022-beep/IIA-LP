"""
Base source connector / wrapper.
Each independent data source has its own connector that encapsulates
all communication with that specific database.

This implements the "Wrappers" concept from IIA-1 (Mediation/Federated architecture).
Each wrapper knows only its own schema — it does NOT know about other sources.
"""
import sqlite3
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from contextlib import contextmanager


class BaseSource(ABC):
    """
    Abstract base class for all data source connectors.
    Each source connector wraps one SQLite database file.
    """

    def __init__(self, db_path: str, source_name: str):
        self.db_path = db_path
        self.source_name = source_name
        self._ensure_db_exists()

    @contextmanager
    def _get_connection(self):
        """Context manager for safe database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # return dict-like rows
        try:
            yield conn
        finally:
            conn.close()

    def _ensure_db_exists(self):
        """Initialize the database schema if not already created."""
        with self._get_connection() as conn:
            self._create_schema(conn)
            conn.commit()

    @abstractmethod
    def _create_schema(self, conn: sqlite3.Connection):
        """Create the database tables. Each source has its own independent schema."""
        pass

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts."""
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE and return the last row id."""
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[tuple]):
        """Execute a query with multiple parameter sets (bulk insert)."""
        with self._get_connection() as conn:
            conn.executemany(query, params_list)
            conn.commit()

    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema metadata for the Integration View page."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            schema = {}
            for table in tables:
                col_cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "pk": bool(col["pk"]),
                        "notnull": bool(col["notnull"]),
                    }
                    for col in col_cursor.fetchall()
                ]
                count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                record_count = count_cursor.fetchone()[0]
                schema[table] = {"columns": columns, "record_count": record_count}
            return {"source": self.source_name, "db_path": self.db_path, "tables": schema}

    @abstractmethod
    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch records matching the given vehicle registration number.
        Each source uses its own local attribute name for this value.
        """
        pass

    def get_all_sample_records(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return sample records for the Data Sources page."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1"
            )
            table_row = cursor.fetchone()
            if not table_row:
                return []
            table = table_row[0]
            cursor = conn.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
