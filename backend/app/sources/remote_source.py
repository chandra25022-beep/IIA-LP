"""
Remote Source Connector — HTTP Wrapper for Distributed Nodes

This implements the "Wrappers" concept from IIA-1 but over HTTP instead of SQLite.
The Mediator uses this exactly the same way as a local source — it doesn't know
whether data comes from a local file or a remote node on the LAN.

Laptop B hosts: insurance + registration  (NODE_B_URL)
Laptop C hosts: theft + ministry          (NODE_C_URL)
"""
import logging
from typing import Any, Dict, List, Optional

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

logger = logging.getLogger(__name__)


class RemoteSource:
    """
    HTTP wrapper for a remote node database.
    Calls the node's REST API to query data — transparent to the Mediator.
    """

    def __init__(self, node_url: str, db_name: str):
        """
        node_url : base URL of the remote node, e.g. 'http://192.168.1.101:8001'
        db_name  : one of 'insurance', 'registration', 'theft', 'ministry'
        """
        self.node_url = node_url.rstrip("/")
        self.db_name = db_name
        self.source_name = db_name
        self._timeout = 5  # seconds — fail fast if node is down
        self._headers = {"ngrok-skip-browser-warning": "69420"}

    # ── Compatibility shim so Mediator can call .get_by_registration() ────────

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """Fetch single record from remote node by registration number."""
        if not _REQUESTS_OK:
            logger.error("'requests' library not installed — cannot reach remote node")
            return None
        try:
            url = f"{self.node_url}/api/node/vehicle/{self.db_name}/{registration_number}"
            resp = requests.get(url, timeout=self._timeout, headers=self._headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("record")  # may be None if not found
            if resp.status_code == 404:
                return None
            logger.warning("Remote node %s returned %s for %s", self.node_url, resp.status_code, self.db_name)
            return None
        except Exception as exc:
            logger.warning("RemoteSource(%s/%s) unreachable: %s", self.node_url, self.db_name, exc)
            return None

    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema metadata from remote node."""
        if not _REQUESTS_OK:
            return {"source": self.db_name, "error": "requests not installed", "tables": {}}
        try:
            url = f"{self.node_url}/api/node/schema/{self.db_name}"
            resp = requests.get(url, timeout=self._timeout, headers=self._headers)
            if resp.status_code == 200:
                return resp.json()
            return {"source": self.db_name, "error": f"HTTP {resp.status_code}", "tables": {}}
        except Exception as exc:
            return {"source": self.db_name, "error": str(exc), "tables": {}}

    def get_statistics(self) -> Dict[str, Any]:
        """Return stats from remote node."""
        if not _REQUESTS_OK:
            return {}
        try:
            url = f"{self.node_url}/api/node/statistics/{self.db_name}"
            resp = requests.get(url, timeout=self._timeout, headers=self._headers)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}

    def execute_sql(self, query: str) -> Dict[str, Any]:
        """Run a SELECT query on the remote node's database."""
        if not _REQUESTS_OK:
            return {"columns": [], "rows": [], "error": "requests not installed"}
        try:
            url = f"{self.node_url}/api/node/sql-query"
            resp = requests.post(
                url,
                json={"query": query, "database": self.db_name},
                timeout=self._timeout,
                headers=self._headers,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"columns": [], "rows": [], "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as exc:
            return {"columns": [], "rows": [], "error": str(exc)}

    def execute_write(self, query: str) -> Dict[str, Any]:
        """Run an INSERT/UPDATE/DELETE query on the remote node's database."""
        if not _REQUESTS_OK:
            return {"success": False, "error": "requests not installed"}
        try:
            url = f"{self.node_url}/api/node/sql-write"
            resp = requests.post(
                url,
                json={"query": query, "database": self.db_name},
                timeout=self._timeout,
                headers=self._headers,
            )
            if resp.status_code == 200:
                return resp.json()
            detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            return {"success": False, "error": detail}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def ping(self) -> bool:
        """Check if the remote node is reachable."""
        if not _REQUESTS_OK:
            return False
        try:
            resp = requests.get(f"{self.node_url}/api/node/health", timeout=2, headers=self._headers)
            return resp.status_code == 200
        except Exception:
            return False

    # ── Stubs for mediator methods that loop over all sources ──────────────────

    def get_all_policies(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("policies", registration_number)

    def get_all_cases(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("cases", registration_number)

    def get_all_reports(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("reports", registration_number)

    def get_all_captures(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("captures", registration_number)

    def _get_all(self, kind: str, registration_number: str) -> List[Dict[str, Any]]:
        if not _REQUESTS_OK:
            return []
        try:
            url = f"{self.node_url}/api/node/vehicle/{self.db_name}/{registration_number}/{kind}"
            resp = requests.get(url, timeout=self._timeout, headers=self._headers)
            if resp.status_code == 200:
                return resp.json().get("records", [])
            return []
        except Exception:
            return []
