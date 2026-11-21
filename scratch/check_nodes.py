import requests
import json

headers = {
    "ngrok-skip-browser-warning": "true",
    "Content-Type": "application/json"
}

print("Checking Node A (https://mooned-antics-shorter.ngrok-free.dev)...")
try:
    rA = requests.get("https://mooned-antics-shorter.ngrok-free.dev/api/node/health", headers=headers, timeout=5)
    print("Node A Health Status:", rA.status_code, rA.text[:200])
except Exception as e:
    print("Node A Error:", e)

try:
    rA_q = requests.post("https://mooned-antics-shorter.ngrok-free.dev/api/node/sql-query", headers=headers, json={"database": "registration", "query": "SELECT COUNT(*) FROM vehicle_registration"}, timeout=5)
    print("Node A Count Reg:", rA_q.status_code, rA_q.text[:200])
except Exception as e:
    print("Node A Query Error:", e)

print("\nChecking Node B (https://manhood-overcome-copartner.ngrok-free.dev)...")
try:
    rB = requests.get("https://manhood-overcome-copartner.ngrok-free.dev/api/node/health", headers=headers, timeout=5)
    print("Node B Health Status:", rB.status_code, rB.text[:200])
except Exception as e:
    print("Node B Error:", e)

try:
    rB_q = requests.post("https://manhood-overcome-copartner.ngrok-free.dev/api/node/sql-query", headers=headers, json={"database": "theft", "query": "SELECT COUNT(*) FROM vehicle_security_records"}, timeout=5)
    print("Node B Count Theft:", rB_q.status_code, rB_q.text[:200])
except Exception as e:
    print("Node B Query Error:", e)
