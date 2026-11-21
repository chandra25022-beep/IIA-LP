"""Quick test for Node A context-query endpoint."""
import requests
r = requests.post("http://localhost:8001/api/node/context-query", json={"plate": "DL7CQ1939"})
d = r.json()
print(f"Status: {r.status_code}")
print(f"DBs: {d.get('node_databases')}")
print(f"Processing time: {d.get('processing_time_ms')}ms")
print(f"Phase: {d.get('phase')}")
print(f"Note: {d.get('note')}")
for k, v in d.get("context_results", {}).items():
    found = v.get("found")
    fk = v.get("fk_tables_joined", [])
    risk = v.get("risk_flags", [])
    print(f"  {k}: found={found}, FK tables={fk}, risks={risk}")
