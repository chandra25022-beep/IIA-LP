"""
Check Connection Status of Distributed Nodes (Node A & Node B)
Usage: python scripts/check_nodes.py
"""
import os
import sys
from pathlib import Path

# Load environment
base_dir = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(base_dir / ".env")
    load_dotenv(base_dir / "backend" / ".env")
except Exception:
    pass

import requests

NODE_A_URL = os.getenv("NODE_B_URL", "https://mooned-antics-shorter.ngrok-free.dev")
NODE_B_URL = os.getenv("NODE_C_URL", "https://manhood-overcome-copartner.ngrok-free.dev")

headers = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "ClusterHealthCheck/1.0",
}

print("\n" + "=" * 70)
print(" 🌐 DISTRIBUTED CLUSTER CONNECTION & NGROK STATUS CHECK")
print("=" * 70)

nodes = [
    {
        "name": "Node A (Friend 1 / Laptop 2)",
        "role": "National Insurance & Vehicle Registration Authority",
        "databases": ["insurance.db", "registration.db"],
        "port": 8001,
        "url": NODE_A_URL,
    },
    {
        "name": "Node B (Friend 2 / Laptop 3)",
        "role": "Police Crime Bureau & Ministry of Transport Authority",
        "databases": ["theft.db", "ministry.db"],
        "port": 8002,
        "url": NODE_B_URL,
    },
]

all_online = True

for n in nodes:
    name = n["name"]
    url = n["url"]
    role = n["role"]
    dbs = ", ".join(n["databases"])
    port = n["port"]

    print(f"\n[*] Probing {name}...")
    print(f"    - Role:      {role}")
    print(f"    - Databases: {dbs}")
    print(f"    - Target URL: {url}")

    try:
        r = requests.get(f"{url}/api/node/health", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            owns = ", ".join(data.get("owns", []))
            print(f"    - Status:    🟢 ONLINE (HTTP 200 OK)")
            print(f"    - Confirmed Ownership: [{owns}]")
            print(f"    - Tunnel:    ngrok active & responding!")
        else:
            all_online = False
            print(f"    - Status:    🔴 OFFLINE (HTTP {r.status_code})")
            print(f"    - Cause:     ngrok tunnel is not active on this URL.")
            print(f"    - Fix:       Ask your friend to run:")
            print(f"                 1) start_node_{name[5]}.bat")
            print(f"                 2) ngrok http {port}")
    except requests.exceptions.Timeout:
        all_online = False
        print(f"    - Status:    🔴 OFFLINE (Connection Timed Out)")
        print(f"    - Cause:     Laptop is sleeping or ngrok is closed.")
    except Exception as e:
        all_online = False
        print(f"    - Status:    🔴 OFFLINE ({type(e).__name__})")
        print(f"    - Error:     {str(e)[:80]}")

print("\n" + "-" * 70)
if all_online:
    print(" 🎉 ALL REMOTE NODES ARE LIVE AND CONNECTED! Ready for evaluation.")
else:
    print(" ℹ️  NOTE: Master has automatic local fallback enabled.")
    print("     If any node is offline, Master queries local SQLite copies in 3ms.")
    print("     The demo will still work completely with 0 downtime!")
print("=" * 70 + "\n")
