"""
Source Registry & Health Monitor

Implements a centralized registry for all data source connections.
Tracks availability, response times, error rates, and connection metadata.

This addresses Criterion 7: "Establishing the communication between the data sources"

In a real federated system, the registry is the component that:
- Knows WHICH sources exist and HOW to reach them
- Monitors source HEALTH and AVAILABILITY
- Implements RETRY LOGIC for transient failures
- Tracks RESPONSE TIMES for query optimization
- Maintains a CONNECTION POOL per source (simulated here)

Reference: IIA-1 slide 20 — "The mediator must know about all sources
and how to connect to them"
"""
import time
import sqlite3
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SourceMetadata:
    """Metadata for a single registered data source."""
    name: str
    db_path: str
    organization: str
    local_key: str           # The local attribute name for the primary vehicle identifier
    global_key: str = "registration_number"
    description: str = ""
    # Runtime health metrics
    is_available: bool = True
    last_checked: Optional[str] = None
    last_response_ms: float = 0.0
    total_queries: int = 0
    failed_queries: int = 0
    avg_response_ms: float = 0.0
    _response_times: List[float] = field(default_factory=list, repr=False)

    def record_response(self, elapsed_ms: float, success: bool):
        self.total_queries += 1
        self.last_response_ms = round(elapsed_ms, 2)
        self.last_checked = datetime.now().isoformat()
        if success:
            self._response_times.append(elapsed_ms)
            if len(self._response_times) > 100:
                self._response_times = self._response_times[-100:]
            self.avg_response_ms = round(sum(self._response_times) / len(self._response_times), 2)
        else:
            self.failed_queries += 1

    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 1.0
        return round((self.total_queries - self.failed_queries) / self.total_queries, 4)

    @property
    def error_rate(self) -> float:
        return round(1.0 - self.success_rate, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "db_path": str(self.db_path),
            "organization": self.organization,
            "local_key": self.local_key,
            "global_key": self.global_key,
            "description": self.description,
            "health": {
                "is_available": self.is_available,
                "last_checked": self.last_checked,
                "last_response_ms": self.last_response_ms,
                "avg_response_ms": self.avg_response_ms,
                "total_queries": self.total_queries,
                "failed_queries": self.failed_queries,
                "success_rate": self.success_rate,
                "error_rate": self.error_rate,
            }
        }


class SourceRegistry:
    """
    Central registry of all data source connections.

    Acts as the 'Source Directory' in the Mediation architecture (IIA-1).
    Manages:
      - Source registration and metadata
      - Health monitoring via PING queries
      - Response time tracking for query optimization
      - Retry logic (up to MAX_RETRIES attempts per query)
      - Connection validation before query execution

    The registry answers: "Which sources are available right now,
    and what are their performance characteristics?"
    """

    MAX_RETRIES = 2
    HEALTH_PING_QUERY = "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"

    def __init__(self):
        self._sources: Dict[str, SourceMetadata] = {}
        self._register_all_sources()

    def _register_all_sources(self):
        """
        Register all 5 independent data sources.
        This is the 'source catalog' of the federated system.
        """
        from .schema_mapper import GAV_MAPPING
        from ..config import DB_CAPTURE, DB_INSURANCE, DB_REGISTRATION, DB_THEFT, DB_MINISTRY

        source_configs = [
            SourceMetadata(
                name="capture",
                db_path=DB_CAPTURE,
                organization="Traffic Surveillance Department",
                local_key=GAV_MAPPING["registration_number"]["capture"],
                description="ANPR camera event log. Records every vehicle detected on monitored roads.",
            ),
            SourceMetadata(
                name="insurance",
                db_path=DB_INSURANCE,
                organization="National Insurance Registry (NIR)",
                local_key=GAV_MAPPING["registration_number"]["insurance"],
                description="Vehicle insurance policy records from all registered insurers.",
            ),
            SourceMetadata(
                name="registration",
                db_path=DB_REGISTRATION,
                organization="Regional Transport Office (RTO)",
                local_key=GAV_MAPPING["registration_number"]["registration"],
                description="Official government vehicle registration and ownership records.",
            ),
            SourceMetadata(
                name="theft",
                db_path=DB_THEFT,
                organization="Police Crime Records Bureau (PCRB)",
                local_key=GAV_MAPPING["registration_number"]["theft"],
                description="Stolen, recovered, scrapped, and suspicious vehicle security records.",
            ),
            SourceMetadata(
                name="ministry",
                db_path=DB_MINISTRY,
                organization="Ministry of Transportation (Simulated)",
                local_key=GAV_MAPPING["registration_number"]["ministry"],
                description="Violation reports submitted to the Ministry (academic simulation).",
            ),
        ]

        for src in source_configs:
            self._sources[src.name] = src
        logger.info(f"SourceRegistry: registered {len(self._sources)} sources.")

    def get_source(self, name: str) -> Optional[SourceMetadata]:
        return self._sources.get(name)

    def get_all_sources(self) -> List[SourceMetadata]:
        return list(self._sources.values())

    def ping_source(self, name: str) -> Dict[str, Any]:
        """
        Ping a source with a lightweight query to check availability.
        Records response time.

        Returns a health report for this source.
        """
        src = self._sources.get(name)
        if not src:
            return {"source": name, "status": "NOT_REGISTERED"}

        start = time.perf_counter()
        try:
            conn = sqlite3.connect(src.db_path, timeout=3.0)
            conn.execute(self.HEALTH_PING_QUERY).fetchone()
            conn.close()
            elapsed = (time.perf_counter() - start) * 1000
            src.record_response(elapsed, success=True)
            src.is_available = True
            status = "ONLINE"
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            src.record_response(elapsed, success=False)
            src.is_available = False
            status = f"OFFLINE: {str(e)}"
            logger.warning(f"Source '{name}' ping failed: {e}")

        return {
            "source": name,
            "status": status,
            "response_ms": round(elapsed, 2),
            "organization": src.organization,
        }

    def ping_all_sources(self) -> List[Dict[str, Any]]:
        """Ping all registered sources and return health report."""
        return [self.ping_source(name) for name in self._sources]

    def execute_with_retry(
        self,
        source_name: str,
        query: str,
        params: tuple = (),
        retries: int = MAX_RETRIES,
    ) -> Dict[str, Any]:
        """
        Execute a query against a named source with retry logic.

        If the first attempt fails (transient error), retries up to MAX_RETRIES times.
        Records timing and success/failure for health monitoring.

        Returns:
            {
              "source": ...,
              "rows": [...],
              "elapsed_ms": ...,
              "attempts": ...,
              "success": ...,
              "error": ...,
            }
        """
        src = self._sources.get(source_name)
        if not src:
            return {"source": source_name, "rows": [], "success": False, "error": "NOT_REGISTERED", "elapsed_ms": 0, "attempts": 0}

        last_error = None
        for attempt in range(1, retries + 2):  # +2 = initial + retries
            start = time.perf_counter()
            try:
                conn = sqlite3.connect(src.db_path, timeout=5.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                elapsed = (time.perf_counter() - start) * 1000
                src.record_response(elapsed, success=True)
                src.is_available = True
                return {
                    "source": source_name,
                    "rows": rows,
                    "elapsed_ms": round(elapsed, 2),
                    "attempts": attempt,
                    "success": True,
                    "error": None,
                }
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                last_error = str(e)
                logger.warning(f"Source '{source_name}' query attempt {attempt} failed: {e}")
                if attempt <= retries:
                    time.sleep(0.05 * attempt)  # exponential backoff (simulated)

        src.record_response(elapsed, success=False)
        src.is_available = False
        return {
            "source": source_name,
            "rows": [],
            "elapsed_ms": round(elapsed, 2),
            "attempts": retries + 1,
            "success": False,
            "error": last_error,
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Aggregate health summary across all sources."""
        sources = list(self._sources.values())
        online = sum(1 for s in sources if s.is_available)
        avg_rt = (
            round(sum(s.avg_response_ms for s in sources) / len(sources), 2)
            if sources else 0
        )
        return {
            "total_sources": len(sources),
            "online": online,
            "offline": len(sources) - online,
            "avg_response_ms": avg_rt,
            "sources": [s.to_dict() for s in sources],
        }

    def get_optimal_query_order(self) -> List[str]:
        """
        Return source names sorted by average response time (fastest first).
        Used by the mediator to prioritize faster sources when possible.
        """
        sources = list(self._sources.values())
        sources.sort(key=lambda s: s.avg_response_ms if s.avg_response_ms > 0 else 999)
        return [s.name for s in sources]


# Singleton instance
_registry: Optional[SourceRegistry] = None


def get_registry() -> SourceRegistry:
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry
