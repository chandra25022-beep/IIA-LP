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
