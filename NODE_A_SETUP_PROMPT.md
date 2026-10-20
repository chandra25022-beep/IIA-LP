# 🚗 IIA Project — Node A Setup Guide (Friend 1 / Laptop 2)

> **Node Role:** National Insurance & Vehicle Registration Data Authority  
> **Databases Owned:** `insurance.db` + `registration.db`  
> **Port:** `8001`  
> **Network Mode:** Local WiFi / Mobile Hotspot OR Cross-Network via ngrok  

---

## 📋 What You Need
1. **Windows Laptop** with **Python 3.10+** installed (check by running `python --version` in terminal).
2. Git installed (or download the ZIP of this branch).

---

## ⚡ Option 1: Quick Start (1-Click)
1. Clone the repository and checkout branch `node-a`:
   ```bash
   git clone <REPO_URL> -b node-a
   cd Car_Project
   ```
2. Double-click the file:
   👉 **`start_node_A_insurance_registration.bat`** (or `node_backend/start_node_A.bat`)

It will automatically:
- Create a Python virtual environment (`venv`)
- Install `fastapi`, `uvicorn`, and `requests`
- Find your local IP address
- Start the FastAPI server on port `8001`

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
$env:NODE_DATABASES="insurance,registration"
$env:NODE_PORT="8001"
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
   Look for `IPv4 Address`, e.g., `192.168.1.15`.
2. Send this URL to the Master:
   👉 `http://192.168.1.15:8001`
3. Verify it works in your browser: [http://localhost:8001/api/health](http://localhost:8001/api/health)

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
   ngrok http 8001
   ```
4. Copy the public forwarding URL (e.g. `https://a1b2-xxx.ngrok-free.app`) and send it to the Master!

---

## 🔍 Verification & Health Check
Open your browser to:
- Health check: [http://localhost:8001/api/health](http://localhost:8001/api/health)
- Databases exposed: [http://localhost:8001/api/sources](http://localhost:8001/api/sources)
- Interactive Swagger docs: [http://localhost:8001/docs](http://localhost:8001/docs)

You are all set! The Master will query your node to federate Insurance and Registration data in real time.
