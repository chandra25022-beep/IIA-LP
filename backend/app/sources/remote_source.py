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
        self._timeout = 4  # seconds — fail fast if remote node is down
        self._headers = {"ngrok-skip-browser-warning": "69420"}

        # Resilient local fallback wrapper
        self._local_fallback = None
        try:
            if db_name == "registration":
                from .registration_source import RegistrationSource
                self._local_fallback = RegistrationSource()
            elif db_name == "insurance":
                from .insurance_source import InsuranceSource
                self._local_fallback = InsuranceSource()
            elif db_name == "theft":
                from .theft_source import TheftSource
                self._local_fallback = TheftSource()
            elif db_name == "ministry":
                from .ministry_source import MinistrySource
                self._local_fallback = MinistrySource()
        except Exception as e:
            logger.debug("Local fallback init error for %s: %s", db_name, e)

    # ── Compatibility shim so Mediator can call .get_by_registration() ────────

    def get_by_registration(self, registration_number: str) -> Optional[Dict[str, Any]]:
        """Fetch single record from remote node by registration number with local fallback."""
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/vehicle/{self.db_name}/{registration_number}"
                resp = requests.get(url, timeout=self._timeout, headers=self._headers)
                is_json = "application/json" in resp.headers.get("content-type", "")
                if resp.status_code == 200 and is_json:
                    data = resp.json()
                    rec = data.get("record")
                    if rec:
                        return rec
                elif resp.status_code == 404 and is_json:
                    # Explicit JSON 404 from remote node means vehicle definitely doesn't exist there
                    return None
            except Exception as exc:
                logger.warning("RemoteSource(%s/%s) unreachable: %s. Using local fallback.", self.node_url, self.db_name, exc)

        # Fallback to local source if remote node is offline
        if self._local_fallback is not None:
            return self._local_fallback.get_by_registration(registration_number)
        return None

    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema metadata from remote node with local fallback."""
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/schema/{self.db_name}"
                resp = requests.get(url, timeout=self._timeout, headers=self._headers)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
        if self._local_fallback is not None and hasattr(self._local_fallback, "get_schema_info"):
            return self._local_fallback.get_schema_info()
        return {"source": self.db_name, "error": "Remote node unreachable", "tables": {}}

    def get_statistics(self) -> Dict[str, Any]:
        """Return stats from remote node with local fallback."""
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/statistics/{self.db_name}"
                resp = requests.get(url, timeout=self._timeout, headers=self._headers)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
        if self._local_fallback is not None and hasattr(self._local_fallback, "get_statistics"):
            return self._local_fallback.get_statistics()
        return {}

    def execute_sql(self, query: str) -> Dict[str, Any]:
        """Run a SELECT query on the remote node's database with local fallback."""
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/sql-query"
                resp = requests.post(
                    url,
                    json={"query": query, "database": self.db_name},
                    timeout=self._timeout,
                    headers=self._headers,
                )
                if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                    return resp.json()
            except Exception:
                pass

        if self._local_fallback is not None and hasattr(self._local_fallback, "execute_sql"):
            return self._local_fallback.execute_sql(query)
        return {"columns": [], "rows": [], "error": "Remote node unreachable"}

    def execute_write(self, query: str) -> Dict[str, Any]:
        """Run an INSERT/UPDATE/DELETE query on remote node with local copy synchronization."""
        remote_res = None
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/sql-write"
                resp = requests.post(
                    url,
                    json={"query": query, "database": self.db_name},
                    timeout=self._timeout,
                    headers=self._headers,
                )
                if resp.status_code == 200:
                    remote_res = resp.json()
            except Exception:
                pass

        # Also sync to local database
        if self._local_fallback is not None and hasattr(self._local_fallback, "execute_write"):
            local_res = self._local_fallback.execute_write(query)
            return remote_res or local_res

        return remote_res or {"success": False, "error": "Node unreachable"}

    def ping(self) -> bool:
        """Check if the remote node is reachable."""
        if not _REQUESTS_OK:
            return False
        try:
            resp = requests.get(f"{self.node_url}/api/node/health", timeout=2, headers=self._headers)
            return resp.status_code == 200
        except Exception:
            return False

    # ── Methods for mediator multi-record joins ──────────────────────────────

    def get_all_policies(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("policies", registration_number)

    def get_all_cases(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("cases", registration_number)

    def get_all_reports(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("reports", registration_number)

    def get_all_captures(self, registration_number: str) -> List[Dict[str, Any]]:
        return self._get_all("captures", registration_number)

    def _get_all(self, kind: str, registration_number: str) -> List[Dict[str, Any]]:
        if _REQUESTS_OK:
            try:
                url = f"{self.node_url}/api/node/vehicle/{self.db_name}/{registration_number}/{kind}"
                resp = requests.get(url, timeout=self._timeout, headers=self._headers)
                if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                    return resp.json().get("records", [])
            except Exception:
                pass
        
        # Local fallback
        if self._local_fallback is not None:
            if kind == "policies" and hasattr(self._local_fallback, "get_all_policies"):
                return self._local_fallback.get_all_policies(registration_number)
            elif kind == "cases" and hasattr(self._local_fallback, "get_all_cases"):
                return self._local_fallback.get_all_cases(registration_number)
            elif kind == "reports" and hasattr(self._local_fallback, "get_all_reports"):
                return self._local_fallback.get_all_reports(registration_number)
        return []
