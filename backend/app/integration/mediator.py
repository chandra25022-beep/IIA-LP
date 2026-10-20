"""
Mediator — Core Information Integration Engine
Implements:
1. Mediation / Federated Virtual Integration (IIA-1)
2. GAV (Global-As-View) Schema Mapping (IIA-3)
3. Week 6-8 Q-Gram Inverted Index & Prefix Filtering for Scalable Candidate Retrieval
4. Week 6-8 Data Integration Under Uncertainty:
   - Multi-Signal Feature Vector phi(r_i, r_j)
   - Logistic Sigmoid Probability Calibration P(Match | Evidence)
   - Straight-Through Processing (STP) Three-Tier Decision Policy:
     * AUTO_MERGE (p >= 0.85)
     * UNCERTAIN_REVIEW (0.50 <= p < 0.85)
     * REJECT (p < 0.50)
   - Probabilistic Truth Discovery & Conflict Resolution
5. Week 8 — Ripple Down Rules (RDR) for plate cleansing & composite attribute normalization
6. Materialized Views vs Virtual Views:
   - Virtual View:  Query all 5 nodes on-the-fly at query time (always fresh, higher latency)
   - Materialized View: Pre-joined snapshot of all 5 databases stored locally
     for instant lookup (stale until refreshed, zero latency)
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import time
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

from ..sources import CaptureSource, InsuranceSource, RegistrationSource, TheftSource, MinistrySource
from ..sources.remote_source import RemoteSource
from ..config import (
    NODE_B_URL, NODE_C_URL, DB_CAPTURE, DB_INSURANCE,
    DB_REGISTRATION, DB_THEFT, DB_MINISTRY
)
from .schema_mapper import SchemaMapper
from .entity_resolver import EntityResolver, normalize_plate, decode_rto_state
from .conflict_resolver import ConflictResolver
from .source_registry import get_registry
from .indexing import QGramInvertedIndex, compute_all_metrics
from .rdr_engine import normalize_plate_via_rdr, normalize_address_via_rdr, PLATE_RDR_ENGINE
from .uncertainty import UncertaintyEngine


class Mediator:
    """
    The Information Integration Mediator with Uncertainty & Indexing Engine.
    """

    def __init__(self):
        # Local & Remote sources
        self.capture_source = CaptureSource()
        self.insurance_source = RemoteSource(NODE_B_URL, "insurance")
        self.registration_source = RemoteSource(NODE_B_URL, "registration")
        self.theft_source = RemoteSource(NODE_C_URL, "theft")
        self.ministry_source = RemoteSource(NODE_C_URL, "ministry")

        # Modules
        self.schema_mapper = SchemaMapper()
        self.entity_resolver = EntityResolver()
        self.conflict_resolver = ConflictResolver()
        self.registry = get_registry()

        self.sources = {
            "capture": self.capture_source,
            "insurance": self.insurance_source,
            "registration": self.registration_source,
            "theft": self.theft_source,
            "ministry": self.ministry_source,
        }

        # Week 6-8 Indexing & Uncertainty Engines
        self.qgram_index = QGramInvertedIndex(q=3)
        self.uncertainty_engine = UncertaintyEngine()
        self._build_global_index()

        # ─── Materialized View Cache ──────────────────────────────────────
        # Materialized View = Pre-joined snapshot of all 5 DBs stored in memory.
        # Virtual View = On-the-fly federated query to all 5 nodes (the default).
        # The professor's lecture distinguishes these as:
        #   Virtual: always fresh, higher latency
        #   Materialized: instant lookup, stale until refreshed
        self._materialized_view: Dict[str, Dict[str, Any]] = {}
        self._materialized_view_timestamp: Optional[str] = None
        self._refresh_materialized_view()

    def _build_global_index(self):
        """
        Builds the Q-Gram Inverted Index and Prefix-Inverted Index over all 5 databases.
        Extracts plates from available local SQLite files.
        """
        db_configs = [
            ("capture", DB_CAPTURE, "plate_number", "vehicle_capture", "detected_color"),
            ("insurance", DB_INSURANCE, "registration_id", "insurance_records", "insurance_status"),
            ("registration", DB_REGISTRATION, "vehicle_reg_no", "vehicle_registration", "registered_color"),
            ("theft", DB_THEFT, "vehicle_identifier", "vehicle_security_records", "case_type"),
            ("ministry", DB_MINISTRY, "vehicle_ref", "transport_reports", "report_type"),
        ]

        indexed_count = 0
        for src_name, db_path, key_col, table_name, extra_col in db_configs:
            if not os.path.exists(db_path):
                continue
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                query = f"SELECT {key_col}, {extra_col} FROM {table_name}"
                cur.execute(query)
                for row in cur.fetchall():
                    plate = str(row[0]).strip().upper()
                    if plate:
                        rec_id = f"{src_name}_{plate}"
                        meta = {
                            "source": src_name,
                            extra_col: row[1],
                            "table": table_name
                        }
                        self.qgram_index.index_record(rec_id, plate, src_name, meta)
                        indexed_count += 1
                conn.close()
            except Exception:
                pass

        # Finalize inverted index and prefix index
        self.qgram_index.build()

    def _decompose_query(self, registration_number: str) -> Dict[str, Dict[str, Any]]:
        """Decompose global query into source-specific sub-queries via GAV."""
        sub_queries = {}
        for source_name in self.sources:
            local_key = self.schema_mapper.get_local_key(source_name, "registration_number")
            sub_queries[source_name] = {
                "source": source_name,
                "local_key": local_key,
                "value": registration_number,
                "query_template": f"SELECT * FROM <table> WHERE {local_key} = '{registration_number}'",
            }
        return sub_queries

    def _execute_sub_queries(
        self, registration_number: str, sub_queries: Dict[str, Any]
    ) -> tuple:
        """Execute sub-queries against all source connectors with latency trace."""
        results = {}
        execution_trace = []
        total_start = time.perf_counter()

        for source_name, source in self.sources.items():
            local_key = sub_queries[source_name]["local_key"]
            sql = sub_queries[source_name]["query_template"]
            step_start = time.perf_counter()
            start_ts = datetime.now().isoformat()

            try:
                record = source.get_by_registration(registration_number)
                results[source_name] = record
                elapsed_ms = round((time.perf_counter() - step_start) * 1000, 2)
                src_meta = self.registry.get_source(source_name)
                if src_meta:
                    src_meta.record_response(elapsed_ms, success=True)
                status = "HIT" if record else "MISS"
                error = None
            except Exception as e:
                results[source_name] = None
                elapsed_ms = round((time.perf_counter() - step_start) * 1000, 2)
                src_meta = self.registry.get_source(source_name)
                if src_meta:
                    src_meta.record_response(elapsed_ms, success=False)
                status = "ERROR"
                error = str(e)

            src_meta = self.registry.get_source(source_name)
            execution_trace.append({
                "step": len(execution_trace) + 1,
                "source": source_name,
                "organization": src_meta.organization if src_meta else "Unknown",
                "schema_translation": {
                    "global_attribute": "registration_number",
                    "local_attribute": local_key,
                    "mapping_type": "GAV",
                },
                "query": sql,
                "start_timestamp": start_ts,
                "elapsed_ms": elapsed_ms,
                "status": status,
                "rows_returned": 1 if results[source_name] else 0,
                "error": error,
            })

        total_elapsed_ms = round((time.perf_counter() - total_start) * 1000, 2)
        return results, execution_trace, total_elapsed_ms

    def _determine_overall_status(
        self,
        insurance_record: Optional[Dict],
        theft_record: Optional[Dict],
        registration_record: Optional[Dict],
        conflicts: List[Dict],
    ) -> str:
        """Determine overall vehicle compliance status."""
        if theft_record and theft_record.get("case_type") in ("SCRAPPED", "SHREDDED"):
            return "SCRAPPED"
        if theft_record and theft_record.get("case_type") == "STOLEN" and theft_record.get("case_status") == "OPEN":
            return "STOLEN"
        if theft_record and theft_record.get("case_type") == "SUSPICIOUS":
            return "SUSPICIOUS"
        if not insurance_record or insurance_record.get("insurance_status") == "NOT_FOUND":
            return "UNINSURED"

        ins_status = insurance_record.get("insurance_status", "")
        if ins_status == "ACTIVE":
            expiry_str = insurance_record.get("policy_expiry_date", "")
            if expiry_str:
                try:
                    expiry = datetime.fromisoformat(expiry_str).date()
                    if expiry < date.today():
                        return "INSURANCE_EXPIRED"
                except Exception:
                    pass
            if conflicts:
                return "DATA_CONFLICT"
            return "INSURED"
        elif ins_status == "EXPIRED":
            return "INSURANCE_EXPIRED"
        elif ins_status == "CANCELLED":
            return "UNINSURED"

        if conflicts:
            return "DATA_CONFLICT"
        return "UNKNOWN"

    def integrate(self, registration_number: str) -> Dict[str, Any]:
        """
        Main integration method with Uncertainty Reasoning & Q-Gram candidate resolution.
        Now also runs the RDR engine for plate cleansing, providing audit trace in response.
        """
        # --- RDR-based Plate Normalization (Week 8 Lecture) ---
        rdr_result, rdr_trace = normalize_plate_via_rdr(registration_number)
        # Fallback to the existing entity_resolver if RDR returned empty
        normalized = rdr_result if rdr_result else normalize_plate(registration_number)
        uncertainty_info: Dict[str, Any] = {
            "query_type": "EXACT_MATCH",
            "original_query": registration_number,
            "normalized_query": normalized,
            "calibrated_probability": 1.0,
            "decision_tier": "AUTO_MERGE",
            "uncertainty_routing": "Deterministic straight-through processing.",
            "candidate_hypotheses": [],
            "feature_attribution": {},
        }

        # Step 1: Query decomposition & Execution
        sub_queries = self._decompose_query(normalized)
        raw_results, execution_trace, total_elapsed_ms = self._execute_sub_queries(normalized, sub_queries)

        capture = raw_results.get("capture")
        insurance = raw_results.get("insurance")
        registration = raw_results.get("registration")
        theft = raw_results.get("theft")
        ministry = raw_results.get("ministry")

        has_any_data = any([capture, insurance, registration, theft, ministry])

        # Step 2: If exact match failed, invoke Q-Gram Prefix Index & Uncertainty Engine
        if not has_any_data:
            candidates = self.qgram_index.search_candidates(normalized, method="prefix_index", max_candidates=5)
            if candidates:
                u_eval = self.uncertainty_engine.evaluate_match_under_uncertainty(
                    normalized, candidates, sensor_confidence=0.90
                )
                best_cand = u_eval.get("best_match")
                uncertainty_info["candidate_hypotheses"] = u_eval.get("candidate_hypotheses", [])
                uncertainty_info["thresholds"] = u_eval.get("thresholds", {})

                if best_cand and u_eval["overall_decision"] in ("AUTO_MERGE", "UNCERTAIN_REVIEW"):
                    matched_plate = best_cand["plate"]
                    prob = best_cand["match_probability"]
                    tier = best_cand["decision_tier"]

                    uncertainty_info.update({
                        "query_type": "PROBABILISTIC_INDEX_MATCH",
                        "matched_plate": matched_plate,
                        "calibrated_probability": prob,
                        "decision_tier": tier,
                        "tier_description": best_cand["tier_description"],
                        "feature_attribution": best_cand["features"],
                        "uncertainty_routing": (
                            f"Automated STP merge with probability P={prob:.2f}." if tier == "AUTO_MERGE"
                            else f"Ambiguous match P={prob:.2f} — candidate presented for human review."
                        )
                    })

                    # Re-run federation for the best candidate
                    sub_queries = self._decompose_query(matched_plate)
                    raw_results, execution_trace, total_elapsed_ms = self._execute_sub_queries(matched_plate, sub_queries)
                    capture = raw_results.get("capture")
                    insurance = raw_results.get("insurance")
                    registration = raw_results.get("registration")
                    theft = raw_results.get("theft")
                    ministry = raw_results.get("ministry")
                    normalized = matched_plate

        # Step 3: Conflict detection & Probabilistic Truth Discovery
        conflict_report = self.conflict_resolver.resolve_all_conflicts(
            capture, insurance, registration, theft
        )

        # Probabilistic truth discovery for color conflict
        if capture and registration and capture.get("detected_color") and registration.get("registered_color"):
            color_conf = self.uncertainty_engine.resolve_conflicts_probabilistically(
                "color",
                {
                    "capture": capture.get("detected_color"),
                    "registration": registration.get("registered_color"),
                },
                camera_confidence=capture.get("detection_confidence", 0.90) or 0.90
            )
            uncertainty_info["probabilistic_color_resolution"] = color_conf

        data_availability = {
            "capture": capture is not None,
            "insurance": insurance is not None,
            "registration": registration is not None,
            "theft": theft is not None,
            "ministry": ministry is not None,
        }

        # Step 4: Determine overall status
        overall_status = self._determine_overall_status(
            insurance, theft, registration, conflict_report["conflicts"]
        )

        # If uncertain review tier was selected, flag the overall status
        if uncertainty_info.get("decision_tier") == "UNCERTAIN_REVIEW":
            overall_status = "UNCERTAIN_MATCH_REVIEW"

        decoded_origin = decode_rto_state(normalized)

        unified_view = {
            "registration_number": normalized,
            "query_timestamp": datetime.now().isoformat(),
            "decoded_origin": decoded_origin,
            "all_records_empty": not (capture or insurance or registration or theft or ministry),
            "uncertainty_evaluation": uncertainty_info,

            "vehicle": {
                "make": registration.get("manufacturer") if registration else None,
                "model": registration.get("model_name") if registration else None,
                "vehicle_class": registration.get("vehicle_class") if registration else None,
                "registered_color": registration.get("registered_color") if registration else None,
                "fuel_type": registration.get("fuel_type") if registration else None,
                "engine_number": registration.get("engine_number") if registration else None,
                "chassis_number": registration.get("chassis_number") if registration else None,
                "seating_capacity": registration.get("seating_capacity") if registration else None,
            },

            "last_capture": {
                "detected_vehicle_type": capture.get("detected_vehicle_type") if capture else None,
                "detected_color": capture.get("detected_color") if capture else None,
                "capture_timestamp": capture.get("capture_timestamp") if capture else None,
                "capture_location": capture.get("capture_location") if capture else None,
                "detection_confidence": capture.get("detection_confidence") if capture else None,
                "ocr_confidence": capture.get("ocr_confidence") if capture else None,
            },

            "registration": {
                "owner_name": registration.get("owner_name") if registration else None,
                "registration_date": registration.get("registration_date") if registration else None,
                "registration_status": registration.get("registration_status") if registration else None,
                "rto_office": registration.get("rto_office") if registration else None,
                "fitness_valid_until": registration.get("fitness_valid_until") if registration else None,
                "tax_valid_until": registration.get("tax_valid_until") if registration else None,
            },

            "insurance": {
                "insurer_name": insurance.get("insurer_name") if insurance else None,
                "policy_number": insurance.get("policy_number") if insurance else None,
                "policy_start_date": insurance.get("policy_start_date") if insurance else None,
                "policy_expiry_date": insurance.get("policy_expiry_date") if insurance else None,
                "insurance_status": insurance.get("insurance_status") if insurance else "NOT_FOUND",
                "coverage_type": insurance.get("coverage_type") if insurance else None,
                "vehicle_category": insurance.get("vehicle_category") if insurance else None,
            },

            "security": {
                "case_type": theft.get("case_type") if theft else None,
                "case_status": theft.get("case_status") if theft else None,
                "reported_date": theft.get("reported_date") if theft else None,
                "police_reference": theft.get("police_reference") if theft else None,
                "shredding_status": theft.get("shredding_status") if theft else "NOT_SCRAPPED",
                "fir_number": theft.get("fir_number") if theft else None,
            },

            "ministry": {
                "report_type": ministry.get("report_type") if ministry else None,
                "report_date": ministry.get("report_date") if ministry else None,
                "severity": ministry.get("severity") if ministry else None,
                "report_status": ministry.get("report_status") if ministry else "NOT_REPORTED",
                "action_taken": ministry.get("action_taken") if ministry else None,
            },

            "integration_metadata": {
                "sub_queries": sub_queries,
                "data_availability": data_availability,
                "sources_queried": len(self.sources),
                "sources_with_data": sum(1 for v in data_availability.values() if v),
                "schema_mapping_used": self.schema_mapper.get_all_source_keys("registration_number"),
                "execution_trace": execution_trace,
                "total_federation_ms": total_elapsed_ms,
                "architecture": "Mediation / Federated Virtual Integration (IIA-1)",
                "mapping_paradigm": "Global-As-View (GAV) -- IIA-3",
                "indexing_framework": "Q-Gram Inverted Index & Prefix Filtering [Bayardo et al, WWW 07]",
                "rdr_normalization": {
                    "engine": "Single-Classification Ripple Down Rules (Week 8 Lecture)",
                    "input": registration_number,
                    "output": normalized,
                    "rules_traversed": len(rdr_trace),
                    "audit_trace": rdr_trace,
                },
                "view_type": "Virtual View (on-the-fly federated query)",
                "query_timestamp": datetime.now().isoformat(),
            },

            "conflicts": conflict_report,
            "overall_status": overall_status,
            "requires_ministry_report": overall_status in (
                "UNINSURED", "INSURANCE_EXPIRED", "STOLEN", "SUSPICIOUS", "DATA_CONFLICT"
            ),
        }

        return unified_view

    def get_statistics(self) -> Dict[str, Any]:
        """Aggregate statistics from all sources for the dashboard."""
        stats = {}
        for name, source in self.sources.items():
            try:
                stats[name] = source.get_statistics()
            except Exception:
                stats[name] = {}
        return stats

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information from all sources for the Data Sources page."""
        schemas = {}
        for name, source in self.sources.items():
            try:
                schemas[name] = source.get_schema_info()
            except Exception:
                schemas[name] = {"source": name, "error": "unavailable"}
        return schemas

    def get_all_captures(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.capture_source.get_all_captures(normalized)

    def get_all_policies(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.insurance_source.get_all_policies(normalized)

    def get_all_security_cases(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.theft_source.get_all_cases(normalized)

    def get_all_ministry_reports(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.ministry_source.get_all_reports(normalized)

    def create_ministry_report(
        self,
        vehicle_ref: str,
        report_type: str,
        reason: str,
        severity: str = "HIGH",
        submitted_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        normalized = normalize_plate(vehicle_ref)
        report_id = self.ministry_source.create_report(
            normalized, report_type, reason, severity, submitted_by
        )
        return {
            "report_id": report_id,
            "vehicle_ref": normalized,
            "report_type": report_type,
            "reason": reason,
            "severity": severity,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
        }

    def get_all_pending_reports(self) -> List[Dict[str, Any]]:
        return self.ministry_source.get_all_pending_reports()

    def get_all_reports_paginated(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        return self.ministry_source.get_all_reports_paginated(skip, limit)

    # ─── MATERIALIZED VIEW METHODS ────────────────────────────────────────────
    # IIA Lecture: Materialized View vs Virtual View
    # Materialized: snapshot pre-joined from all 5 DBs, stored in local dict
    # Virtual: on-the-fly query federation (used by integrate() above)

    def _refresh_materialized_view(self):
        """
        Refresh the Materialized View by pulling ALL records from ALL 5 local databases
        and pre-joining them on the global key (registration_number via GAV mapping).
        This is the "materialized" counterpart to integrate() which is "virtual".
        """
        logger.info("Refreshing Materialized View from all 5 databases...")
        mv: Dict[str, Dict[str, Any]] = {}

        db_configs = [
            ("capture", DB_CAPTURE, "plate_number", "vehicle_capture"),
            ("insurance", DB_INSURANCE, "registration_id", "insurance_records"),
            ("registration", DB_REGISTRATION, "vehicle_reg_no", "vehicle_registration"),
            ("theft", DB_THEFT, "vehicle_identifier", "vehicle_security_records"),
            ("ministry", DB_MINISTRY, "vehicle_ref", "transport_reports"),
        ]

        for src_name, db_path, key_col, table in db_configs:
            if not os.path.exists(db_path):
                continue
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                conn.close()
                for row in rows:
                    record = dict(row)
                    plate = normalize_plate(str(record.get(key_col, "")))
                    if not plate:
                        continue
                    if plate not in mv:
                        mv[plate] = {
                            "registration_number": plate,
                            "capture": None,
                            "insurance": None,
                            "registration": None,
                            "theft": None,
                            "ministry": None,
                        }
                    mv[plate][src_name] = record
            except Exception as e:
                logger.warning(f"Materialized view: failed to load {src_name}: {e}")

        self._materialized_view = mv
        self._materialized_view_timestamp = datetime.now().isoformat()
        logger.info(f"Materialized View refreshed: {len(mv)} unique plates.")

    def get_materialized_view(self, registration_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the Materialized View.
        If registration_number is given, look up a single plate.
        Otherwise return the full materialized snapshot.
        """
        if registration_number:
            norm = normalize_plate(registration_number)
            entry = self._materialized_view.get(norm)
            return {
                "view_type": "Materialized View (pre-joined snapshot)",
                "last_refreshed": self._materialized_view_timestamp,
                "total_plates": len(self._materialized_view),
                "result": entry,
            }
        return {
            "view_type": "Materialized View (full snapshot)",
            "last_refreshed": self._materialized_view_timestamp,
            "total_plates": len(self._materialized_view),
            "plates": list(self._materialized_view.keys()),
        }

    def refresh_materialized_view(self) -> Dict[str, Any]:
        """Force-refresh the materialized view and return metadata."""
        self._refresh_materialized_view()
        return {
            "status": "refreshed",
            "total_plates": len(self._materialized_view),
            "timestamp": self._materialized_view_timestamp,
        }
