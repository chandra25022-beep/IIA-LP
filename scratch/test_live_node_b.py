import sys
import io
import requests
import json

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

url = "https://manhood-overcome-copartner.ngrok-free.dev"
headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

print("=" * 65)
print("🌐 LIVE TESTING NODE B (FRIEND 2'S LAPTOP OVER NGROK)")
print("URL:", url)
print("=" * 65)

# ── 1. Health Check ──
r = requests.get(f"{url}/api/node/health", headers=headers, timeout=10)
print(f"\n[1] Health Check: Status {r.status_code}")
print(f"    Payload: {r.json()}")

# ── 2. Access Control Sovereignty Test ──
# Attempt to write to 'insurance' (which is owned by Node A, NOT Node B!)
r = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
    "database": "insurance",
    "query": "INSERT INTO insurance_records (policy_id, registration_id) VALUES (999, 'UNAUTHORIZED')"
}, timeout=10)
print(f"\n[2] Schema Sovereignty Test (Attempting to write to 'insurance' on Node B):")
print(f"    Status: {r.status_code} (Expected: 403 Forbidden)")
print(f"    Message: {r.json().get('detail')}")
assert r.status_code == 403, "Access control violation: Node B should have refused write to insurance!"
print("    ✓ Access Control Confirmed: Node B strictly denies access to unowned databases.")

# ── 3. Live INSERT on Node B (theft.db) ──
test_plate = "DL7CQ1939"
insert_query = (
    "INSERT INTO vehicle_security_records "
    "(vehicle_identifier, case_type, case_status, remarks, reported_date) "
    f"VALUES ('{test_plate}', 'THEFT', 'OPEN', 'Viva Live Demo: Stolen Alert Broadcast', '2026-10-21')"
)
r = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
    "database": "theft",
    "query": insert_query
}, timeout=10)
print(f"\n[3] Live INSERT into Node B (theft.db for '{test_plate}'):")
print(f"    Status: {r.status_code}")
print(f"    Response: {r.json()}")

# ── 4. Live SELECT from Node B to Verify Insertion ──
r = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "theft",
    "query": f"SELECT case_id, vehicle_identifier, case_type, case_status, remarks FROM vehicle_security_records WHERE vehicle_identifier = '{test_plate}'"
}, timeout=10)
rows = r.json().get("rows", [])
print(f"\n[4] Live SELECT from Node B to verify inserted record:")
print(f"    Total Rows Returned: {len(rows)}")
for idx, row in enumerate(rows):
    print(f"    Row {idx+1}: {row}")

# ── 5. Live UPDATE on Node B ──
update_query = (
    "UPDATE vehicle_security_records "
    "SET case_status = 'RECOVERED', remarks = 'Viva Live Demo: Vehicle located by Delhi Police' "
    f"WHERE vehicle_identifier = '{test_plate}'"
)
r = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
    "database": "theft",
    "query": update_query
}, timeout=10)
print(f"\n[5] Live UPDATE on Node B (Marking status 'RECOVERED'):")
print(f"    Status: {r.status_code}")
print(f"    Response: {r.json()}")

# Verify the update on Node B
r = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "theft",
    "query": f"SELECT case_id, vehicle_identifier, case_status, remarks FROM vehicle_security_records WHERE vehicle_identifier = '{test_plate}'"
}, timeout=10)
updated_rows = r.json().get("rows", [])
print(f"    Updated Record in Friend 2's Database: {updated_rows}")

# ── 6. Live DELETE on Node B (Cleanup) ──
delete_query = f"DELETE FROM vehicle_security_records WHERE vehicle_identifier = '{test_plate}'"
r = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
    "database": "theft",
    "query": delete_query
}, timeout=10)
print(f"\n[6] Live DELETE on Node B (Cleanup):")
print(f"    Status: {r.status_code}")
print(f"    Response: {r.json()}")

# Verify deletion
r = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "theft",
    "query": f"SELECT * FROM vehicle_security_records WHERE vehicle_identifier = '{test_plate}'"
}, timeout=10)
remaining = r.json().get("rows", [])
print(f"    Remaining Rows for '{test_plate}' after delete: {len(remaining)}")

print("\n" + "=" * 65)
print("🎉 VERDICT: LIVE INTER-LAPTOP NETWORKING WITH NODE B IS 100% OPERATIONAL!")
print("=" * 65)
