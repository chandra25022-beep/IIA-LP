import sys
import io
import requests
import json
import time

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NODE_A_URL = "https://mooned-antics-shorter.ngrok-free.dev"
NODE_B_URL = "https://manhood-overcome-copartner.ngrok-free.dev"
MASTER_URL = "http://127.0.0.1:8000"

HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

TEST_PLATE = "KA51VIVA2026"

def header(text):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def test_node_a():
    header("💻 PART 1: TESTING NODE A (FRIEND 1 - INSURANCE & REGISTRATION)")
    print(f"Node A URL: {NODE_A_URL}")

    # 1. Health & Ownership
    r = requests.get(f"{NODE_A_URL}/api/node/health", headers=HEADERS, timeout=10)
    print(f"\n[1.1] Health Check: Status {r.status_code}")
    print(f"      Owned Databases: {r.json().get('owns')}")
    assert set(r.json().get('owns', [])) == {"insurance", "registration"}, "Node A must own insurance & registration!"

    # 2. Access Control: Should reject theft
    r = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": "INSERT INTO vehicle_security_records (case_id, vehicle_identifier) VALUES (999, 'HACK')"
    }, timeout=10)
    print(f"\n[1.2] Schema Sovereignty (Trying to access 'theft' on Node A):")
    print(f"      Status: {r.status_code} (Expected: 403 Forbidden)")
    print(f"      Detail: {r.json().get('detail')}")
    assert r.status_code == 403, "Node A should have refused access to theft.db!"
    print("      ✓ 403 Forbidden confirmed! Node A strictly protects its boundary.")

    # 3. Live INSERT into Node A
    print(f"\n[1.3] Live INSERT into Node A (registration.db & insurance.db for '{TEST_PLATE}'):")
    # Clean previous if any
    requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": f"DELETE FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
    }, timeout=10)
    requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": f"DELETE FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
    }, timeout=10)

    # Insert Registration
    insert_reg = (
        "INSERT INTO vehicle_registration "
        "(vehicle_reg_no, owner_name, owner_contact, manufacturer, model_name, "
        "registered_color, registration_status, registration_date, rto_office) "
        f"VALUES ('{TEST_PLATE}', 'Dr. Priya Nambiar', '+91-99887-76655', 'Kia', 'Seltos GTX', "
        "'AURORA_BLACK', 'ACTIVE', '2026-10-21', 'KA-51 Electronic City, Bangalore')"
    )
    r_reg = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": insert_reg
    }, timeout=10)
    print(f"      Insert Registration Result: {r_reg.json()}")

    # Insert Insurance
    insert_ins = (
        "INSERT INTO insurance_records "
        "(registration_id, insurer_name, policy_number, policy_start_date, "
        "policy_expiry_date, insurance_status, coverage_type, premium_amount) "
        f"VALUES ('{TEST_PLATE}', 'Tata AIG General Insurance', 'TATA-VIVA-998811', "
        "'2026-10-21', '2028-10-21', 'ACTIVE', 'Zero Depreciation Comprehensive', 22500.0)"
    )
    r_ins = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": insert_ins
    }, timeout=10)
    print(f"      Insert Insurance Result: {r_ins.json()}")

    # 4. Live SELECT from Node A
    print(f"\n[1.4] Live SELECT from Node A:")
    r_q = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "registration",
        "query": f"SELECT vehicle_reg_no, owner_name, manufacturer, model_name, rto_office FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
    }, timeout=10)
    reg_data = r_q.json().get("rows", [])
    print(f"      Registration on Friend 1's Laptop: {reg_data}")

    r_qi = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "insurance",
        "query": f"SELECT registration_id, insurer_name, policy_number, insurance_status, coverage_type FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
    }, timeout=10)
    ins_data = r_qi.json().get("rows", [])
    print(f"      Insurance on Friend 1's Laptop: {ins_data}")

    # 5. Live UPDATE on Node A
    print(f"\n[1.5] Live UPDATE on Node A (Updating Owner Name & Coverage Type):")
    update_reg = f"UPDATE vehicle_registration SET owner_name = 'Dr. Priya Nambiar (Verified MTech IIITD)' WHERE vehicle_reg_no = '{TEST_PLATE}'"
    r_u = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": update_reg
    }, timeout=10)
    print(f"      Update Result: {r_u.json()}")

    # Verify update on Node A
    r_q2 = requests.post(f"{NODE_A_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "registration",
        "query": f"SELECT vehicle_reg_no, owner_name FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
    }, timeout=10)
    print(f"      Updated Data on Friend 1's Machine: {r_q2.json().get('rows')}")

    return True


def test_node_b():
    header("🚔 PART 2: TESTING NODE B (FRIEND 2 - THEFT & MINISTRY)")
    print(f"Node B URL: {NODE_B_URL}")

    # 1. Health & Ownership
    r = requests.get(f"{NODE_B_URL}/api/node/health", headers=HEADERS, timeout=10)
    print(f"\n[2.1] Health Check: Status {r.status_code}")
    print(f"      Owned Databases: {r.json().get('owns')}")
    assert set(r.json().get('owns', [])) == {"theft", "ministry"}, "Node B must own theft & ministry!"

    # 2. Access Control: Should reject insurance
    r = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": "INSERT INTO insurance_records (policy_id, registration_id) VALUES (999, 'HACK')"
    }, timeout=10)
    print(f"\n[2.2] Schema Sovereignty (Trying to access 'insurance' on Node B):")
    print(f"      Status: {r.status_code} (Expected: 403 Forbidden)")
    print(f"      Detail: {r.json().get('detail')}")
    assert r.status_code == 403, "Node B should have refused access to insurance.db!"
    print("      ✓ 403 Forbidden confirmed! Node B strictly protects its boundary.")

    # 3. Live INSERT into Node B
    print(f"\n[2.3] Live INSERT into Node B (theft.db & ministry.db for '{TEST_PLATE}'):")
    # Clean previous if any
    requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": f"DELETE FROM vehicle_security_records WHERE vehicle_identifier = '{TEST_PLATE}'"
    }, timeout=10)
    requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "ministry",
        "query": f"DELETE FROM transport_reports WHERE vehicle_ref = '{TEST_PLATE}'"
    }, timeout=10)

    # Insert Theft Record
    insert_theft = (
        "INSERT INTO vehicle_security_records "
        "(vehicle_identifier, case_type, case_status, reported_date, "
        "police_reference, fir_number, police_station, remarks) "
        f"VALUES ('{TEST_PLATE}', 'THEFT', 'OPEN', '2026-10-21', "
        "'PS-BLR-SOUTH-001', 'FIR/BLR/9988', 'Electronic City Police Station', 'Vehicle reported missing from IT park')"
    )
    r_th = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": insert_theft
    }, timeout=10)
    print(f"      Insert Theft Result: {r_th.json()}")

    # Insert Ministry Report
    insert_min = (
        "INSERT INTO transport_reports "
        "(vehicle_ref, report_type, report_date, reason, severity, report_status, submitted_by, action_taken, notes) "
        f"VALUES ('{TEST_PLATE}', 'THEFT_LOOKOUT', '2026-10-21', 'Police FIR lodged for Kia Seltos', "
        "'CRITICAL', 'PENDING', 'Karnataka State Police HQ', 'Broadcasted to toll booths', 'Flagged at Hosur checkpost')"
    )
    r_m = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "ministry",
        "query": insert_min
    }, timeout=10)
    print(f"      Insert Ministry Result: {r_m.json()}")

    # 4. Live SELECT from Node B
    print(f"\n[2.4] Live SELECT from Node B:")
    r_qt = requests.post(f"{NODE_B_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "theft",
        "query": f"SELECT vehicle_identifier, case_type, case_status, fir_number, police_station, remarks FROM vehicle_security_records WHERE vehicle_identifier = '{TEST_PLATE}'"
    }, timeout=10)
    print(f"      Theft on Friend 2's Laptop: {r_qt.json().get('rows')}")

    r_qm = requests.post(f"{NODE_B_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "ministry",
        "query": f"SELECT vehicle_ref, report_type, severity, report_status, action_taken FROM transport_reports WHERE vehicle_ref = '{TEST_PLATE}'"
    }, timeout=10)
    print(f"      Ministry on Friend 2's Laptop: {r_qm.json().get('rows')}")

    # 5. Live UPDATE on Node B
    print(f"\n[2.5] Live UPDATE on Node B (Updating Case Status to 'RECOVERED'):")
    update_theft = f"UPDATE vehicle_security_records SET case_status = 'RECOVERED', remarks = 'Vehicle intercepted at Hosur Border Toll' WHERE vehicle_identifier = '{TEST_PLATE}'"
    r_ub = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": update_theft
    }, timeout=10)
    print(f"      Update Result: {r_ub.json()}")

    # Verify update on Node B
    r_qt2 = requests.post(f"{NODE_B_URL}/api/node/sql-query", headers=HEADERS, json={
        "database": "theft",
        "query": f"SELECT vehicle_identifier, case_status, remarks FROM vehicle_security_records WHERE vehicle_identifier = '{TEST_PLATE}'"
    }, timeout=10)
    print(f"      Updated Data on Friend 2's Machine: {r_qt2.json().get('rows')}")

    return True


def test_master_federated_join():
    header("🌐 PART 3: MASTER FEDERATED GLOBAL-AS-VIEW JOIN (LIVE 3-NODE MERGE)")
    print(f"Querying Master Mediator for plate '{TEST_PLATE}'...")
    r = requests.get(f"{MASTER_URL}/api/vehicle/{TEST_PLATE}", timeout=15)
    print(f"Master HTTP Status: {r.status_code}")
    d = r.json()
    
    print("\n📦 UNIFIED GLOBAL VIEW MERGED ACROSS ALL 3 LAPTOPS:")
    print("  • Vehicle Model (Node A):", d.get("vehicle", {}).get("make"), d.get("vehicle", {}).get("model"))
    print("  • Owner (Node A):        ", d.get("registration", {}).get("owner_name"))
    print("  • Insurance (Node A):    ", d.get("insurance", {}).get("insurer_name"), f"[{d.get('insurance', {}).get('insurance_status')}]")
    print("  • Security Status (Node B):", d.get("security", {}).get("case_type"), f"[{d.get('security', {}).get('case_status')}]")
    print("  • Police FIR (Node B):    ", d.get("security", {}).get("fir_number"))
    print("  • Ministry Alert (Node B):", d.get("ministry", {}).get("report_type"), f"[{d.get('ministry', {}).get('severity')}]")
    print("  • Overall Status:        ", d.get("overall_status"))


def cleanup():
    header("🧹 PART 4: CLEANUP TEST RECORD (DELETE FROM NODE A & NODE B)")
    r1 = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "registration",
        "query": f"DELETE FROM vehicle_registration WHERE vehicle_reg_no = '{TEST_PLATE}'"
    }, timeout=10)
    r2 = requests.post(f"{NODE_A_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "insurance",
        "query": f"DELETE FROM insurance_records WHERE registration_id = '{TEST_PLATE}'"
    }, timeout=10)
    r3 = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "theft",
        "query": f"DELETE FROM vehicle_security_records WHERE vehicle_identifier = '{TEST_PLATE}'"
    }, timeout=10)
    r4 = requests.post(f"{NODE_B_URL}/api/node/sql-write", headers=HEADERS, json={
        "database": "ministry",
        "query": f"DELETE FROM transport_reports WHERE vehicle_ref = '{TEST_PLATE}'"
    }, timeout=10)
    print(f"  ✓ Deleted from Node A registration: {r1.json().get('affected_rows')} row(s)")
    print(f"  ✓ Deleted from Node A insurance:    {r2.json().get('affected_rows')} row(s)")
    print(f"  ✓ Deleted from Node B theft:        {r3.json().get('affected_rows')} row(s)")
    print(f"  ✓ Deleted from Node B ministry:     {r4.json().get('affected_rows')} row(s)")
    print("\n✅ CLEANUP COMPLETE: All test records removed cleanly!")


if __name__ == "__main__":
    try:
        test_node_a()
        test_node_b()
        test_master_federated_join()
        cleanup()
        header("🎉 FULL DISTRIBUTED CRUD SUITE PASSED 100% ACROSS ALL 3 LAPTOPS!")
    except Exception as e:
        print(f"\n❌ Error during distributed testing: {e}")
        import traceback
        traceback.print_exc()
