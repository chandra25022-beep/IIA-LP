"""
Dedicated Node A Fast Sync Script
Pushes 1,000 vehicle registration records and 906 insurance records to Node A
over ngrok using multi-row batching.
"""
import sys
import io
import time
import sqlite3
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

NODE_A_URL = "https://mooned-antics-shorter.ngrok-free.dev"

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
        }, timeout=25)
        
        if res.status_code == 200 and res.json().get("success"):
            inserted += len(chunk)
            print(f"    ✓ Sent batch {i // BATCH_SIZE + 1} ({inserted}/{total} rows)...", flush=True)
        else:
            print(f"    ❌ Error on batch {i // BATCH_SIZE + 1}: {res.text[:200]}", flush=True)
            time.sleep(1)
    return inserted

def main():
    print("=" * 65)
    print("🚀 PUSHING 1,000 RECORDS TO NODE A (FRIEND 1)")
    print(f"URL: {NODE_A_URL}")
    print("=" * 65, flush=True)

    # Health check
    r = requests.get(f"{NODE_A_URL}/api/node/health", headers=HEADERS, timeout=10)
    print(f"✓ Health Check: {r.status_code} -> {r.json()}", flush=True)

    # 1. Registration
    print("\n[STEP 1] Syncing registration.db (1,000 vehicles)...", flush=True)
    conn_reg = sqlite3.connect(str(DATA_DIR / "registration.db"))
    c_reg = conn_reg.cursor()
    c_reg.execute("SELECT * FROM vehicle_registration")
    reg_rows = c_reg.fetchall()
    reg_cols = [col[0] for col in c_reg.description]
    conn_reg.close()

    # Clear old records
    del_r = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": "DELETE FROM vehicle_registration"
    }, timeout=15)
    print(f"  ✓ Cleared previous table on Node A: {del_r.json().get('success')}", flush=True)

    t0 = time.time()
    ins_reg = push_batches(NODE_A_URL, "registration", "vehicle_registration", reg_cols, reg_rows)
    print(f"  ✓ Completed registration in {time.time() - t0:.2f}s! ({ins_reg}/{len(reg_rows)} rows)", flush=True)

    # 2. Insurance
    print("\n[STEP 2] Syncing insurance.db (906 policies)...", flush=True)
    conn_ins = sqlite3.connect(str(DATA_DIR / "insurance.db"))
    c_ins = conn_ins.cursor()
    c_ins.execute("SELECT * FROM insurance_records")
    ins_rows = c_ins.fetchall()
    ins_cols = [col[0] for col in c_ins.description]
    conn_ins.close()

    del_i = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": "DELETE FROM insurance_records"
    }, timeout=15)
    print(f"  ✓ Cleared previous table on Node A: {del_i.json().get('success')}", flush=True)

    t1 = time.time()
    ins_ins = push_batches(NODE_A_URL, "insurance", "insurance_records", ins_cols, ins_rows)
    print(f"  ✓ Completed insurance in {time.time() - t1:.2f}s! ({ins_ins}/{len(ins_rows)} rows)", flush=True)

    # 3. Live Verification
    print("\n[STEP 3] Verifying live counts on Friend 1's laptop via ngrok...", flush=True)
    q_reg = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "registration",
        "query": "SELECT COUNT(*) FROM vehicle_registration"
    }, timeout=10)
    q_ins = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "insurance",
        "query": "SELECT COUNT(*) FROM insurance_records"
    }, timeout=10)

    print(f"  🎉 Live Node A registration count: {q_reg.json().get('rows')}", flush=True)
    print(f"  🎉 Live Node A insurance count:    {q_ins.json().get('rows')}", flush=True)

    # Check anchor vehicle test0.9.jpeg (DL7CQ1939)
    q_dl = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "registration",
        "query": "SELECT vehicle_reg_no, owner_name, model_name, registered_color FROM vehicle_registration WHERE vehicle_reg_no = 'DL7CQ1939'"
    }, timeout=10)
    print(f"  🚗 Verified Anchor Vehicle DL7CQ1939 on Friend 1's machine:\n     {q_dl.json().get('rows')}", flush=True)

if __name__ == "__main__":
    main()
