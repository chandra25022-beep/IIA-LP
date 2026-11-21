"""Phase 3 Comprehensive Verification Script"""
import requests, json, time, sqlite3, os

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:5173"
DB_DIR = "data"  # DBs are directly in data/, not data/databases/

results = []

def test(name, passed, detail):
    status = "PASS" if passed else "FAIL"
    results.append((status, name, detail))
    icon = "✓" if passed else "✗"
    print(f"  [{status}] {icon} {name}: {detail}")

print("=" * 70)
print("PHASE 3 COMPREHENSIVE VERIFICATION")
print("=" * 70)

# 1. Server health
print("\n--- 1. SERVER HEALTH ---")
try:
    r = requests.get(f"{BASE}/api/health", timeout=5)
    test("Backend health", r.status_code == 200, f"Status {r.status_code}")
except Exception as e:
    test("Backend health", False, str(e))

try:
    r = requests.get(FRONTEND, timeout=5)
    test("Frontend loads", r.status_code == 200, f"Status {r.status_code}, {len(r.text)} bytes")
except Exception as e:
    test("Frontend loads", False, str(e))

# 2. Phase 1-2 endpoints
print("\n--- 2. PHASE 1-2 ENDPOINTS ---")
for ep in ["/api/nodes/status", "/api/data-sources", "/api/course-concepts"]:
    try:
        r = requests.get(f"{BASE}{ep}", timeout=10)
        body = r.json()
        if isinstance(body, list):
            detail = f"OK, {len(body)} items"
        elif isinstance(body, dict):
            detail = f"OK, keys={list(body.keys())[:5]}"
        else:
            detail = "OK"
        test(f"GET {ep}", r.status_code == 200, detail)
    except Exception as e:
        test(f"GET {ep}", False, str(e))

# 3. Phase 3 endpoints
print("\n--- 3. PHASE 3 ENDPOINTS ---")

# Context search with CORRECT field name 'plate'
try:
    t0 = time.time()
    r = requests.post(f"{BASE}/api/context-search", json={"plate": "DL7CQ1939"}, timeout=30)
    elapsed = time.time() - t0
    test("POST /api/context-search", r.status_code == 200, f"Status {r.status_code}, {elapsed:.2f}s")
    if r.status_code == 200:
        data = r.json()
        nq = data.get("nodes_queried", 0)
        test("  → nodes_queried", nq >= 1, f"{nq} nodes")
        sr = data.get("structured_results", {})
        test("  → structured_results", len(sr) > 0, f"{len(sr)} DBs: {list(sr.keys())}")
        fk = data.get("fk_tables_joined", 0)
        test("  → fk_tables_joined", fk > 0, f"{fk} FK joins")
        ur = data.get("unstructured_results", [])
        test("  → unstructured_results", len(ur) > 0, f"{len(ur)} docs matched")
        cs = data.get("context_summary", "")
        test("  → context_summary", len(cs) > 0, f"{len(cs)} chars")
        perf = data.get("performance", {})
        test("  → performance.total_ms", perf.get("total_ms", 0) > 0, f"{perf.get('total_ms')}ms total")
        dp = data.get("distributed_processing", {})
        na_status = dp.get("node_a", {}).get("status", "?")
        nb_status = dp.get("node_b", {}).get("status", "?")
        test("  → distributed_processing", len(dp) >= 3, f"master + node_a({na_status}) + node_b({nb_status})")
    else:
        print(f"    Response: {r.text[:300]}")
except Exception as e:
    test("POST /api/context-search", False, str(e))

# Schema graph
try:
    r2 = requests.get(f"{BASE}/api/context-search/schema-graph", timeout=10)
    d2 = r2.json()
    total_tables = d2.get("total_tables", 0)
    total_fk = d2.get("total_fk_relationships", 0)
    dbs = list(d2.get("databases", {}).keys())
    test("GET schema-graph", r2.status_code == 200 and total_tables == 21, 
         f"{total_tables} tables, {total_fk} FK rels, dbs={dbs}")
except Exception as e:
    test("GET schema-graph", False, str(e))

# Unstructured stats
try:
    r3 = requests.get(f"{BASE}/api/context-search/unstructured-stats", timeout=10)
    d3 = r3.json()
    stats = d3.get("stats", {})
    total_docs = stats.get("total_documents", 0)
    total_tokens = stats.get("total_tokens", 0)
    test("GET unstructured-stats", r3.status_code == 200 and total_docs >= 10, 
         f"{total_docs} docs, {total_tokens} tokens")
except Exception as e:
    test("GET unstructured-stats", False, str(e))

# 4. Database verification
print("\n--- 4. DATABASE VERIFICATION (21 tables across 5 DBs) ---")
dbs_config = {
    "capture.db": ["cameras", "vehicle_capture", "capture_alerts", "operator_logs"],
    "registration.db": ["vehicle_owners", "vehicle_registration", "vehicle_specs", "rto_transactions", "fitness_certificates"],
    "insurance.db": ["insurance_policies", "insurance_claims", "policy_endorsements", "premium_payments"],
    "theft.db": ["vehicle_security_records", "investigation_details", "recovery_records", "suspect_info"],
    "ministry.db": ["transport_reports", "enforcement_actions", "compliance_history", "blacklisted_vehicles"],
}
total_tables_found = 0
for db_name, tables in dbs_config.items():
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path):
        test(f"DB {db_name}", False, "FILE NOT FOUND")
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for tbl in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            cnt = cur.fetchone()[0]
            test(f"  {db_name}/{tbl}", cnt > 0, f"{cnt} rows")
            total_tables_found += 1
        except Exception as e:
            test(f"  {db_name}/{tbl}", False, str(e))
    conn.close()

print(f"\n  Total tables verified: {total_tables_found}/21")

# 5. FK-PK join verification
print("\n--- 5. FK-PK JOIN QUERIES ---")
fk_tests = [
    ("capture.db", "SELECT vc.plate_number, c.location, ca.alert_type FROM vehicle_capture vc JOIN cameras c ON vc.camera_id = c.camera_id LEFT JOIN capture_alerts ca ON vc.capture_id = ca.capture_id LIMIT 3"),
    ("registration.db", "SELECT vr.vehicle_reg_no, vo.owner_name, vs.engine_cc FROM vehicle_registration vr JOIN vehicle_owners vo ON vr.owner_id = vo.owner_id JOIN vehicle_specs vs ON vr.vehicle_reg_no = vs.vehicle_reg_no LIMIT 3"),
    ("insurance.db", "SELECT ip.policy_number, ic.claim_id, ic.claim_amount FROM insurance_policies ip JOIN insurance_claims ic ON ip.policy_id = ic.policy_id LIMIT 3"),
    ("theft.db", "SELECT vsr.vehicle_identifier, id.investigation_id, si.suspect_name FROM vehicle_security_records vsr JOIN investigation_details id ON vsr.record_id = id.record_id LEFT JOIN suspect_info si ON id.investigation_id = si.investigation_id LIMIT 3"),
    ("ministry.db", "SELECT tr.vehicle_ref, ea.action_type, bv.reason FROM transport_reports tr JOIN enforcement_actions ea ON tr.report_id = ea.report_id LEFT JOIN blacklisted_vehicles bv ON tr.vehicle_ref = bv.vehicle_ref LIMIT 3"),
]
for db_name, query in fk_tests:
    db_path = os.path.join(DB_DIR, db_name)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        test(f"FK join in {db_name}", len(rows) > 0, f"{len(rows)} rows, sample: {rows[0]}")
    except Exception as e:
        test(f"FK join in {db_name}", False, str(e))

# 6. Unstructured data files
print("\n--- 6. UNSTRUCTURED DATA FILES ---")
unstr_dir = "data/unstructured"
if os.path.exists(unstr_dir):
    files = sorted([f for f in os.listdir(unstr_dir) if f.endswith('.txt')])
    test("Unstructured files count", len(files) >= 10, f"{len(files)} .txt files")
    for f in files:
        fpath = os.path.join(unstr_dir, f)
        size = os.path.getsize(fpath)
        test(f"  {f}", size > 100, f"{size} bytes")
else:
    test("Unstructured dir", False, "NOT FOUND")

# 7. Frontend pages
print("\n--- 7. FRONTEND PAGES ---")
for page in ["/", "/context", "/query"]:
    try:
        r = requests.get(f"{FRONTEND}{page}", timeout=5)
        test(f"Frontend {page}", r.status_code == 200, f"{r.status_code}, {len(r.text)} bytes")
    except Exception as e:
        test(f"Frontend {page}", False, str(e))

# 8. Context search with different plates
print("\n--- 8. CONTEXT SEARCH - MULTIPLE PLATES ---")
for plate in ["DL7CQ1939", "MH12AB1234", "KA01MN5678"]:
    try:
        t0 = time.time()
        r = requests.post(f"{BASE}/api/context-search", json={"plate": plate}, timeout=30)
        elapsed = time.time() - t0
        d = r.json() if r.status_code == 200 else {}
        nq = d.get('nodes_queried', 0)
        fk = d.get('fk_tables_joined', 0)
        ur_count = len(d.get('unstructured_results', []))
        test(f"Search '{plate}'", r.status_code == 200,
             f"nodes={nq}, fk={fk}, unstruct={ur_count}, time={elapsed:.2f}s")
    except Exception as e:
        test(f"Search '{plate}'", False, str(e))

# 9. SQL query endpoint
print("\n--- 9. SQL QUERY ENDPOINT ---")
try:
    r = requests.post(f"{BASE}/api/sql/query", json={"query": "SELECT COUNT(*) as cnt FROM vehicle_capture", "database": "capture"}, timeout=10)
    test("SQL query (capture)", r.status_code == 200, f"Status {r.status_code}, result={r.json().get('results', [{}])[0] if r.status_code == 200 else 'N/A'}")
except Exception as e:
    test("SQL query (capture)", False, str(e))

try:
    r = requests.post(f"{BASE}/api/sql/query", json={"query": "SELECT COUNT(*) as cnt FROM insurance_policies", "database": "insurance"}, timeout=10)
    test("SQL query (insurance)", r.status_code == 200, f"Status {r.status_code}, result={r.json().get('results', [{}])[0] if r.status_code == 200 else 'N/A'}")
except Exception as e:
    test("SQL query (insurance)", False, str(e))

# Summary
print("\n" + "=" * 70)
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
total = len(results)
pct = (passed / total * 100) if total > 0 else 0
print(f"RESULTS: {passed}/{total} PASSED ({pct:.0f}%), {failed} FAILED")
if failed == 0:
    print("\n🎉 ALL TESTS PASSED! Ready for evaluation!")
else:
    print(f"\n⚠ FAILED tests ({failed}):")
    for s, n, d in results:
        if s != "PASS":
            print(f"  [{s}] {n}: {d}")
print("=" * 70)
