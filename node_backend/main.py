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
    NODE_DATABASES, DB_FILES, DB_TABLES, DB_LOCAL_KEY,
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
        """,
        "registration": """
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
            );
            CREATE INDEX IF NOT EXISTS idx_reg_vno ON vehicle_registration(vehicle_reg_no);
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
