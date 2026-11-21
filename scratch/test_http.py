"""Quick check - actual HTTP response structure"""
import requests, json

r = requests.post("http://localhost:8000/api/context-search", json={"plate": "DL7CQ1939"}, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"\nTop-level keys: {list(data.keys())}")
    print(f"\nstructured_context: {json.dumps(data.get('structured_context', {}), indent=2)[:500]}")
    print(f"\nrisk_assessment: {data.get('risk_assessment')}")
    print(f"\naccumulated_keywords: {data.get('accumulated_keywords', [])[:10]}")
    print(f"\nunstructured_data.documents_found: {data.get('unstructured_data', {}).get('documents_found')}")
    unstr = data.get('unstructured_data', {}).get('results', [])
    print(f"unstructured_data.results count: {len(unstr)}")
    for doc in unstr[:3]:
        print(f"  {doc['document']}: score={doc['relevance_score']}, matched={doc['matched_keywords'][:3]}")
    print(f"\nintegration_metadata: {json.dumps(data.get('integration_metadata', {}), indent=2)}")
    print(f"\nperformance: {json.dumps(data.get('performance', {}), indent=2)}")
    print(f"\ndistributed_processing keys: {list(data.get('distributed_processing', {}).keys())}")
else:
    print(r.text)
