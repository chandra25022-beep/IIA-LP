"""
Fast Batched Distributed Database Sync Script
Synchronizes local 1,000-vehicle seeded records from Master machine to:
- Node A (Friend 1: registration.db, insurance.db)
- Node B (Friend 2: theft.db, ministry.db)

Uses multi-row INSERT batching (50 rows per batch) for near-instant execution over ngrok tunnels.
"""
import sys
import io
import sqlite3
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

NODE_A_URL = "https://mooned-antics-shorter.ngrok-free.dev"
NODE_B_URL = "https://manhood-overcome-copartner.ngrok-free.dev"

HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

BATCH_SIZE = 50

def escape_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"

def push_batches(node_url, db_name, table_name, cols, rows):
    cols_str = ", ".join(cols)
    total = len(rows)
    inserted = 0

    for i in range(0, total, BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        val_tuples = []
        for row in chunk:
            row_str = "(" + ", ".join(escape_sql(v) for v in row) + ")"
            val_tuples.append(row_str)
        sql = f"INSERT INTO {table_name} ({cols_str}) VALUES " + ",\n".join(val_tuples)

        res = requests.post(f"{node_url}/api/node/sql-write", headers=HEADERS, json={
            "database": db_name,
            "query": sql
        }, timeout=20)
        
        if res.status_code == 200 and res.json().get("success"):
            inserted += len(chunk)
            print(f"    ✓ Sent batch {i // BATCH_SIZE + 1}: {inserted}/{total} records")
        else:
            print(f"    ❌ Error on batch {i // BATCH_SIZE + 1}: {res.text[:200]}")
    return inserted

def sync_node_b():
    print("=" * 65)
    print("🚀 FAST BATCH SYNC TO NODE B (Friend 2: theft.db & ministry.db)")
    print(f"Target: {NODE_B_URL}")
    print("=" * 65)

    try:
        r = requests.get(f"{NODE_B_URL}/api/node/health", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"  ❌ Node B health check failed: {r.status_code}")
            return False
        print(f"  ✓ Node B is ONLINE! Owns: {r.json().get('owns')}")
    except Exception as e:
        print(f"  ❌ Cannot reach Node B: {e}")
        return False

    # 1. Sync Theft DB
    print("\n[1] Syncing theft.db (vehicle_security_records)...")
    conn_theft = sqlite3.connect(str(DATA_DIR / "theft.db"))
    c_theft = conn_theft.cursor()
    c_theft.execute("SELECT * FROM vehicle_security_records")
    theft_rows = c_theft.fetchall()
    theft_cols = [col[0] for col in c_theft.description]
    conn_theft.close()

    # Clear old table
    requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": "DELETE FROM vehicle_security_records"
    }, timeout=15)

    ins_theft = push_batches(NODE_B_URL, "theft", "vehicle_security_records", theft_cols, theft_rows)
    print(f"  ✓ Theft Sync Completed: {ins_theft}/{len(theft_rows)} records in Node B")

    # 2. Sync Ministry DB
    print("\n[2] Syncing ministry.db (transport_reports)...")
    conn_min = sqlite3.connect(str(DATA_DIR / "ministry.db"))
    c_min = conn_min.cursor()
    c_min.execute("SELECT * FROM transport_reports")
    min_rows = c_min.fetchall()
    min_cols = [col[0] for col in c_min.description]
    conn_min.close()

    # Clear old table
    requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "ministry",
        "query": "DELETE FROM transport_reports"
    }, timeout=15)

    ins_min = push_batches(NODE_B_URL, "ministry", "transport_reports", min_cols, min_rows)
    print(f"  ✓ Ministry Sync Completed: {ins_min}/{len(min_rows)} records in Node B")

    # Verification Query on Node B
    r_ver_t = requests.post(f"{NODE_B_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "theft",
        "query": "SELECT COUNT(*) FROM vehicle_security_records"
    }, timeout=10)
    r_ver_m = requests.post(f"{NODE_B_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "ministry",
        "query": "SELECT COUNT(*) FROM transport_reports"
    }, timeout=10)
    print("\n[VERIFICATION DIRECTLY ON FRIEND 2's LAPTOP OVER NGROK]")
    print(f"  ✓ Live theft.db count on Friend 2:    {r_ver_t.json().get('rows')}")
    print(f"  ✓ Live ministry.db count on Friend 2: {r_ver_m.json().get('rows')}")
    return True

def sync_node_a(custom_url=None):
    url = custom_url or NODE_A_URL
    print("\n" + "=" * 65)
    print("🚀 FAST BATCH SYNC TO NODE A (Friend 1: registration.db & insurance.db)")
    print(f"Target: {url}")
    print("=" * 65)

    try:
        r = requests.get(f"{url}/api/node/health", headers=HEADERS, timeout=5)
        if r.status_code != 200:
            print(f"  ❌ Node A health check returned: {r.status_code}")
            return False
        print(f"  ✓ Node A is ONLINE! Owns: {r.json().get('owns')}")
    except Exception as e:
        print(f"  ❌ Cannot reach Node A: {e}")
        return False

    # 1. Sync Registration DB
    print("\n[1] Syncing registration.db (vehicle_registration)...")
    conn_reg = sqlite3.connect(str(DATA_DIR / "registration.db"))
    c_reg = conn_reg.cursor()
    c_reg.execute("SELECT * FROM vehicle_registration")
    reg_rows = c_reg.fetchall()
    reg_cols = [col[0] for col in c_reg.description]
    conn_reg.close()

    requests.post(f"{url}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": "DELETE FROM vehicle_registration"
    }, timeout=15)

    ins_reg = push_batches(url, "registration", "vehicle_registration", reg_cols, reg_rows)
    print(f"  ✓ Registration Sync Completed: {ins_reg}/{len(reg_rows)} records in Node A")

    # 2. Sync Insurance DB
    print("\n[2] Syncing insurance.db (insurance_records)...")
    conn_ins = sqlite3.connect(str(DATA_DIR / "insurance.db"))
    c_ins = conn_ins.cursor()
    c_ins.execute("SELECT * FROM insurance_records")
    ins_rows = c_ins.fetchall()
    ins_cols = [col[0] for col in c_ins.description]
    conn_ins.close()

    requests.post(f"{url}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": "DELETE FROM insurance_records"
    }, timeout=15)

    ins_ins = push_batches(url, "insurance", "insurance_records", ins_cols, ins_rows)
    print(f"  ✓ Insurance Sync Completed: {ins_ins}/{len(ins_rows)} records in Node A")

    # Verification Query on Node A
    r_ver_r = requests.post(f"{url}/api/node/sql-query", headers=HEADERS, json={
        "database": "registration",
        "query": "SELECT COUNT(*) FROM vehicle_registration"
    }, timeout=10)
    r_ver_i = requests.post(f"{url}/api/node/sql-query", headers=HEADERS, json={
        "database": "insurance",
        "query": "SELECT COUNT(*) FROM insurance_records"
    }, timeout=10)
    print("\n[VERIFICATION DIRECTLY ON FRIEND 1's LAPTOP OVER NGROK]")
    print(f"  ✓ Live registration.db count on Friend 1: {r_ver_r.json().get('rows')}")
    print(f"  ✓ Live insurance.db count on Friend 1:    {r_ver_i.json().get('rows')}")
    return True

if __name__ == "__main__":
    node_a_override = sys.argv[1] if len(sys.argv) > 1 else None
    sync_node_b()
    sync_node_a(node_a_override)
