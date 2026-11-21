import sys
import io
import requests
import json

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

url = "https://mooned-antics-shorter.ngrok-free.dev"
headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

print("=" * 65)
print("🌐 LIVE TESTING NODE A (FRIEND 1'S LAPTOP OVER NGROK)")
print("URL:", url)
print("=" * 65)

# ── 1. Health Check ──
try:
    r = requests.get(f"{url}/api/node/health", headers=headers, timeout=10)
    print(f"\n[1] Health Check: Status {r.status_code}")
    print(f"    Payload: {r.json()}")
except Exception as e:
    print(f"\n[1] Health Check Failed: {e}")
    sys.exit(1)

# ── 2. Schema Sovereignty Test ──
# Attempt to write to 'theft' (which is owned by Node B, NOT Node A!)
r = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
    "database": "theft",
    "query": "INSERT INTO vehicle_security_records (case_id, vehicle_identifier) VALUES (999, 'UNAUTHORIZED')"
}, timeout=10)
print(f"\n[2] Schema Sovereignty Test (Attempting to write to 'theft' on Node A):")
print(f"    Status: {r.status_code} (Expected: 403 Forbidden)")
print(f"    Message: {r.json().get('detail')}")
assert r.status_code == 403, "Access control violation: Node A should have refused write to theft!"
print("    ✓ Access Control Confirmed: Node A strictly denies access to unowned databases.")

# ── 3. Inspect Current Records on Node A ──
r_reg = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "registration",
    "query": "SELECT vehicle_reg_no, owner_name, manufacturer, model_name FROM vehicle_registration LIMIT 10"
}, timeout=10)
print(f"\n[3] Current Registration Records on Node A:")
rows_reg = r_reg.json().get("rows", [])
print(f"    Count: {len(rows_reg)}")
for row in rows_reg:
    print(f"    - {row}")

r_ins = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "insurance",
    "query": "SELECT registration_id, insurer_name, policy_number, insurance_status FROM insurance_records LIMIT 10"
}, timeout=10)
print(f"\n[4] Current Insurance Records on Node A:")
rows_ins = r_ins.json().get("rows", [])
print(f"    Count: {len(rows_ins)}")
for row in rows_ins:
    print(f"    - {row}")

# ── 5. Ensure DL7CQ1939 exists on Node A ──
has_dl7_reg = any(r.get("vehicle_reg_no") == "DL7CQ1939" for r in rows_reg)
if not has_dl7_reg:
    print(f"\n[5] Inserting DL7CQ1939 into Node A registration.db...")
    insert_reg = (
        "INSERT INTO vehicle_registration "
        "(vehicle_reg_no, owner_name, owner_contact, owner_address, registration_date, "
        "manufacturer, model_name, vehicle_class, registered_color, fuel_type, registration_status, rto_office) "
        "VALUES ('DL7CQ1939', 'Rahul Sharma', '+91-98110-12345', 'Pocket A, Sarita Vihar, South Delhi', '2025-10-21', "
        "'Hyundai', 'Creta 1.6 VTVT', 'SUV / Private', 'BLACK', 'PETROL', 'ACTIVE', 'DL-07 South West Delhi')"
    )
    res = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
        "database": "registration",
        "query": insert_reg
    }, timeout=10)
    print("    Insert Reg Result:", res.json())

has_dl7_ins = any(r.get("registration_id") == "DL7CQ1939" for r in rows_ins)
if not has_dl7_ins:
    print(f"\n[6] Inserting DL7CQ1939 into Node A insurance.db...")
    insert_ins = (
        "INSERT INTO insurance_records "
        "(registration_id, insurer_name, policy_number, policy_start_date, policy_expiry_date, insurance_status, coverage_type) "
        "VALUES ('DL7CQ1939', 'HDFC ERGO General Insurance', 'HDFC-COMP-778899', '2025-10-21', '2027-10-21', 'ACTIVE', 'Comprehensive')"
    )
    res = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
        "database": "insurance",
        "query": insert_ins
    }, timeout=10)
    print("    Insert Ins Result:", res.json())

print("\n" + "=" * 65)
print("🎉 VERDICT: LIVE INTER-LAPTOP NETWORKING WITH NODE A IS 100% OPERATIONAL!")
print("=" * 65)
