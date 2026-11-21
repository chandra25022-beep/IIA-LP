"""
Node Backend — FastAPI application for Laptop B / Laptop C

Exposes REST endpoints for:
  - Reading vehicle records from this node's databases
  - Running SELECT queries (federated from master)
  - Running INSERT/UPDATE/DELETE (ONLY on databases owned by this node)
  - Schema inspection
  - Health check

Run with:
  uvicorn main:app --host 0.0.0.0 --port 8001   (Laptop B)
  uvicorn main:app --host 0.0.0.0 --port 8002   (Laptop C)
"""
import sqlite3
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    NODE_DATABASES, DB_FILES, DB_TABLES, DB_LOCAL_KEY, DB_RELATED_TABLES,
    NODE_HOST, NODE_PORT, DEBUG, CORS_ORIGINS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=f"IIA Node Backend — {', '.join(NODE_DATABASES)}",
    description=(
        f"Distributed node server owning: {', '.join(NODE_DATABASES)}. "
        "Accepts read queries from master and write queries locally."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Models ───────────────────────────────────────────────────────────

class SqlQueryRequest(BaseModel):
    query: str
    database: str


class SqlWriteRequest(BaseModel):
    query: str
    database: str


class ContextQueryRequest(BaseModel):
    plate: str
    context_hints: List[str] = []


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_owns(db_name: str):
    """Raise 403 if this node does not own the requested database."""
    if db_name not in NODE_DATABASES:
        raise HTTPException(
            status_code=403,
            detail=(
                f"This node does not own '{db_name}'. "
                f"This node owns: {', '.join(NODE_DATABASES)}. "
                f"Connect to the correct laptop to access '{db_name}'."
            )
        )


def _get_conn(db_name: str):
    db_path = DB_FILES.get(db_name)
    if not db_path:
        raise HTTPException(status_code=400, detail=f"Unknown database: {db_name}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _is_select(query: str) -> bool:
    s = query.strip().lstrip("(").upper()
    return s.startswith("SELECT") or s.startswith("WITH")


def _is_write(query: str) -> bool:
    s = query.strip().lstrip("(").upper()
    return any(s.startswith(k) for k in ("INSERT", "UPDATE", "DELETE", "REPLACE"))


def _ensure_schema(db_name: str):
    """Create the table for this DB if it doesn't exist yet."""
    db_path = DB_FILES[db_name]
    conn = sqlite3.connect(db_path)

    schemas = {
        "insurance": """
            CREATE TABLE IF NOT EXISTS insurance_records (
                policy_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id     TEXT NOT NULL,
                insurer_name        TEXT NOT NULL,
                policy_number       TEXT UNIQUE NOT NULL,
                policy_start_date   TEXT NOT NULL,
                policy_expiry_date  TEXT NOT NULL,
                insurance_status    TEXT NOT NULL DEFAULT 'ACTIVE',
                vehicle_category    TEXT,
                premium_amount      REAL,
                nominee_name        TEXT,
                coverage_type       TEXT DEFAULT 'COMPREHENSIVE',
                claim_count         INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_ins_regid ON insurance_records(registration_id);
            CREATE TABLE IF NOT EXISTS insurance_policies (
                policy_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id     TEXT NOT NULL,
                insurer_name        TEXT NOT NULL,
                policy_number       TEXT UNIQUE NOT NULL,
                policy_start_date   TEXT NOT NULL,
                policy_expiry_date  TEXT NOT NULL,
                insurance_status    TEXT NOT NULL DEFAULT 'ACTIVE',
                vehicle_category    TEXT,
                premium_amount      REAL,
                nominee_name        TEXT,
                coverage_type       TEXT DEFAULT 'COMPREHENSIVE',
                claim_count         INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_insp_regid ON insurance_policies(registration_id);
            CREATE TABLE IF NOT EXISTS insurance_claims (
                claim_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id       INTEGER NOT NULL,
                claim_type      TEXT NOT NULL,
                claim_date      TEXT NOT NULL,
                claim_amount    REAL DEFAULT 0,
                claim_status    TEXT DEFAULT 'PENDING',
                description     TEXT,
                settlement_date TEXT,
                settlement_amount REAL,
                FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
            );
            CREATE TABLE IF NOT EXISTS policy_endorsements (
                endorsement_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id        INTEGER NOT NULL,
                endorsement_type TEXT NOT NULL,
                endorsement_date TEXT NOT NULL,
                old_value        TEXT,
                new_value        TEXT,
                premium_impact   REAL DEFAULT 0,
                FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
            );
            CREATE TABLE IF NOT EXISTS premium_payments (
                payment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id     INTEGER NOT NULL,
                amount        REAL NOT NULL,
                payment_date  TEXT NOT NULL,
                payment_mode  TEXT DEFAULT 'ONLINE',
                receipt_no    TEXT,
                FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
            );
        """,
        "registration": """
            CREATE TABLE IF NOT EXISTS vehicle_registration (
                reg_serial          INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_reg_no      TEXT UNIQUE NOT NULL,
                owner_name          TEXT NOT NULL,
                owner_id            INTEGER,
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
            );
            CREATE INDEX IF NOT EXISTS idx_reg_vno ON vehicle_registration(vehicle_reg_no);
            CREATE TABLE IF NOT EXISTS vehicle_owners (
                owner_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_name    TEXT NOT NULL,
                owner_contact TEXT,
                owner_address TEXT,
                pan_number    TEXT,
                aadhaar_hash  TEXT,
                owner_type    TEXT DEFAULT 'INDIVIDUAL'
            );
            CREATE TABLE IF NOT EXISTS vehicle_specs (
                spec_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_serial       INTEGER NOT NULL,
                manufacturer     TEXT,
                model_name       TEXT,
                vehicle_class    TEXT,
                registered_color TEXT,
                fuel_type        TEXT,
                engine_cc        INTEGER,
                manufacture_year INTEGER,
                emission_norm    TEXT,
                gross_weight     INTEGER,
                wheelbase_mm     INTEGER,
                FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
            );
            CREATE TABLE IF NOT EXISTS rto_transactions (
                txn_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_serial INTEGER NOT NULL,
                txn_type   TEXT NOT NULL,
                txn_date   TEXT NOT NULL,
                amount     REAL DEFAULT 0,
                receipt_no TEXT,
                rto_office TEXT,
                FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
            );
            CREATE TABLE IF NOT EXISTS fitness_certificates (
                cert_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_serial  INTEGER NOT NULL,
                test_date   TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                result      TEXT DEFAULT 'PASS',
                center_name TEXT,
                remarks     TEXT,
                FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
            );
        """,
        "theft": """
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
            );
            CREATE INDEX IF NOT EXISTS idx_theft_vid ON vehicle_security_records(vehicle_identifier);
            CREATE TABLE IF NOT EXISTS investigation_details (
                investigation_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id               INTEGER NOT NULL,
                investigation_date    TEXT,
                investigating_officer TEXT,
                sighting_location     TEXT,
                sighting_date         TEXT,
                investigation_status  TEXT DEFAULT 'OPEN',
                notes                 TEXT,
                FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
            );
            CREATE TABLE IF NOT EXISTS recovery_records (
                recovery_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id               INTEGER NOT NULL,
                recovery_date         TEXT,
                recovery_location     TEXT,
                condition_on_recovery TEXT DEFAULT 'INTACT',
                recovered_by          TEXT,
                remarks               TEXT,
                FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
            );
            CREATE TABLE IF NOT EXISTS suspect_info (
                suspect_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id       INTEGER NOT NULL,
                suspect_name  TEXT,
                suspect_alias TEXT,
                id_type       TEXT,
                id_number     TEXT,
                arrest_status TEXT DEFAULT 'WANTED',
                last_known_location TEXT,
                FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
            );
        """,
        "ministry": """
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
            );
            CREATE INDEX IF NOT EXISTS idx_min_vref ON transport_reports(vehicle_ref);
            CREATE TABLE IF NOT EXISTS enforcement_actions (
                action_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id     INTEGER NOT NULL,
                action_type   TEXT NOT NULL,
                action_date   TEXT NOT NULL,
                fine_amount   REAL DEFAULT 0,
                action_status TEXT DEFAULT 'PENDING',
                officer_name  TEXT,
                remarks       TEXT,
                FOREIGN KEY (report_id) REFERENCES transport_reports(report_id)
            );
            CREATE TABLE IF NOT EXISTS compliance_history (
                compliance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id      INTEGER NOT NULL,
                check_date     TEXT NOT NULL,
                was_compliant  INTEGER DEFAULT 0,
                check_type     TEXT,
                inspector_name TEXT,
                notes          TEXT,
                FOREIGN KEY (report_id) REFERENCES transport_reports(report_id)
            );
            CREATE TABLE IF NOT EXISTS blacklisted_vehicles (
                blacklist_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_ref      TEXT NOT NULL,
                blacklist_reason TEXT NOT NULL,
                blacklist_date   TEXT NOT NULL,
                is_active        INTEGER DEFAULT 1,
                authority        TEXT,
                removal_date     TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_bl_vref ON blacklisted_vehicles(vehicle_ref);
        """,
    }

    schema_sql = schemas.get(db_name, "")
    if schema_sql:
        conn.executescript(schema_sql)
        conn.commit()
    conn.close()


@app.on_event("startup")
async def startup_event():
    logger.info("Node Backend starting — owns: %s", ", ".join(NODE_DATABASES))
    for db_name in NODE_DATABASES:
        _ensure_schema(db_name)
        logger.info("  ✓ %s.db ready", db_name)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "node": "IIA Node Backend",
        "owns": NODE_DATABASES,
        "docs": "/docs",
        "health": "/api/node/health",
    }


@app.get("/api/node/health")
async def health():
    return {"status": "healthy", "owns": NODE_DATABASES}


# ─── Vehicle Lookup (called by Master Mediator) ───────────────────────────────

@app.get("/api/node/vehicle/{db_name}/{registration_number}")
async def get_vehicle_record(db_name: str, registration_number: str):
    """
    Return the record for the given registration number from this node's database.
    Called by the master backend's RemoteSource wrapper.
    """
    _check_owns(db_name)
    table = DB_TABLES[db_name]
    key_col = DB_LOCAL_KEY[db_name]
    try:
        conn = _get_conn(db_name)
        cursor = conn.execute(
            f"SELECT * FROM {table} WHERE {key_col} = ? ORDER BY rowid DESC LIMIT 1",
            (registration_number,)
        )
        row = cursor.fetchone()
        conn.close()
        return {"record": dict(row) if row else None, "database": db_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/node/vehicle/{db_name}/{registration_number}/{kind}")
async def get_vehicle_records_all(db_name: str, registration_number: str, kind: str):
    """Return all records of a given kind (policies, cases, reports, captures)."""
    _check_owns(db_name)
    table = DB_TABLES[db_name]
    key_col = DB_LOCAL_KEY[db_name]
    try:
        conn = _get_conn(db_name)
        cursor = conn.execute(
            f"SELECT * FROM {table} WHERE {key_col} = ? ORDER BY rowid DESC",
            (registration_number,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"records": rows, "count": len(rows), "database": db_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── SQL Query (SELECT — called by Master for federated reads) ────────────────

@app.post("/api/node/sql-query")
async def node_sql_query(request: SqlQueryRequest):
    """
    Execute a SELECT query on this node's database.
    Called by the master backend when federating reads.
    """
    db_name = request.database.lower()
    _check_owns(db_name)

    query = request.query.strip()
    if not _is_select(query):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed via sql-query.")

    try:
        conn = _get_conn(db_name)
        cursor = conn.execute(query)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"columns": columns, "rows": rows, "row_count": len(rows), "error": None}
    except Exception as e:
        return {"columns": [], "rows": [], "row_count": 0, "error": str(e)}


# ─── SQL Write (INSERT/UPDATE/DELETE — LOCAL ONLY) ────────────────────────────

@app.post("/api/node/sql-write")
async def node_sql_write(request: SqlWriteRequest):
    """
    Execute an INSERT/UPDATE/DELETE query on THIS node's database.

    ISOLATION: Only databases owned by this node can be written here.
    Attempting to write to another node's DB returns 403 Forbidden.
    """
    db_name = request.database.lower()
    _check_owns(db_name)  # 403 if not owned by this node

    query = request.query.strip()
    if not _is_write(query):
        raise HTTPException(
            status_code=400,
            detail="Only INSERT/UPDATE/DELETE queries are allowed via sql-write."
        )

    try:
        conn = _get_conn(db_name)
        cursor = conn.execute(query)
        conn.commit()
        affected = cursor.rowcount
        lastrowid = cursor.lastrowid
        conn.close()
        return {
            "success": True,
            "database": db_name,
            "affected_rows": affected,
            "last_insert_id": lastrowid,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Phase 3: Context Discovery (FK-PK Join + Minimal Response) ───────────────

@app.post("/api/node/context-query")
async def context_query(request: ContextQueryRequest):
    """
    Phase 3 Context Discovery Endpoint.
    
    Performs LOCAL FK-PK joins across all tables in this node's databases,
    discovers related records, and returns a MINIMAL context summary.
    
    This is NOT a raw data dump — the node processes locally and filters.
    Real-world analogy: when Company A asks Company B about a vehicle,
    Company B runs internal queries across its related tables and returns
    only the relevant summary.
    """
    import time
    start = time.perf_counter()
    plate = request.plate.strip().upper()
    results = {}

    for db_name in NODE_DATABASES:
        db_path = DB_FILES.get(db_name)
        if not db_path:
            continue

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            table = DB_TABLES[db_name]
            key_col = DB_LOCAL_KEY[db_name]
            related_config = DB_RELATED_TABLES.get(db_name, {})

            # Step 1: Find base record
            # For insurance, try insurance_policies first
            primary_table = related_config.get("primary", table)
            fallback = related_config.get("fallback_primary")
            tables_in_db = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]

            if primary_table not in tables_in_db and fallback and fallback in tables_in_db:
                primary_table = fallback

            base_rows = conn.execute(
                f"SELECT * FROM {primary_table} WHERE {key_col} = ? ORDER BY rowid DESC",
                (plate,)
            ).fetchall()

            if not base_rows:
                results[db_name] = {"found": False, "source": db_name}
                conn.close()
                continue

            base_record = dict(base_rows[0])
            all_base_records = [dict(r) for r in base_rows]

            # Step 2: Follow FK-PK relationships
            related_data = {}
            fk_tables_joined = []
            context_keywords = []
            risk_flags = []

            related_tables = related_config.get("related", {})
            for rel_table, rel_info in related_tables.items():
                if rel_table not in tables_in_db:
                    continue

                fk_col = rel_info["fk"]
                is_direct = rel_info.get("direct_key", False)

                if is_direct:
                    # Direct lookup by plate (e.g., blacklisted_vehicles)
                    rel_rows = conn.execute(
                        f"SELECT * FROM {rel_table} WHERE {fk_col} = ?",
                        (plate,)
                    ).fetchall()
                else:
                    # FK lookup through base records
                    rel_rows = []
                    for br in all_base_records:
                        pk_val = br.get(fk_col)
                        if pk_val is not None:
                            rows = conn.execute(
                                f"SELECT * FROM {rel_table} WHERE {fk_col} = ?",
                                (pk_val,)
                            ).fetchall()
                            rel_rows.extend(rows)

                if rel_rows:
                    related_data[rel_table] = [dict(r) for r in rel_rows]
                    fk_tables_joined.append(rel_table)

            conn.close()

            # Step 3: Build MINIMAL context (not raw dump)
            context = _build_context_summary(
                db_name, plate, base_record, all_base_records,
                related_data, fk_tables_joined, request.context_hints
            )
            results[db_name] = context

        except Exception as e:
            logger.error(f"Context query error for {db_name}: {e}")
            results[db_name] = {"found": False, "source": db_name, "error": str(e)}

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "plate": plate,
        "node_databases": NODE_DATABASES,
        "context_results": results,
        "processing_time_ms": elapsed_ms,
        "context_hints_received": request.context_hints,
        "phase": "Phase 3 — FK-PK Context Discovery",
        "note": "Node processed locally and returned minimal context (not raw data dump)",
    }


def _build_context_summary(
    db_name: str, plate: str, base_record: dict,
    all_base_records: list, related_data: dict,
    fk_tables_joined: list, context_hints: list
) -> dict:
    """Build a minimal, relevant context summary from FK-PK joined data."""
    from datetime import date as _date

    context = {
        "source": db_name,
        "found": True,
        "plate": plate,
        "fk_tables_joined": fk_tables_joined,
        "total_related_records": sum(len(v) for v in related_data.values()),
        "risk_flags": [],
        "context_keywords": [],
    }

    today_str = _date.today().isoformat()

    if db_name == "registration":
        # Summarize owner + specs + fitness + transactions
        owner_data = related_data.get("vehicle_owners", [{}])
        specs_data = related_data.get("vehicle_specs", [{}])
        fitness_data = related_data.get("fitness_certificates", [])
        txn_data = related_data.get("rto_transactions", [])

        owner = owner_data[0] if owner_data else {}
        specs = specs_data[0] if specs_data else {}

        context["owner_summary"] = {
            "name": owner.get("owner_name", base_record.get("owner_name")),
            "contact": owner.get("owner_contact", base_record.get("owner_contact")),
            "address": owner.get("owner_address", base_record.get("owner_address")),
        }
        context["vehicle_summary"] = {
            "make": specs.get("manufacturer", base_record.get("manufacturer", "")),
            "model": specs.get("model_name", base_record.get("model_name", "")),
            "class": specs.get("vehicle_class", base_record.get("vehicle_class", "")),
            "color": specs.get("registered_color", base_record.get("registered_color", "")),
            "fuel": specs.get("fuel_type", base_record.get("fuel_type", "")),
            "engine_cc": specs.get("engine_cc"),
            "year": specs.get("manufacture_year"),
            "emission_norm": specs.get("emission_norm"),
        }
        context["registration_status"] = base_record.get("registration_status")
        context["rto_office"] = base_record.get("rto_office")

        # Fitness status
        if fitness_data:
            latest = sorted(fitness_data, key=lambda x: x.get("expiry_date", ""), reverse=True)[0]
            context["fitness_status"] = latest.get("result", "UNKNOWN")
            context["fitness_expiry"] = latest.get("expiry_date")
            if latest.get("expiry_date", "9999") < today_str:
                context["risk_flags"].append("FITNESS_EXPIRED")
            if latest.get("result") in ("FAIL", "CONDITIONAL"):
                context["risk_flags"].append(f"FITNESS_{latest['result']}")

        context["total_transactions"] = len(txn_data)
        context["recent_transactions"] = [
            {"type": t.get("txn_type"), "date": t.get("txn_date")}
            for t in sorted(txn_data, key=lambda x: x.get("txn_date", ""), reverse=True)[:3]
        ]
        context["context_keywords"] = [
            specs.get("manufacturer", ""), specs.get("model_name", ""),
            specs.get("vehicle_class", ""), base_record.get("rto_office", ""),
        ]

    elif db_name == "insurance":
        claims = related_data.get("insurance_claims", [])
        endorsements = related_data.get("policy_endorsements", [])
        payments = related_data.get("premium_payments", [])

        context["policy_summary"] = {
            "insurer": base_record.get("insurer_name"),
            "policy_number": base_record.get("policy_number"),
            "status": base_record.get("insurance_status"),
            "coverage": base_record.get("coverage_type"),
            "start": base_record.get("policy_start_date"),
            "expiry": base_record.get("policy_expiry_date"),
            "premium": base_record.get("premium_amount"),
        }
        context["claims_summary"] = {
            "total_claims": len(claims),
            "total_amount": round(sum(c.get("claim_amount", 0) for c in claims), 2),
            "recent": [{"type": c.get("claim_type"), "amount": c.get("claim_amount"),
                        "status": c.get("claim_status")} for c in claims[:3]],
        }
        context["endorsements_count"] = len(endorsements)
        context["payments_count"] = len(payments)
        context["total_premium_paid"] = round(sum(p.get("amount", 0) for p in payments), 2)

        if base_record.get("insurance_status") != "ACTIVE":
            context["risk_flags"].append(f"INSURANCE_{base_record.get('insurance_status', 'UNKNOWN')}")
        if base_record.get("policy_expiry_date", "9999") < today_str:
            context["risk_flags"].append("POLICY_EXPIRED")
        if claims:
            context["risk_flags"].append(f"HAS_{len(claims)}_CLAIMS")

        context["context_keywords"] = [
            base_record.get("insurer_name", ""), base_record.get("insurance_status", ""),
        ]

    elif db_name == "theft":
        investigations = related_data.get("investigation_details", [])
        recoveries = related_data.get("recovery_records", [])
        suspects = related_data.get("suspect_info", [])

        context["cases_summary"] = {
            "total_cases": len(all_base_records),
            "latest": {
                "type": base_record.get("case_type"),
                "status": base_record.get("case_status"),
                "date": base_record.get("reported_date"),
            },
        }
        context["investigations"] = {
            "total": len(investigations),
            "sightings": [i.get("sighting_location") for i in investigations if i.get("sighting_location")][:5],
            "active": sum(1 for i in investigations if i.get("investigation_status") not in ("CLOSED", "DEAD_END")),
        }
        context["recoveries"] = {"total": len(recoveries)}
        context["suspects"] = {
            "total": len(suspects),
            "arrested": sum(1 for s in suspects if s.get("arrest_status") == "ARRESTED"),
        }

        if base_record.get("case_type") == "STOLEN" and base_record.get("case_status") == "OPEN":
            context["risk_flags"].append("ACTIVELY_STOLEN")
        if base_record.get("case_type") == "SUSPICIOUS":
            context["risk_flags"].append("SUSPICIOUS_VEHICLE")

        sightings = [i.get("sighting_location") for i in investigations if i.get("sighting_location")]
        context["context_keywords"] = sightings + [base_record.get("case_type", "")]

    elif db_name == "ministry":
        actions = related_data.get("enforcement_actions", [])
        compliance = related_data.get("compliance_history", [])
        blacklist = related_data.get("blacklisted_vehicles", [])

        context["reports_summary"] = {
            "total_reports": len(all_base_records),
            "types": list(set(r.get("report_type") for r in all_base_records)),
            "latest": {
                "type": base_record.get("report_type"),
                "severity": base_record.get("severity"),
                "date": base_record.get("report_date"),
            },
        }
        context["enforcement"] = {
            "total_actions": len(actions),
            "total_fines": round(sum(a.get("fine_amount", 0) for a in actions if a.get("fine_amount")), 2),
            "pending": sum(1 for a in actions if a.get("action_status") == "PENDING"),
        }
        comp_rate = sum(1 for c in compliance if c.get("was_compliant")) / max(len(compliance), 1)
        context["compliance_rate"] = round(comp_rate * 100, 1)
        context["is_blacklisted"] = any(b.get("is_active") for b in blacklist)

        if context["is_blacklisted"]:
            context["risk_flags"].append("BLACKLISTED")
        pending = context["enforcement"]["pending"]
        if pending > 0:
            context["risk_flags"].append(f"{pending}_PENDING_FINES")

        context["context_keywords"] = [base_record.get("report_type", "")]

    # Filter empty keywords
    context["context_keywords"] = [k for k in context.get("context_keywords", []) if k]
    return context


# ─── Schema Info ──────────────────────────────────────────────────────────────

@app.get("/api/node/schema/{db_name}")
async def get_schema(db_name: str):
    """Return table schema for one of this node's databases."""
    _check_owns(db_name)
    try:
        conn = _get_conn(db_name)
        tables_cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [r[0] for r in tables_cur.fetchall()]
        result = {}
        for tbl in tables:
            col_cur = conn.execute(f"PRAGMA table_info({tbl})")
            cols = [{"name": r[1], "type": r[2], "pk": bool(r[5])} for r in col_cur.fetchall()]
            cnt_cur = conn.execute(f"SELECT COUNT(*) FROM {tbl}")
            result[tbl] = {"columns": cols, "record_count": cnt_cur.fetchone()[0]}
        conn.close()
        return {"source": db_name, "tables": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/node/statistics/{db_name}")
async def get_statistics(db_name: str):
    """Return row counts and basic stats for one of this node's databases."""
    _check_owns(db_name)
    table = DB_TABLES.get(db_name)
    if not table:
        raise HTTPException(status_code=400, detail=f"Unknown db: {db_name}")
    try:
        conn = _get_conn(db_name)
        cur = conn.execute(f"SELECT COUNT(*) as total FROM {table}")
        row = dict(cur.fetchone())
        conn.close()
        return row
    except Exception as e:
        return {"total": 0, "error": str(e)}


@app.get("/api/node/tables")
async def get_all_tables():
    """Return schema for all databases owned by this node."""
    result = {}
    for db_name in NODE_DATABASES:
        try:
            conn = _get_conn(db_name)
            tables_cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [r[0] for r in tables_cur.fetchall()]
            db_schema = {}
            for tbl in tables:
                col_cur = conn.execute(f"PRAGMA table_info({tbl})")
                cols = [{"name": r[1], "type": r[2], "pk": bool(r[5])} for r in col_cur.fetchall()]
                db_schema[tbl] = cols
            conn.close()
            result[db_name] = {"tables": db_schema}
        except Exception as e:
            result[db_name] = {"error": str(e), "tables": {}}
    return {"databases": result, "owns": NODE_DATABASES}


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=NODE_HOST, port=NODE_PORT, reload=DEBUG)
