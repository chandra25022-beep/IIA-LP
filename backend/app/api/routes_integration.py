"""
Integration View API Routes

These routes expose the Information Integration layer itself:
- Schema information from all sources
- GAV schema mappings
- Schema matching results
- Dashboard statistics
- SQL Query execution across all 5 DBs
  * SELECT: federated across all nodes
  * INSERT/UPDATE/DELETE: local DBs only (capture on master)
  * Remote writes must be done on the owning laptop
"""
import sqlite3
import requests
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..integration.mediator import Mediator
from ..integration.schema_mapper import SchemaMapper, GAV_MAPPING
from ..integration.schema_matcher import SchemaMatcher, sample_column_values, compute_multisignal_similarity
from ..integration.source_registry import get_registry
from ..config import (
    DB_CAPTURE, DB_INSURANCE, DB_REGISTRATION, DB_THEFT, DB_MINISTRY,
    LOCAL_DATABASES, DATABASE_NODE_MAP, NODE_URLS
)

router = APIRouter(prefix="/api", tags=["integration"])

_mediator: Optional[Mediator] = None
_schema_mapper = SchemaMapper()
_schema_matcher = SchemaMatcher()

# ─── SQL Query Models ────────────────────────────────────────────────────────

class SqlQueryRequest(BaseModel):
    query: str
    database: str = "all"   # all | capture | insurance | registration | theft | ministry

class SqlWriteRequest(BaseModel):
    query: str
    database: str  # capture | insurance | registration | theft | ministry (not 'all')

def get_mediator() -> Mediator:
    global _mediator
    if _mediator is None:
        _mediator = Mediator()
    return _mediator


@router.get("/data-sources")
async def get_data_sources():
    """
    Get schema information from all 5 independent data sources.
    Used for the Data Sources page in the frontend.
    """
    mediator = get_mediator()
    schema_info = mediator.get_schema_info()

    # Enrich with schema mapping information
    sources_info = []
    source_descriptions = {
        "capture": {
            "purpose": "Traffic surveillance ANPR camera system. Records vehicles detected on the road.",
            "local_key": "plate_number",
            "global_key": "registration_number",
            "organization": "Traffic Surveillance Department",
        },
        "insurance": {
            "purpose": "Insurance company policy management system. Stores vehicle insurance records.",
            "local_key": "registration_id",
            "global_key": "registration_number",
            "organization": "National Insurance Registry",
        },
        "registration": {
            "purpose": "Government RTO vehicle registration system. Official vehicle registration records.",
            "local_key": "vehicle_reg_no",
            "global_key": "registration_number",
            "organization": "Regional Transport Office (RTO)",
        },
        "theft": {
            "purpose": "Police department vehicle security records. Stolen, recovered, scrapped vehicles.",
            "local_key": "vehicle_identifier",
            "global_key": "registration_number",
            "organization": "Police Crime Records Bureau",
        },
        "ministry": {
            "purpose": "Ministry of Transportation reporting system (SIMULATED ACADEMIC SYSTEM).",
            "local_key": "vehicle_ref",
            "global_key": "registration_number",
            "organization": "Ministry of Transportation (Simulated)",
        },
    }

    for source_name, info in schema_info.items():
        desc = source_descriptions.get(source_name, {})
        sources_info.append({
            **info,
            **desc,
            "schema_mapping": {
                "local_key": desc.get("local_key"),
                "global_key": "registration_number",
                "mapping_type": "GAV (Global-As-View)",
            },
        })

    return {"sources": sources_info, "count": len(sources_info)}


@router.get("/integration/schema")
async def get_integration_schema():
    """
    Get the complete GAV schema mapping and multi-signal matching results.

    Runs instance-based matching using real sampled data from each source DB.
    This demonstrates IIA-3 'Instance-based: Attributes match if they have
    similar instances or value distributions'.
    """
    # GAV mapping table
    mapping_table = _schema_mapper.get_full_mapping_table()

    source_key_attrs = {
        "capture": ["plate_number", "detected_vehicle_type", "detected_color", "capture_timestamp",
                    "capture_location", "detection_confidence", "ocr_confidence"],
        "insurance": ["registration_id", "insurer_name", "policy_number", "policy_start_date",
                      "policy_expiry_date", "insurance_status", "vehicle_category"],
        "registration": ["vehicle_reg_no", "owner_name", "registration_date", "manufacturer",
                         "model_name", "vehicle_class", "registered_color", "fuel_type", "registration_status"],
        "theft": ["vehicle_identifier", "case_type", "case_status", "reported_date",
                  "police_reference", "shredding_status"],
        "ministry": ["vehicle_ref", "report_type", "report_date", "reason", "severity", "report_status"],
    }

    # Sample real instance data for instance-based matching (IIA-3)
    db_configs = {
        "capture":      (DB_CAPTURE,      "vehicle_capture",          "plate_number"),
        "insurance":    (DB_INSURANCE,    "insurance_records",         "registration_id"),
        "registration": (DB_REGISTRATION, "vehicle_registration",      "vehicle_reg_no"),
        "theft":        (DB_THEFT,        "vehicle_security_records",  "vehicle_identifier"),
        "ministry":     (DB_MINISTRY,     "transport_reports",         "vehicle_ref"),
    }
    instance_data: dict = {}
    for src, (db_path, table, key_col) in db_configs.items():
        instance_data[src] = {key_col: sample_column_values(db_path, table, key_col, limit=50)}

    # Run multi-signal matching with real instance data
    key_correspondences = _schema_matcher.find_key_correspondences(source_key_attrs, instance_data=instance_data)
    all_correspondences = _schema_matcher.match_all_sources(source_key_attrs)

    return {
        "gav_mapping": mapping_table,
        "all_source_keys": _schema_mapper.get_all_source_keys("registration_number"),
        "key_correspondences": key_correspondences,
        "all_correspondences": [c for c in all_correspondences if c["similarity"] >= 0.5],
        "integration_approach": "Mediation / Federated Virtual Integration (IIA-1)",
        "schema_mapping_approach": "Global-As-View (GAV) (IIA-3)",
        "matching_model": "Multi-signal: Score = 0.35*N + 0.25*I + 0.20*S + 0.10*C + 0.10*O (IIA-3)",
        "instance_data_sampled": {src: len(list(v.values())[0]) for src, v in instance_data.items()},
    }


@router.get("/statistics")
async def get_statistics():
    """Dashboard statistics aggregated from all sources."""
    mediator = get_mediator()
    raw_stats = mediator.get_statistics()

    # Pull structured values from each source
    capture_stats = raw_stats.get("capture", {})
    insurance_stats = raw_stats.get("insurance", {})
    registration_stats = raw_stats.get("registration", {})
    theft_stats = raw_stats.get("theft", {})
    ministry_stats = raw_stats.get("ministry", {})

    return {
        "total_vehicles_captured": capture_stats.get("total", 0),
        "unique_plates_captured": capture_stats.get("unique_plates", 0),
        "total_insurance_records": insurance_stats.get("total", 0),
        "insured_active": insurance_stats.get("active", 0),
        "insurance_expired": insurance_stats.get("expired", 0),
        "total_registered": registration_stats.get("total", 0),
        "total_theft_cases": theft_stats.get("total", 0),
        "stolen_vehicles": theft_stats.get("stolen", 0),
        "scrapped_vehicles": theft_stats.get("scrapped", 0),
        "suspicious_vehicles": theft_stats.get("suspicious", 0),
        "total_reports": ministry_stats.get("total", 0),
        "pending_reports": ministry_stats.get("pending", 0),
        "resolved_reports": ministry_stats.get("resolved", 0),
        "sources": {
            "capture": capture_stats,
            "insurance": insurance_stats,
            "registration": registration_stats,
            "theft": theft_stats,
            "ministry": ministry_stats,
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "IIA Vehicle Integration System",
        "version": "1.0.0",
    }


@router.get("/sources/health")
async def get_sources_health():
    """
    Source health dashboard.

    Pings all 5 data sources and returns their health status,
    availability, response time, and query statistics.

    IIA-3 'Data Source Selection' slide:
      'Must evaluate data sources to know which to select:
       Is it complete? Is it correct? Is it up to date?'

    IIA-4 Wrappers slide:
      'Wrappers communicate with data sources, sending queries,
       converting replies to a format the query processor can use.'

    Returns:
      - Online/offline status for each source
      - Response time (ms) -- query latency per source
      - Success rate and error rate
      - Optimal query order (fastest first)
    """
    registry = get_registry()
    ping_results = registry.ping_all_sources()
    summary = registry.get_health_summary()
    optimal_order = registry.get_optimal_query_order()

    return {
        "summary": summary,
        "ping_results": ping_results,
        "optimal_query_order": optimal_order,
        "description": (
            "Source health monitoring implements the IIA-1 source registry concept. "
            "The mediator queries fastest available sources first to minimize latency."
        ),
    }


@router.get("/integration/instance-matching")
async def get_instance_based_matching():
    """
    Instance-based schema matching with real data samples.

    IIA-3: 'Data instances -- Attributes match if they have
    similar instances or value distributions'
    IIA-3: 'Instance-based: Distribution similarity (e.g., KL divergence)'

    This endpoint:
    1. Samples actual data values from each source DB
    2. Computes value overlap between attribute pairs
    3. Shows how the I (instance) signal dramatically boosts scores
       for 'plate_number' vs 'vehicle_ref' etc.

    Without instance data: plate_number vs vehicle_ref linguistic score ~0.18
    With instance data:    plate_number vs vehicle_ref total score is much higher
                           because they share the same 10 vehicle plate values.
    """
    db_configs = {
        "capture":      (DB_CAPTURE,      "vehicle_capture",          "plate_number"),
        "insurance":    (DB_INSURANCE,    "insurance_records",         "registration_id"),
        "registration": (DB_REGISTRATION, "vehicle_registration",      "vehicle_reg_no"),
        "theft":        (DB_THEFT,        "vehicle_security_records",  "vehicle_identifier"),
        "ministry":     (DB_MINISTRY,     "transport_reports",         "vehicle_ref"),
    }

    # Sample real data from each source's key column
    sampled: dict = {}
    for src, (db_path, table, key_col) in db_configs.items():
        values = sample_column_values(db_path, table, key_col, limit=50)
        sampled[src] = {"column": key_col, "values": values, "count": len(values)}

    # Run pairwise instance-based matching on the 5 identity columns
    key_pairs = []
    src_list = list(db_configs.keys())
    for i in range(len(src_list)):
        for j in range(i + 1, len(src_list)):
            s1, s2 = src_list[i], src_list[j]
            col1 = db_configs[s1][2]
            col2 = db_configs[s2][2]
            vals1 = sampled[s1]["values"]
            vals2 = sampled[s2]["values"]

            result = compute_multisignal_similarity(
                col1, col2,
                instance_values1=vals1,
                instance_values2=vals2,
            )

            # Also compute linguistic-only for comparison
            from ..integration.schema_matcher import compute_attribute_similarity
            ling_only = compute_attribute_similarity(col1, col2)

            key_pairs.append({
                "source1": s1, "col1": col1,
                "source2": s2, "col2": col2,
                "score_with_instances": result["score"],
                "score_linguistic_only": ling_only,
                "improvement": round(result["score"] - ling_only, 4),
                "signals": result["signals"],
                "match_type": result["match_type"],
                "shared_values": list(set(vals1) & set(v.strip().upper() for v in vals2))[:5],
            })

    return {
        "description": (
            "Instance-based matching (IIA-3): Attributes from different sources are matched "
            "by comparing their actual data values. High overlap proves they represent the same concept "
            "even when their names differ greatly (e.g., plate_number vs vehicle_ref)."
        ),
        "sampled_data": sampled,
        "pairwise_matching": sorted(key_pairs, key=lambda x: x["score_with_instances"], reverse=True),
        "algorithm": "Jaccard overlap on sampled value sets as proxy for distribution similarity",
        "formula": "I_sim = |values1 intersect values2| / |values1 union values2|",
    }


@router.get("/demo-vehicles")
async def get_demo_vehicles():
    """Return the list of pre-seeded demo vehicles for the demo page."""
    return {
        "demo_vehicles": [
            {"plate": "UP32AB1234", "expected_status": "INSURED", "description": "Valid, insured vehicle"},
            {"plate": "UP32CD5678", "expected_status": "INSURANCE_EXPIRED", "description": "Insurance expired"},
            {"plate": "MH02EF9012", "expected_status": "UNINSURED", "description": "No insurance record"},
            {"plate": "DL01GH3456", "expected_status": "STOLEN", "description": "Reported stolen"},
            {"plate": "KA03IJ7890", "expected_status": "SCRAPPED", "description": "Vehicle scrapped"},
            {"plate": "TN05KL1122", "expected_status": "DATA_CONFLICT", "description": "Color data conflict"},
            {"plate": "GJ06MN3344", "expected_status": "UNINSURED", "description": "Partial info — no insurance"},
            {"plate": "RJ07OP5566", "expected_status": "INSURED", "description": "Fuzzy OCR match demo"},
            {"plate": "HR26PQ7788", "expected_status": "SUSPICIOUS", "description": "Suspicious vehicle"},
            {"plate": "PB10RS9900", "expected_status": "INSURANCE_EXPIRED", "description": "Cancelled policy"},
        ]
    }


# ─── SQL Query Endpoints ─────────────────────────────────────────────────────

# Map of database name -> file path (local SQLite files — master owns capture only)
_DB_MAP: Dict[str, str] = {
    "capture":      DB_CAPTURE,
    "insurance":    DB_INSURANCE,
    "registration": DB_REGISTRATION,
    "theft":        DB_THEFT,
    "ministry":     DB_MINISTRY,
}

# DB ownership labels for UI display
DB_OWNERSHIP = {
    "capture":      {"owner": "Master Laptop",  "node": "master", "writable_here": True},
    "insurance":    {"owner": "Laptop B",        "node": "node_b", "writable_here": False},
    "registration": {"owner": "Laptop B",        "node": "node_b", "writable_here": False},
    "theft":        {"owner": "Laptop C",        "node": "node_c", "writable_here": False},
    "ministry":     {"owner": "Laptop C",        "node": "node_c", "writable_here": False},
}


def _run_select(db_path: str, query: str) -> Dict[str, Any]:
    """Execute a SELECT query on a local SQLite db and return columns + rows."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"columns": columns, "rows": rows, "error": None}
    except Exception as e:
        return {"columns": [], "rows": [], "error": str(e)}


def _run_select_remote(node_url: str, query: str, db_name: str) -> Dict[str, Any]:
    """Forward a SELECT query to a remote node."""
    try:
        resp = requests.post(
            f"{node_url}/api/node/sql-query",
            json={"query": query, "database": db_name},
            timeout=5,
            headers={"ngrok-skip-browser-warning": "69420"},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"columns": [], "rows": [], "error": f"Node returned HTTP {resp.status_code}"}
    except Exception as e:
        return {"columns": [], "rows": [], "error": f"Node unreachable: {e}"}


def _run_write_local(db_path: str, query: str) -> Dict[str, Any]:
    """Execute an INSERT/UPDATE/DELETE on a local SQLite db."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(query)
        conn.commit()
        affected = cursor.rowcount
        lastrowid = cursor.lastrowid
        conn.close()
        return {"success": True, "affected_rows": affected, "last_insert_id": lastrowid, "error": None}
    except Exception as e:
        return {"success": False, "affected_rows": 0, "last_insert_id": None, "error": str(e)}


def _is_safe_query(query: str) -> bool:
    """Return True only if query starts with SELECT."""
    stripped = query.strip().lstrip("(").upper()
    return stripped.startswith("SELECT") or stripped.startswith("WITH")


def _is_write_query(query: str) -> bool:
    """Return True for INSERT / UPDATE / DELETE / REPLACE queries."""
    stripped = query.strip().lstrip("(").upper()
    return any(stripped.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "REPLACE"))


@router.post("/sql-query")
async def run_sql_query(request: SqlQueryRequest):
    """
    Execute a SQL SELECT query against one or all of the 5 databases.
    SELECT queries are federated: local DBs run directly, remote DBs are
    forwarded to the correct node via HTTP.

    Body:
        { "query": "SELECT * FROM vehicle_capture LIMIT 10", "database": "capture" }

    database can be: all | capture | insurance | registration | theft | ministry
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not _is_safe_query(query):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed here. Use /api/sql-write for INSERT/UPDATE/DELETE."
        )

    target = request.database.lower()

    def _run_db(db_name: str) -> Dict[str, Any]:
        node_key = DATABASE_NODE_MAP.get(db_name, "master")
        if node_key == "master":
            result = _run_select(_DB_MAP[db_name], query)
        else:
            node_url = NODE_URLS[node_key]
            result = _run_select_remote(node_url, query, db_name)
        return {
            "database": db_name,
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
            "row_count": len(result.get("rows", [])),
            "error": result.get("error"),
        }

    if target == "all":
        all_results = [_run_db(db_name) for db_name in _DB_MAP]
        return {
            "query": query,
            "database": "all",
            "results": all_results,
            "total_rows": sum(r["row_count"] for r in all_results),
        }

    if target not in _DB_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown database '{target}'. Choose: all, {', '.join(_DB_MAP.keys())}"
        )

    result_item = _run_db(target)
    return {
        "query": query,
        "database": target,
        "results": [result_item],
        "total_rows": result_item["row_count"],
    }


@router.post("/sql-write")
async def run_sql_write(request: SqlWriteRequest):
    """
    Execute an INSERT / UPDATE / DELETE query.

    ISOLATION RULE — each database can only be written from the laptop that owns it:
      Master  → capture
      Laptop B → insurance, registration
      Laptop C → theft, ministry

    If this master receives a write request for a remote DB, it forwards
    the query to the correct node backend via HTTP.

    Body:
        { "query": "INSERT INTO vehicle_capture ...", "database": "capture" }
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not _is_write_query(query):
        raise HTTPException(
            status_code=400,
            detail="Only INSERT/UPDATE/DELETE queries are allowed here. Use /api/sql-query for SELECT."
        )

    target = request.database.lower()
    if target not in _DB_MAP or target == "all":
        raise HTTPException(
            status_code=400,
            detail=f"Specify a single database: {', '.join(_DB_MAP.keys())}"
        )

    node_key = DATABASE_NODE_MAP.get(target, "master")
    ownership = DB_OWNERSHIP.get(target, {})

    if node_key == "master":
        # This DB is local — write directly
        result = _run_write_local(_DB_MAP[target], query)
        if result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return {
            "success": True,
            "database": target,
            "owner": "Master Laptop",
            "affected_rows": result["affected_rows"],
            "last_insert_id": result["last_insert_id"],
        }
    else:
        # Forward to remote node
        node_url = NODE_URLS[node_key]
        try:
            resp = requests.post(
                f"{node_url}/api/node/sql-write",
                json={"query": query, "database": target},
                timeout=5,
                headers={"ngrok-skip-browser-warning": "69420"},
            )
            if resp.status_code == 200:
                data = resp.json()
                data["forwarded_to"] = node_url
                data["owner"] = ownership.get("owner", node_key)
                return data
            detail = resp.json().get("detail", resp.text) if resp.content else resp.text
            raise HTTPException(status_code=resp.status_code, detail=f"Node error: {detail}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Cannot reach {ownership.get('owner', node_key)} node at {node_url}. "
                    f"Make sure that laptop is running its node backend. Error: {e}"
                )
            )


@router.get("/sql-write/ownership")
async def get_db_ownership():
    """
    Return which laptop owns each database.
    Used by the frontend to show lock icons and ownership labels.
    """
    return {
        "databases": DB_OWNERSHIP,
        "description": (
            "Each database can only be written from the laptop that owns it. "
            "The master backend forwards write requests to remote nodes automatically."
        ),
    }



@router.get("/sql-query/tables")
async def get_all_table_schemas():
    """
    Return the full schema (tables + columns) of all 5 databases.
    Used by the SQL Query page to show available tables as hints.
    """
    schema: Dict[str, Any] = {}

    for db_name, db_path in _DB_MAP.items():
        try:
            conn = sqlite3.connect(db_path)
            tables_cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in tables_cursor.fetchall()]
            db_schema: Dict[str, List] = {}
            for table in tables:
                col_cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [
                    {"name": row[1], "type": row[2], "pk": bool(row[5])}
                    for row in col_cursor.fetchall()
                ]
                db_schema[table] = columns
            conn.close()
            schema[db_name] = {"db_file": db_path, "tables": db_schema}
        except Exception as e:
            schema[db_name] = {"error": str(e), "tables": {}}

    return {"databases": schema, "count": len(schema)}


# ─── WEEK 6-8: INDEXING & UNCERTAINTY ROUTES ─────────────────────────────────

class IndexSearchRequest(BaseModel):
    query: str
    method: str = "prefix_index"   # prefix_index | inverted_index | size_filter
    threshold: float = 0.4
    max_candidates: int = 10


class MetricCompareRequest(BaseModel):
    string1: str
    string2: str


class UncertaintyEvalRequest(BaseModel):
    query_plate: str
    candidate_plate: str
    sensor_confidence: float = 0.90


@router.get("/indexing/stats")
async def get_indexing_stats():
    """
    Return statistics of the Q-Gram Inverted Index & Prefix-Inverted Index.
    Reference: Week 6-8 Slides 47-65.
    """
    mediator = get_mediator()
    return mediator.qgram_index.get_index_stats()


@router.post("/indexing/search")
async def search_index_candidates(req: IndexSearchRequest):
    """
    Search candidate vehicle plates using the 2-step Blocking/Indexing framework.
    Methods: 'prefix_index' (Bayardo et al), 'inverted_index' (Sarawagi et al), 'size_filter' (Arasu et al).
    """
    mediator = get_mediator()
    candidates = mediator.qgram_index.search_candidates(
        query=req.query,
        method=req.method,
        jaccard_threshold=req.threshold,
        max_candidates=req.max_candidates
    )
    return {
        "query": req.query,
        "method": req.method,
        "candidates_found": len(candidates),
        "candidates": candidates
    }


@router.post("/indexing/metrics")
async def compare_string_metrics(req: MetricCompareRequest):
    """
    Compute all 8 Week 6-8 string similarity metrics between two strings.
    Levenshtein, Jaro, Jaro-Winkler, Jaccard, Overlap, TF-IDF, Ratcliff-Obershelp, Soundex.
    """
    from ..integration.indexing import compute_all_metrics
    mediator = get_mediator()
    metrics = compute_all_metrics(req.string1, req.string2, idf_weights=mediator.qgram_index.idf_weights)
    return {
        "string1": req.string1,
        "string2": req.string2,
        "metrics": metrics
    }


@router.post("/uncertainty/evaluate")
async def evaluate_uncertainty(req: UncertaintyEvalRequest):
    """
    Evaluate match probability and decision routing under uncertainty.
    Reference: Week 2 Slide 24 & Week 6-8 Slide 81.
    """
    mediator = get_mediator()
    features = mediator.uncertainty_engine.extract_feature_vector(
        req.query_plate,
        req.candidate_plate,
        sensor_confidence=req.sensor_confidence
    )
    prob = mediator.uncertainty_engine.calibrate_probability(features)

    tier = "AUTO_MERGE" if prob >= 0.85 else ("UNCERTAIN_REVIEW" if prob >= 0.50 else "REJECT")
    return {
        "query_plate": req.query_plate,
        "candidate_plate": req.candidate_plate,
        "calibrated_probability": prob,
        "decision_tier": tier,
        "features": features,
        "policy": {
            "auto_merge_threshold": 0.85,
            "review_threshold": 0.50,
            "routing": (
                "Automated straight-through integration" if tier == "AUTO_MERGE"
                else "Route to human review queue" if tier == "UNCERTAIN_REVIEW"
                else "Reject candidate as distinct entity"
            )
        }
    }


# ─── MATERIALIZED VIEW vs VIRTUAL VIEW ENDPOINTS ─────────────────────────────
# IIA Lecture: Materialized Views store pre-joined snapshots locally.
# Virtual Views query all nodes on-the-fly (the default integrate() path).


@router.get("/materialized-view")
async def get_materialized_view(plate: Optional[str] = None):
    """
    Query the Materialized View (pre-joined snapshot of all 5 databases).
    Instant O(1) lookup vs Virtual View which queries all nodes on-the-fly.

    - GET /api/materialized-view         → list all plates in the snapshot
    - GET /api/materialized-view?plate=X → lookup plate X from the snapshot
    """
    mediator = get_mediator()
    return mediator.get_materialized_view(plate)


@router.post("/materialized-view/refresh")
async def refresh_materialized_view():
    """
    Force-refresh the Materialized View from all 5 databases.
    After a write (INSERT/UPDATE/DELETE), call this to re-snapshot.
    """
    mediator = get_mediator()
    return mediator.refresh_materialized_view()


class ViewCompareRequest(BaseModel):
    plate: str

@router.post("/view-comparison")
async def compare_virtual_vs_materialized(req: ViewCompareRequest):
    """
    Side-by-side comparison: Virtual View (on-the-fly) vs Materialized View (snapshot).
    Demonstrates the IIA lecture concept of view freshness vs query latency.
    """
    import time
    mediator = get_mediator()

    # Virtual View (on-the-fly federation)
    t0 = time.perf_counter()
    virtual_result = mediator.integrate(req.plate)
    virtual_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Materialized View (pre-joined snapshot)
    t1 = time.perf_counter()
    mat_result = mediator.get_materialized_view(req.plate)
    mat_ms = round((time.perf_counter() - t1) * 1000, 2)

    return {
        "plate": req.plate,
        "virtual_view": {
            "description": "On-the-fly federated query to all 5 nodes (always fresh)",
            "latency_ms": virtual_ms,
            "overall_status": virtual_result.get("overall_status"),
            "sources_with_data": virtual_result.get("integration_metadata", {}).get("sources_with_data", 0),
        },
        "materialized_view": {
            "description": "Pre-joined snapshot stored locally (instant but may be stale)",
            "latency_ms": mat_ms,
            "last_refreshed": mat_result.get("last_refreshed"),
            "has_data": mat_result.get("result") is not None,
        },
        "comparison": {
            "latency_speedup": f"{virtual_ms / max(mat_ms, 0.01):.1f}x faster with materialized view",
            "freshness_tradeoff": "Virtual is always current; Materialized needs manual refresh after writes",
        }
    }


# ─── RDR (RIPPLE DOWN RULES) DEMO ENDPOINT ───────────────────────────────────
# Week 8 Lecture: Single-Classification Ripple Down Rules


class RdrDemoRequest(BaseModel):
    input_text: str
    mode: str = "plate"   # plate | address


@router.post("/rdr/demo")
async def rdr_demo(req: RdrDemoRequest):
    """
    Demonstrate the Ripple Down Rules engine with full audit trace.
    Shows how each rule node is evaluated (TRUE/FALSE) with its cornerstone case.

    Modes:
    - plate:   Normalize a license plate (UK, Indian, Bharat, Vanity)
    - address: Decompose a composite Indian postal address into schema fields
    """
    from ..integration.rdr_engine import normalize_plate_via_rdr, normalize_address_via_rdr

    if req.mode == "address":
        result, trace = normalize_address_via_rdr(req.input_text)
    else:
        result, trace = normalize_plate_via_rdr(req.input_text)

    return {
        "input": req.input_text,
        "mode": req.mode,
        "output": result,
        "rdr_audit_trace": trace,
        "rules_evaluated": len(trace),
        "engine": "Single-Classification Ripple Down Rules (SCRDR) — Week 8 Lecture",
        "reference": "if condition then conclusion [because case] except if ... else if ..."
    }


# ─── COURSE CONCEPTS VERIFICATION ENDPOINT ───────────────────────────────────


@router.get("/course-concepts")
async def get_course_concepts():
    """
    Returns a checklist of all IIA course concepts implemented in this project,
    with code references. For professor evaluation & viva preparation.
    """
    return {
        "project": "Uninsured Vehicle Detection via Distributed Data Integration & ANPR",
        "concepts_implemented": [
            {
                "topic": "Global-As-View (GAV) Schema Mapping",
                "lecture": "IIA Lecture 3",
                "file": "backend/app/integration/schema_mapper.py",
                "description": "Maps global attribute 'registration_number' to 5 different local attribute names"
            },
            {
                "topic": "Mediation / Federated Virtual Integration",
                "lecture": "IIA Lecture 1",
                "file": "backend/app/integration/mediator.py",
                "description": "Query decomposition → Sub-query execution → Result integration across 3 laptops"
            },
            {
                "topic": "Materialized View vs Virtual View",
                "lecture": "IIA Lectures",
                "file": "backend/app/integration/mediator.py → _refresh_materialized_view()",
                "description": "Materialized: pre-joined O(1) snapshot. Virtual: on-the-fly federation."
            },
            {
                "topic": "Size Filtering [Arasu et al, VLDB 06]",
                "lecture": "Week 6-8 Slides 53-54",
                "file": "backend/app/integration/indexing/qgram_index.py → size_filter()",
                "description": "|x|*t ≤ |y| ≤ |x|/t pruning for Jaccard threshold t"
            },
            {
                "topic": "Prefix Filtering [Chaudhuri et al, ICDE 06]",
                "lecture": "Week 6-8 Slides 55-56",
                "file": "backend/app/integration/indexing/qgram_index.py → search_candidates()",
                "description": "Prefix of size |x|-(k-1) must overlap if overlap ≥ k"
            },
            {
                "topic": "Prefix-Inverted Index [Bayardo et al, WWW 07]",
                "lecture": "Week 6-8 Slides 57-64",
                "file": "backend/app/integration/indexing/qgram_index.py → build()",
                "description": "Universal ordering (rarest tokens first), index only prefixes"
            },
            {
                "topic": "Position Filtering [Xiao et al, WWW 08]",
                "lecture": "Week 6-8 Slide 65",
                "file": "backend/app/integration/indexing/qgram_index.py → _position_filter()",
                "description": "Upper-bound on max overlap to prune redundant distance computations"
            },
            {
                "topic": "Edit Distance / Levenshtein (DP)",
                "lecture": "Week 6-8 Slides 16-19",
                "file": "backend/app/integration/indexing/string_metrics.py → edit_distance()",
                "description": "O(m*n) dynamic programming for insert/delete/substitute"
            },
            {
                "topic": "Jaro & Jaro-Winkler Similarity",
                "lecture": "Week 6-8 Slides 20-22",
                "file": "backend/app/integration/indexing/string_metrics.py → jaro_winkler_similarity()",
                "description": "Short string matching with prefix bonus (scale=0.1)"
            },
            {
                "topic": "Jaccard Similarity (q-grams & tokens)",
                "lecture": "Week 6-8 Slide 26",
                "file": "backend/app/integration/indexing/string_metrics.py → jaccard_similarity()",
                "description": "|Bx ∩ By| / |Bx ∪ By| on character 3-grams"
            },
            {
                "topic": "TF-IDF Cosine Similarity",
                "lecture": "Week 6-8 Slides 27-31",
                "file": "backend/app/integration/indexing/string_metrics.py → tfidf_cosine_similarity()",
                "description": "IDF-weighted cosine between token frequency vectors"
            },
            {
                "topic": "Soundex Phonetic Encoding",
                "lecture": "Week 6-8 Slides 36-37",
                "file": "backend/app/integration/indexing/string_metrics.py → soundex()",
                "description": "4-char phonetic code for surname matching"
            },
            {
                "topic": "Ratcliff-Obershelp Similarity",
                "lecture": "Week 6-8 Slides 33-34",
                "file": "backend/app/integration/indexing/string_metrics.py → ratcliff_obershelp_similarity()",
                "description": "Recursive longest common substring ratio"
            },
            {
                "topic": "Ripple Down Rules (RDR)",
                "lecture": "Week 8 Slides 24-29",
                "file": "backend/app/integration/rdr_engine.py",
                "description": "SCRDR tree: if→then→except→else for plate/address normalization with audit trail"
            },
            {
                "topic": "Composite Attribute Normalization",
                "lecture": "Week 8 Slides 8-16",
                "file": "backend/app/integration/rdr_engine.py → _build_address_rdr_tree()",
                "description": "Decomposing dirty Indian addresses into DB schema fields"
            },
            {
                "topic": "Schema Heterogeneity & Instance-Based Matching",
                "lecture": "IIA Lecture 3",
                "file": "backend/app/integration/schema_matcher.py",
                "description": "Multi-signal similarity (name, instance, value-distribution) across 5 schemas"
            },
            {
                "topic": "Entity Resolution & OCR Error Correction",
                "lecture": "Project + Week 6-8",
                "file": "backend/app/integration/entity_resolver.py",
                "description": "Positional OCR disambiguation, state code validation, format canonicalization"
            },
            {
                "topic": "Uncertainty & Probabilistic Integration",
                "lecture": "Week 2 + Week 6-8 Slide 81",
                "file": "backend/app/integration/uncertainty/",
                "description": "Logistic sigmoid calibration, STP 3-tier policy (AUTO_MERGE/REVIEW/REJECT)"
            },
            {
                "topic": "Source Registry & Health Monitoring",
                "lecture": "IIA Lecture 1",
                "file": "backend/app/integration/source_registry.py",
                "description": "PING health checks, response time tracking, retry logic"
            },
            {
                "topic": "Conflict Resolution & Truth Discovery",
                "lecture": "IIA Lectures",
                "file": "backend/app/integration/conflict_resolver.py",
                "description": "Detect & resolve conflicting values across 5 independently designed sources"
            },
        ]
    }

