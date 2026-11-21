import requests, json, time, sqlite3, os

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:5173"
results = []

def test(name, func):
    try:
        ok, detail = func()
        status = "PASS" if ok else "FAIL"
        results.append((status, name, detail))
        print(f"  [{status}] {name}: {detail}")
    except Exception as e:
        results.append(("ERROR", name, str(e)))
        print(f"  [ERROR] {name}: {e}")

print("=" * 70)
print("PHASE 3 COMPREHENSIVE VERIFICATION")
print("=" * 70)

# 1. Server health
print("\n--- 1. SERVER HEALTH ---")
test("Backend health", lambda: (
    requests.get(f"{BASE}/api/health", timeout=5).status_code == 200,
    f"Status {requests.get(f'{BASE}/api/health', timeout=5).status_code}"
))
test("Frontend loads", lambda: (
    requests.get(FRONTEND, timeout=5).status_code == 200,
    f"Status {requests.get(FRONTEND, timeout=5).status_code}, {len(requests.get(FRONTEND, timeout=5).text)} bytes"
))

# 2. Phase 1-2 endpoints
print("\n--- 2. PHASE 1-2 ENDPOINTS ---")
for ep in ["/api/nodes/status", "/api/data-sources", "/api/course-concepts"]:
    test(f"GET {ep}", lambda ep=ep: (
        requests.get(f"{BASE}{ep}", timeout=10).status_code == 200,
        f"OK, {len(requests.get(f'{BASE}{ep}', timeout=10).json())} items" if isinstance(requests.get(f"{BASE}{ep}", timeout=10).json(), list) else "OK"
    ))

# 3. Phase 3 endpoints
print("\n--- 3. PHASE 3 ENDPOINTS ---")

# Context search
t0 = time.time()
r = requests.post(f"{BASE}/api/context-search", json={"plate_number": "DL7CQ1939"}, timeout=30)
elapsed = time.time() - t0
test("POST /api/context-search", lambda: (
    r.status_code == 200,
    f"Status {r.status_code}, {elapsed:.2f}s"
))
if r.status_code == 200:
    data = r.json()
    test("  - nodes_queried", lambda: (data.get("nodes_queried", 0) >= 1, f"{data.get('nodes_queried', 0)} nodes"))
    test("  - has structured_results", lambda: (len(data.get("structured_results", {})) > 0, f"{len(data.get('structured_results', {}))} DBs"))
    test("  - has fk_tables_joined", lambda: (data.get("fk_tables_joined", 0) > 0, f"{data.get('fk_tables_joined', 0)} FK joins"))
    test("  - has unstructured_results", lambda: (len(data.get("unstructured_results", [])) > 0, f"{len(data.get('unstructured_results', []))} docs"))
    test("  - has context_summary", lambda: (len(data.get("context_summary", "")) > 0, f"{len(data.get('context_summary', ''))} chars"))

# Schema graph
r2 = requests.get(f"{BASE}/api/context-search/schema-graph", timeout=10)
test("GET /api/context-search/schema-graph", lambda: (
    r2.status_code == 200,
    f"{len(r2.json().get('tables', []))} tables, {len(r2.json().get('relationships', []))} FK rels"
))

# Unstructured stats
r3 = requests.get(f"{BASE}/api/context-search/unstructured-stats", timeout=10)
test("GET /api/context-search/unstructured-stats", lambda: (
    r3.status_code == 200,
    f"{r3.json().get('total_documents', 0)} docs, {r3.json().get('total_tokens', 0)} tokens"
))

# 4. Database verification
print("\n--- 4. DATABASE VERIFICATION (21 tables across 5 DBs) ---")
db_dir = "data/databases"
dbs = {
    "capture.db": ["cameras", "vehicle_capture", "capture_alerts", "operator_logs"],
    "registration.db": ["vehicle_owners", "vehicle_registration", "vehicle_specs", "rto_transactions", "fitness_certificates"],
    "insurance.db": ["insurance_policies", "insurance_claims", "policy_endorsements", "premium_payments"],
    "theft.db": ["vehicle_security_records", "investigation_details", "recovery_records", "suspect_info"],
    "ministry.db": ["transport_reports", "enforcement_actions", "compliance_history", "blacklisted_vehicles"]
}
total_tables = 0
for db_name, tables in dbs.items():
    db_path = os.path.join(db_dir, db_name)
    if not os.path.exists(db_path):
        test(f"DB {db_name}", lambda: (False, "FILE NOT FOUND"))
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for tbl in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            cnt = cur.fetchone()[0]
            test(f"  {db_name}/{tbl}", lambda cnt=cnt: (cnt > 0, f"{cnt} rows"))
            total_tables += 1
        except Exception as e:
            test(f"  {db_name}/{tbl}", lambda e=e: (False, str(e)))
    conn.close()

# 5. FK-PK join verification
print("\n--- 5. FK-PK JOIN QUERIES ---")
fk_tests = [
    ("registration.db", "SELECT vr.vehicle_reg_no, vo.owner_name, vs.engine_cc FROM vehicle_registration vr JOIN vehicle_owners vo ON vr.owner_id = vo.owner_id JOIN vehicle_specs vs ON vr.vehicle_reg_no = vs.vehicle_reg_no LIMIT 3"),
    ("insurance.db", "SELECT ip.policy_number, ic.claim_id, ic.claim_amount FROM insurance_policies ip JOIN insurance_claims ic ON ip.policy_id = ic.policy_id LIMIT 3"),
    ("theft.db", "SELECT vsr.vehicle_identifier, id.investigation_id, si.suspect_name FROM vehicle_security_records vsr JOIN investigation_details id ON vsr.record_id = id.record_id LEFT JOIN suspect_info si ON id.investigation_id = si.investigation_id LIMIT 3"),
    ("ministry.db", "SELECT tr.vehicle_ref, ea.action_type, bv.reason FROM transport_reports tr JOIN enforcement_actions ea ON tr.report_id = ea.report_id LEFT JOIN blacklisted_vehicles bv ON tr.vehicle_ref = bv.vehicle_ref LIMIT 3"),
]
for db_name, query in fk_tests:
    db_path = os.path.join(db_dir, db_name)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        test(f"FK join in {db_name}", lambda rows=rows: (len(rows) > 0, f"{len(rows)} rows returned"))
    except Exception as e:
        test(f"FK join in {db_name}", lambda e=e: (False, str(e)))

# 6. Unstructured data files
print("\n--- 6. UNSTRUCTURED DATA FILES ---")
unstr_dir = "data/unstructured"
if os.path.exists(unstr_dir):
    files = [f for f in os.listdir(unstr_dir) if f.endswith('.txt')]
    test("Unstructured files count", lambda: (len(files) >= 10, f"{len(files)} .txt files"))
else:
    test("Unstructured dir", lambda: (False, "NOT FOUND"))

# 7. Frontend pages
print("\n--- 7. FRONTEND PAGES ---")
for page in ["/", "/context", "/query"]:
    try:
        r = requests.get(f"{FRONTEND}{page}", timeout=5)
        test(f"Frontend {page}", lambda r=r: (r.status_code == 200, f"{r.status_code}, {len(r.text)} bytes"))
    except Exception as e:
        test(f"Frontend {page}", lambda e=e: (False, str(e)))

# 8. Context search with different plates
print("\n--- 8. CONTEXT SEARCH - MULTIPLE PLATES ---")
for plate in ["DL7CQ1939", "MH12AB1234", "KA01MN5678"]:
    try:
        t0 = time.time()
        r = requests.post(f"{BASE}/api/context-search", json={"plate_number": plate}, timeout=30)
        elapsed = time.time() - t0
        d = r.json() if r.status_code == 200 else {}
        test(f"Search '{plate}'", lambda d=d, elapsed=elapsed: (
            r.status_code == 200,
            f"nodes={d.get('nodes_queried',0)}, fk={d.get('fk_tables_joined',0)}, unstruct={len(d.get('unstructured_results',[]))}, time={elapsed:.2f}s"
        ))
    except Exception as e:
        test(f"Search '{plate}'", lambda e=e: (False, str(e)))

# Summary
print("\n" + "=" * 70)
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
errors = sum(1 for s,_,_ in results if s == "ERROR")
print(f"RESULTS: {passed} PASSED, {failed} FAILED, {errors} ERRORS out of {len(results)} tests")
if failed + errors == 0:
    print("ALL TESTS PASSED! Ready for evaluation!")
else:
    print("\nFAILED/ERROR tests:")
    for s, n, d in results:
        if s != "PASS":
            print(f"  [{s}] {n}: {d}")
print("=" * 70)
