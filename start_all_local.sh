#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# IIA Vehicle Integration System — Start All Local (macOS)
# Launches: Master (8000) + Node B (8001) + Node C (8002) + Frontend (5173)
# ─────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  IIA Vehicle Integration System — Starting All Services"
echo "============================================================"

# 1. Check if data directory exists and databases are seeded
if [ ! -f "data/capture.db" ]; then
    echo ""
    echo ">>> Databases not found. Running seed script..."
    cd "$SCRIPT_DIR"
    python3 scripts/seed_databases.py
    echo ""
fi

# 2. Start Node B (insurance.db + registration.db) on port 8001
echo ">>> Starting Node B (Port 8001)..."
cd "$SCRIPT_DIR/node_backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 &
NODE_B_PID=$!
echo "    Node B PID: $NODE_B_PID"

# 3. Start Node C (theft.db + ministry.db) on port 8002
echo ">>> Starting Node C (Port 8002)..."
cd "$SCRIPT_DIR/node_backend"
NODE_ROLE=C python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 &
NODE_C_PID=$!
echo "    Node C PID: $NODE_C_PID"

sleep 2

# 4. Start Master Backend on port 8000
echo ">>> Starting Master Backend (Port 8000)..."
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
MASTER_PID=$!
echo "    Master PID: $MASTER_PID"

# 5. Start Frontend on port 5173
echo ">>> Starting Frontend (Port 5173)..."
cd "$SCRIPT_DIR/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
echo "    Frontend PID: $FRONTEND_PID"

echo ""
echo "============================================================"
echo "  All services started!"
echo "  Frontend:       http://localhost:5173"
echo "  Master API:     http://localhost:8000/docs"
echo "  Node B:         http://localhost:8001"
echo "  Node C:         http://localhost:8002"
echo "============================================================"
echo ""
echo "Press Ctrl+C to stop all services..."

# Trap Ctrl+C to kill all processes
trap "kill $NODE_B_PID $NODE_C_PID $MASTER_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
