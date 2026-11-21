"""Final comprehensive verification with CORRECT response structure"""
import requests, json, time, sqlite3, os

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:5173"
DB_DIR = "data"
results = []

def test(name, passed, detail):
    status = "PASS" if passed else "FAIL"
    results.append((status, name, detail))
    icon = "✓" if passed else "✗"
    print(f"  [{status}] {icon} {name}: {detail}")

print("=" * 70)
print("PHASE 3 FINAL VERIFICATION — " + time.strftime("%Y-%m-%d %H:%M:%S"))
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
    test("Frontend loads", r.status_code == 200, f"{len(r.text)} bytes")
except Exception as e:
    test("Frontend loads", False, str(e))

# 2. Phase 1-2 endpoints
print("\n--- 2. PHASE 1-2 ENDPOINTS ---")
for ep in ["/api/data-sources", "/api/course-concepts"]:
    try:
        r = requests.get(f"{BASE}{ep}", timeout=10)
        test(f"GET {ep}", r.status_code == 200, "OK")
    except Exception as e:
        test(f"GET {ep}", False, str(e))

# 3. Phase 3 — Context Search (the main endpoint)
print("\n--- 3. PHASE 3: CONTEXT SEARCH ---")
try:
    t0 = time.time()
    r = requests.post(f"{BASE}/api/context-search", json={"plate": "DL7CQ1939"}, timeout=30)
    elapsed = time.time() - t0
    test("POST /api/context-search", r.status_code == 200, f"Status {r.status_code}, {elapsed:.2f}s")
    if r.status_code == 200:
        data = r.json()
        sc = data.get("structured_context", {})
        test("  → structured_context.nodes_queried", sc.get("nodes_queried", 0) >= 1, f"{sc.get('nodes_queried')} nodes")
        test("  → structured_context.nodes_with_data", sc.get("nodes_with_data", 0) >= 1, f"{sc.get('nodes_with_data')} nodes with data")
        test("  → structured_context.total_fk_tables_joined", sc.get("total_fk_tables_joined", 0) >= 1, f"{sc.get('total_fk_tables_joined')} FK tables")
        pnc = sc.get("per_node_context", [])
        test("  → per_node_context count", len(pnc) >= 1, f"{len(pnc)} node contexts")
        # Check each node context has 'found'
        found_count = sum(1 for c in pnc if c.get("found"))
        test("  → nodes with data found", found_count >= 1, f"{found_count} nodes have data")

        # Risk assessment
        ra = data.get("risk_assessment", {})
        test("  → risk_assessment", "risk_score" in ra, f"score={ra.get('risk_score')}, level={ra.get('risk_level')}")

        # Accumulated keywords
        kw = data.get("accumulated_keywords", [])
        test("  → accumulated_keywords", len(kw) >= 3, f"{len(kw)} keywords: {kw[:5]}")

        # Unstructured data
        ud = data.get("unstructured_data", {})
        test("  → unstructured_data.documents_found", ud.get("documents_found", 0) >= 1, f"{ud.get('documents_found')} docs")
        ur = ud.get("results", [])
        test("  → unstructured TF-IDF results", len(ur) >= 1, f"{len(ur)} docs matched")
        if ur:
            top_doc = ur[0]
            test("  → top doc has relevance_score", top_doc.get("relevance_score", 0) > 0, 
                 f"{top_doc.get('document')}: {top_doc.get('relevance_score')}")
            test("  → top doc has matched_keywords", len(top_doc.get("matched_keywords", [])) > 0,
                 f"{top_doc.get('matched_keywords', [])[:3]}")
            test("  → top doc has snippet", len(top_doc.get("snippet", "")) > 0,
                 f"{len(top_doc.get('snippet', ''))} chars")

        # Integration metadata
        im = data.get("integration_metadata", {})
        test("  → integration_metadata", "rubric_coverage" in im, im.get("phase", "?"))

        # Performance
        perf = data.get("performance", {})
        test("  → performance.total_ms", perf.get("total_ms", 0) > 0, f"{perf.get('total_ms')}ms")

        # Distributed processing
        dp = data.get("distributed_processing", {})
        test("  → distributed_processing", len(dp) >= 3, f"master + node_a + node_b")
except Exception as e:
    test("POST /api/context-search", False, str(e))

# 4. Phase 3 — Schema Graph
print("\n--- 4. PHASE 3: SCHEMA GRAPH ---")
try:
    r2 = requests.get(f"{BASE}/api/context-search/schema-graph", timeout=10)
    d2 = r2.json()
    test("GET schema-graph", r2.status_code == 200 and d2.get("total_tables") == 21,
         f"{d2.get('total_tables')} tables, {d2.get('total_fk_relationships')} FK rels")
    dbs = list(d2.get("databases", {}).keys())
    test("  → 5 databases", len(dbs) == 5, str(dbs))
except Exception as e:
    test("GET schema-graph", False, str(e))

# 5. Phase 3 — Unstructured Stats
print("\n--- 5. PHASE 3: UNSTRUCTURED STATS ---")
try:
    r3 = requests.get(f"{BASE}/api/context-search/unstructured-stats", timeout=10)
    d3 = r3.json()
    stats = d3.get("stats", {})
    test("GET unstructured-stats", r3.status_code == 200 and stats.get("total_documents", 0) >= 10,
         f"{stats.get('total_documents')} docs, {stats.get('total_unique_tokens')} tokens")
except Exception as e:
    test("GET unstructured-stats", False, str(e))

# 6. Database verification (21 tables)
print("\n--- 6. DATABASE TABLES (21 tables across 5 DBs) ---")
dbs_config = {
    "capture.db": ["cameras", "vehicle_capture", "capture_alerts", "operator_logs"],
    "registration.db": ["vehicle_owners", "vehicle_registration", "vehicle_specs", "rto_transactions", "fitness_certificates"],
    "insurance.db": ["insurance_policies", "insurance_claims", "policy_endorsements", "premium_payments"],
    "theft.db": ["vehicle_security_records", "investigation_details", "recovery_records", "suspect_info"],
    "ministry.db": ["transport_reports", "enforcement_actions", "compliance_history", "blacklisted_vehicles"],
}
total_ok = 0
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
            total_ok += 1
        except Exception as e:
            test(f"  {db_name}/{tbl}", False, str(e))
    conn.close()
print(f"  Tables verified: {total_ok}/21")

# 7. Unstructured data files
print("\n--- 7. UNSTRUCTURED DATA FILES ---")
unstr_dir = "data/unstructured"
if os.path.exists(unstr_dir):
    files = sorted([f for f in os.listdir(unstr_dir) if f.endswith('.txt')])
    test("Unstructured files", len(files) >= 10, f"{len(files)} .txt files")
else:
    test("Unstructured dir", False, "NOT FOUND")

# 8. Frontend pages
print("\n--- 8. FRONTEND PAGES ---")
for page in ["/", "/context", "/query"]:
    try:
        r = requests.get(f"{FRONTEND}{page}", timeout=5)
        test(f"Frontend {page}", r.status_code == 200, "OK")
    except Exception as e:
        test(f"Frontend {page}", False, str(e))

# 9. SQL query endpoint (correct URL)
print("\n--- 9. SQL QUERY ENDPOINT ---")
try:
    r = requests.post(f"{BASE}/api/sql-query", json={"query": "SELECT COUNT(*) as cnt FROM vehicle_capture", "database": "capture"}, timeout=10)
    test("SQL query (capture)", r.status_code == 200, f"Result: {r.json().get('results', [{}])}")
except Exception as e:
    test("SQL query (capture)", False, str(e))

# Summary
print("\n" + "=" * 70)
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
total = len(results)
pct = (passed / total * 100) if total > 0 else 0
print(f"RESULTS: {passed}/{total} PASSED ({pct:.0f}%), {failed} FAILED")
if failed == 0:
    print("\n🎉 ALL TESTS PASSED! System ready for Phase 3 evaluation!")
else:
    print(f"\n⚠ FAILED tests ({failed}):")
    for s, n, d in results:
        if s != "PASS":
            print(f"  [{s}] {n}: {d}")
print("=" * 70)
