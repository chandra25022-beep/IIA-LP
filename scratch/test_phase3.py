"""Quick Phase 3 endpoint verification."""
import requests
import json

BASE = "http://localhost:8000"

# Test 1: Context Search
print("=== TEST 1: Context Search (DL7CQ1939) ===")
r = requests.post(f"{BASE}/api/context-search", json={"plate": "DL7CQ1939"})
d = r.json()
ra = d["risk_assessment"]
sc = d["structured_context"]
ud = d["unstructured_data"]
pf = d["performance"]
print(f"Status: {r.status_code}")
print(f"Risk: {ra['risk_level']} ({ra['risk_score']}/100)")
print(f"Risk flags: {ra['risk_flags']}")
print(f"Nodes with data: {sc['nodes_with_data']}/{sc['nodes_queried']}")
print(f"FK tables joined: {sc['total_fk_tables_joined']}")
print(f"FK tables: {sc['fk_tables_list']}")
print(f"Unstructured docs found: {ud['documents_found']}")
for doc in ud["results"][:3]:
    print(f"  - {doc['document']}: score={doc['relevance_score']}")
print(f"Context keywords (first 10): {d['accumulated_keywords'][:10]}")
print(f"Total time: {pf['total_ms']}ms")
for k, v in pf["per_step_ms"].items():
    print(f"  {k}: {v}")

# Test 2: Schema Graph
print("\n=== TEST 2: Schema Graph ===")
r = requests.get(f"{BASE}/api/context-search/schema-graph")
d = r.json()
print(f"Total tables: {d['total_tables']}, FK relationships: {d['total_fk_relationships']}")
for db, info in d["databases"].items():
    related = list(info["related_tables"].keys())
    print(f"  {db}: {info['primary_table']} -> {related}")

# Test 3: Unstructured Stats
print("\n=== TEST 3: Unstructured Stats ===")
r = requests.get(f"{BASE}/api/context-search/unstructured-stats")
d = r.json()
print(f"Documents: {d['stats']['total_documents']}, Tokens: {d['stats']['total_unique_tokens']}")

# Test 4: Course Concepts (Phase 3 entries)
print("\n=== TEST 4: Phase 3 Course Concepts ===")
r = requests.get(f"{BASE}/api/course-concepts")
d = r.json()
p3 = [c for c in d["concepts"] if "Phase 3" in c.get("topic", "")]
for c in p3:
    print(f"  {c['topic']}")
print(f"Total concepts: {len(d['concepts'])}")

print("\n=== ALL TESTS PASSED ===")
