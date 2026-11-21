# 🚓 IIA Project — Node B Setup Guide (Friend 2 / Laptop 3)

> **Node Role:** Police Stolen Vehicle Bureau & Ministry of Transport Authority  
> **Databases Owned:** `theft.db` + `ministry.db`  
> **Port:** `8002`  
> **Network Mode:** Local WiFi / Mobile Hotspot OR Cross-Network via ngrok  

---

## 📋 What You Need
1. **Windows Laptop** with **Python 3.10+** installed (check by running `python --version` in terminal).
2. Git installed (or download the ZIP of this branch).

---

## ⚡ Option 1: Quick Start (1-Click)
1. Clone the repository and checkout branch `node-b`:
   ```bash
   git clone <REPO_URL> -b node-b
   cd Car_Project
   ```
2. Double-click the file:
   👉 **`start_node_B_theft_ministry.bat`** (or `node_backend/start_node_B.bat`)

It will automatically:
- Create a Python virtual environment (`venv`)
- Install `fastapi`, `uvicorn`, and `requests`
- Find your local IP address
- Start the FastAPI server on port `8002`

---

## 🛠 Option 2: Step-by-Step Manual Setup in Terminal

Open **PowerShell** or **Command Prompt** inside the cloned folder:

```powershell
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install requirements
pip install -r node_backend/requirements.txt

# 3. Set environment variables
$env:NODE_DATABASES="theft,ministry"
$env:NODE_PORT="8002"
$env:NODE_HOST="0.0.0.0"

# 4. Start the server
cd node_backend
python main.py
```

---

## 🌐 Connecting with Master Node

### Scenario A: You and Master are on the **SAME WiFi / Hotspot**
1. Check your laptop's local IP address:
   ```cmd
   ipconfig
   ```
   Look for `IPv4 Address`, e.g., `192.168.1.18`.
2. Send this URL to the Master:
   👉 `http://192.168.1.18:8002`
3. Verify it works in your browser: [http://localhost:8002/api/health](http://localhost:8002/api/health)

---

### Scenario B: You and Master are on **DIFFERENT Networks** (Using ngrok)
1. Install ngrok (if not already installed):
   ```cmd
   winget install ngrok.ngrok
   ```
   *(Or download from https://ngrok.com)*
2. Sign up for a free ngrok account and paste your authtoken:
   ```cmd
   ngrok config add-authtoken YOUR_FREE_TOKEN
   ```
3. Start the tunnel in a new terminal:
   ```cmd
   ngrok http 8002
   ```
4. Copy the public forwarding URL (e.g. `https://c3d4-xxx.ngrok-free.app`) and send it to the Master!

---

## 🔍 Verification & Health Check
Open your browser to:
- Health check: [http://localhost:8002/api/health](http://localhost:8002/api/health)
- Databases exposed: [http://localhost:8002/api/sources](http://localhost:8002/api/sources)
- Interactive Swagger docs: [http://localhost:8002/docs](http://localhost:8002/docs)

You are all set! The Master will query your node to federate Theft and Ministry blacklists in real time.

---

## 🧩 Phase 3: Context Discovery (NEW)

Your node now supports **Phase 3 Context Discovery** with expanded databases:

### Database Tables (FK-PK Relationships)
**theft.db** (4 tables):
- `vehicle_security_records` — Primary table (FK: `vehicle_identifier`)
- `investigation_details` — FK: `case_id` → `vehicle_security_records`
- `recovery_records` — FK: `case_id` → `vehicle_security_records`
- `suspect_info` — FK: `case_id` → `vehicle_security_records`

**ministry.db** (4 tables):
- `transport_reports` — Primary table (FK: `vehicle_ref`)
- `enforcement_actions` — FK: `report_id` → `transport_reports`
- `compliance_history` — FK: `report_id` → `transport_reports`
- `blacklisted_vehicles` — Direct lookup by `vehicle_ref`

### New Endpoint
```
POST /api/node/context-query
Body: {"plate": "DL7CQ1939", "context_hints": []}
```
This endpoint:
1. Looks up the plate in both `theft.db` and `ministry.db`
2. Performs LOCAL FK-PK joins across all related tables
3. Returns a **minimal context summary** (risk flags, keywords) — NOT a raw data dump
4. Reports internal processing time

### Test It
```bash
curl -X POST http://localhost:8002/api/node/context-query \
  -H "Content-Type: application/json" \
  -d '{"plate":"DL7CQ1939"}'
```

The response will show FK tables joined (e.g., `investigation_details`, `recovery_records`, `enforcement_actions`), risk flags (e.g., `ACTIVELY_STOLEN`, `BLACKLISTED`), and context keywords extracted from the data.
