import requests
import json

url = "https://manhood-overcome-copartner.ngrok-free.dev"
headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

# 1. Check if DL7CQ1939 is already there
r = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "theft",
    "query": "SELECT * FROM vehicle_security_records WHERE vehicle_identifier = 'DL7CQ1939'"
}, timeout=10)
existing = r.json().get("rows", [])

if not existing:
    insert_sql = (
        "INSERT INTO vehicle_security_records "
        "(vehicle_identifier, case_type, case_status, reported_date, police_reference, fir_number, police_station, remarks) "
        "VALUES ('DL7CQ1939', 'THEFT', 'OPEN', '2026-10-21', 'PS-DELHI-007', 'FIR-DEL-7719', 'Sarita Vihar Police Station', 'Active theft alert broadcasted in Delhi NCR')"
    )
    res = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
        "database": "theft",
        "query": insert_sql
    }, timeout=10)
    print("INSERT RESULT:", res.json())
else:
    print("Record already exists on Node B!")

# 2. Also insert a Ministry compliance record for DL7CQ1939 so both databases have it!
r_min = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "ministry",
    "query": "SELECT * FROM transport_reports WHERE vehicle_ref = 'DL7CQ1939'"
}, timeout=10)
existing_min = r_min.json().get("rows", [])

if not existing_min:
    insert_min = (
        "INSERT INTO transport_reports "
        "(vehicle_ref, report_type, report_date, reason, severity, report_status, submitted_by, action_taken, notes) "
        "VALUES ('DL7CQ1939', 'THEFT_ALERT', '2026-10-21', 'Police FIR lodged for stolen Hyundai Creta', 'CRITICAL', 'ACTIONED', 'Delhi Police Crime Branch', 'Checkpoint scanning alerted', 'High alert at Delhi NCR border tolls')"
    )
    res_min = requests.post(f"{url}/api/node/sql-write", headers=headers, json={
        "database": "ministry",
        "query": insert_min
    }, timeout=10)
    print("MINISTRY INSERT RESULT:", res_min.json())
else:
    print("Ministry record already exists on Node B!")

# 3. Verify final state
r_check = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "theft",
    "query": "SELECT case_id, vehicle_identifier, case_type, case_status, remarks FROM vehicle_security_records WHERE vehicle_identifier = 'DL7CQ1939'"
}, timeout=10)
print("\nFINAL THEFT RECORD ON NODE B:", json.dumps(r_check.json().get("rows"), indent=2))

r_min_check = requests.post(f"{url}/api/node/sql-query", headers=headers, json={
    "database": "ministry",
    "query": "SELECT report_id, vehicle_ref, report_type, severity, report_status, notes FROM transport_reports WHERE vehicle_ref = 'DL7CQ1939'"
}, timeout=10)
print("\nFINAL MINISTRY RECORD ON NODE B:", json.dumps(r_min_check.json().get("rows"), indent=2))
