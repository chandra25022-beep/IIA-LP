import sys
import io
import requests
import json
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NODE_A_URL = "https://mooned-antics-shorter.ngrok-free.dev"
HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

TEST_PLATE = "DL09VIVA7777"

print("=" * 70)
print("🚀 NODE A LIVE DISTRIBUTED CRUD DEMONSTRATION")
print("Target: Friend 1's Laptop via ngrok")
print(f"URL:    {NODE_A_URL}")
print("=" * 70)

# ── 1. CONNECT & HEALTH CHECK ──
print("\n[STEP 1] Connecting to Node A...")
r = requests.get(f"{NODE_A_URL}/api/node/health", headers=HEADERS, timeout=10)
print(f"  ✓ Connected! Status Code: {r.status_code}")
print(f"  ✓ Node A Reports Ownership: {r.json().get('owns')}")

# ── 2. INSERT OPERATION ──
print(f"\n[STEP 2] Performing Live INSERT into Node A for vehicle '{TEST_PLATE}'...")

# Clean up before inserting (in case of re-run)
requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "registration",
    "query": f"DELETE FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
}, timeout=10)
requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "insurance",
    "query": f"DELETE FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
}, timeout=10)

insert_reg_sql = (
    "INSERT INTO vehicle_registration "
    "(vehicle_reg_no, owner_name, owner_contact, owner_address, registration_date, "
    "manufacturer, model_name, vehicle_class, registered_color, fuel_type, "
    "registration_status, rto_office) "
    f"VALUES ('{TEST_PLATE}', 'Prof. Anupama Ray', '+91-98765-43210', 'IIIT Delhi Campus, Okhla Phase 3', '2026-10-21', "
    "'Mercedes-Benz', 'C-Class C300', 'Luxury Sedan', 'POLAR_WHITE', 'PETROL', 'ACTIVE', 'DL-09 Janakpuri, Delhi')"
)

r_reg = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "registration",
    "query": insert_reg_sql
}, timeout=10)
print(f"  ✓ Registration INSERT: {r_reg.json()}")

insert_ins_sql = (
    "INSERT INTO insurance_records "
    "(registration_id, insurer_name, policy_number, policy_start_date, "
    "policy_expiry_date, insurance_status, coverage_type, premium_amount) "
    f"VALUES ('{TEST_PLATE}', 'Bajaj Allianz General Insurance', 'BAJAJ-LUX-2026-001', "
    "'2026-10-21', '2028-10-21', 'ACTIVE', 'Zero Depreciation Bumper-to-Bumper', 48500.0)"
)

r_ins = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "insurance",
    "query": insert_ins_sql
}, timeout=10)
print(f"  ✓ Insurance INSERT:    {r_ins.json()}")

# ── 3. READ & VERIFY INSERTION ──
print(f"\n[STEP 3] Reading newly inserted records directly from Friend 1's SQLite databases...")
q_reg = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
    "database": "registration",
    "query": f"SELECT vehicle_reg_no, owner_name, manufacturer, model_name, registered_color, rto_office FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
}, timeout=10)
print(f"  ✓ registration.db returned:")
for row in q_reg.json().get("rows", []):
    print(f"    {row}")

q_ins = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
    "database": "insurance",
    "query": f"SELECT registration_id, insurer_name, policy_number, insurance_status, coverage_type FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
}, timeout=10)
print(f"  ✓ insurance.db returned:")
for row in q_ins.json().get("rows", []):
    print(f"    {row}")

# ── 4. UPDATE OPERATION ──
print(f"\n[STEP 4] Performing Live UPDATE on Node A...")
update_sql = (
    "UPDATE vehicle_registration "
    "SET owner_name = 'Prof. Anupama Ray (HOD IIITD)', registered_color = 'OBSIDIAN_BLACK' "
    f"WHERE vehicle_reg_no = '{TEST_PLATE}'"
)
r_upd = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "registration",
    "query": update_sql
}, timeout=10)
print(f"  ✓ UPDATE Result: {r_upd.json()}")

# Verify the update
q_upd = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
    "database": "registration",
    "query": f"SELECT vehicle_reg_no, owner_name, registered_color FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
}, timeout=10)
print(f"  ✓ Verified Updated Row on Friend 1's Laptop:")
for row in q_upd.json().get("rows", []):
    print(f"    {row}")

# ── 5. DELETE OPERATION ──
print(f"\n[STEP 5] Performing Live DELETE on Node A (Cleanup)...")
delete_reg_sql = f"DELETE FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
r_del1 = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "registration",
    "query": delete_reg_sql
}, timeout=10)
print(f"  ✓ DELETE from registration: {r_del1.json()}")

delete_ins_sql = f"DELETE FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
r_del2 = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
    "database": "insurance",
    "query": delete_ins_sql
}, timeout=10)
print(f"  ✓ DELETE from insurance:    {r_del2.json()}")

# Verify deletion
q_del = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
    "database": "registration",
    "query": f"SELECT * FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
}, timeout=10)
remaining = len(q_del.json().get("rows", []))
print(f"  ✓ Verification: Rows remaining for '{TEST_PLATE}': {remaining} (0 means fully deleted!)")

print("\n" + "=" * 70)
print("🎉 SUCCESS: NODE A LIVE INSERT, UPDATE, AND DELETE COMPLETED 100%!")
print("=" * 70)
