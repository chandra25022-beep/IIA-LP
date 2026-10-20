# 🚗 IIA Project — Distributed Multi-Node & Sharing Guide
### Identification of Uninsured Vehicles | IIIT Delhi — M.Tech 3rd Semester
### Course: Information Integration and Applications (IIA)
### Project-Part B: Data Integration Under Uncertainty (15 Marks)

---

## 📋 System Architecture Overview

This project implements a **real-world heterogeneous distributed information integration system** adhering to the course principles:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAPTOP A (MASTER NODE)                            │
│  - Hosts: capture.db (Traffic Surveillance camera records)                  │
│  - ANPR Engine: YOLOv8 + Aspect Ratio + Morphological + EasyOCR            │
│  - Mediator / GAV Schema Mapper (Global View)                               │
│  - Part B: Q-Gram Inverted Index + Prefix Filtering (Bayardo et al, WWW 07) │
│  - Part B: Probabilistic Uncertainty Engine & 3-Tier Decision Policy        │
│  - Web UI: React 18 + Vite (Port 5173)                                      │
│  - Master API: FastAPI (Port 8000)                                          │
└───────────────────────┬─────────────────────────────┬───────────────────────┘
                        │ HTTP / REST                 │ HTTP / REST
                        ▼                             ▼
┌───────────────────────────────────┐     ┌───────────────────────────────────┐
│       LAPTOP B (NODE B)           │     │       LAPTOP C (NODE C)           │
│  - Hosts: insurance.db (NIR)      │     │  - Hosts: theft.db (PCRB)         │
│  - Hosts: registration.db (RTO)   │     │  - Hosts: ministry.db (Transport) │
│  - Fast REST Server (Port 8001)   │     │  - Fast REST Server (Port 8002)   │
│  - Key: registration_id /         │     │  - Key: vehicle_identifier /      │
│         vehicle_reg_no            │     │         vehicle_ref               │
└───────────────────────────────────┘     └───────────────────────────────────┘
```

The system supports **two running modes**:
1. **Mode 1 (1-Click Local Simulation):** Runs all 3 independent nodes + frontend locally on your laptop (ideal for quick grading and verification).
2. **Mode 2 (Real 3-Laptop Distributed Setup):** Runs across 3 distinct student laptops over WiFi LAN or `ngrok` tunnels over the internet.

---

## ⚡ Mode 1: 1-Click Local Multi-Node Simulation (Fastest)

If you are demonstrating on your own laptop or recording a video:

1. Double-click **`start_all_local.bat`** in the project root folder.
2. This script automatically starts all 4 isolated services:
   - **Node B** (Port 8001) with `insurance.db` and `registration.db`
   - **Node C** (Port 8002) with `theft.db` and `ministry.db`
   - **Master Backend** (Port 8000) with `capture.db`, Mediator, and ANPR pipeline
   - **Frontend UI** (Port 5173) with React Vite dev server
3. Open your browser and navigate to:
   - **Web UI:** [http://localhost:5173](http://localhost:5173)
   - **Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 Mode 2: Real 3-Laptop Distributed Setup

If you and your 2 teammates are demonstrating on 3 separate physical laptops:

### Step 1: Teammate B (Laptop B — Insurance & Registration)
1. On Laptop B, navigate to the `node_backend` folder.
2. Double-click `start_node_B.bat` (or run in terminal):
   ```cmd
   set NODE_DATABASES=insurance,registration
   set NODE_PORT=8001
   python main.py
   ```
3. If using WiFi LAN: find Laptop B's WiFi IP (e.g. `http://192.168.1.15:8001`).
   If using ngrok over the internet: copy the ngrok URL (e.g. `https://node-b.ngrok-free.app`).

### Step 2: Teammate C (Laptop C — Theft & Ministry)
1. On Laptop C, navigate to the `node_backend` folder.
2. Double-click `start_node_C.bat` (or run in terminal):
   ```cmd
   set NODE_DATABASES=theft,ministry
   set NODE_PORT=8002
   python main.py
   ```
3. Copy Laptop C's URL (e.g. `http://192.168.1.22:8002` or `https://node-c.ngrok-free.app`).

### Step 3: Master Laptop (Your Laptop — Capture DB & Frontend)
1. In the project root, launch the master backend pointing to your teammates' URLs:
   ```cmd
   set NODE_B_URL=http://192.168.1.15:8001
   set NODE_C_URL=http://192.168.1.22:8002
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Start the frontend:
   ```cmd
   cd frontend
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
3. Now all queries executed on your laptop are dynamically federated over the network to Laptop B and Laptop C in real time!

---

## 🎯 Part B: 15 Marks Demonstration Guide (Course Week 6–8)

When presenting to the professor or TA, follow this structured demo script:

### Demo 1: Multi-Strategy License Plate Detection (Any Image)
- **Navigate to:** [Scan Vehicle (`/scan`)](http://localhost:5173/scan)
- **Upload test images** from `test_assets/assets/`:
  - `image1.jpg` $\rightarrow$ Detected plate `HR26BR9044` (98.6% OCR confidence)
  - `image2.jpg` $\rightarrow$ Detected plate `ECOVD19` (70.4% OCR confidence)
  - `image3.jpg` $\rightarrow$ Detected plate `EBJY982J` (63.9% OCR confidence)
  - `image4.jpg` $\rightarrow$ Detected plate `H982FKL` (99.6% OCR confidence)
  - `Screenshot 2024-06-26 074909.png` $\rightarrow$ Detected plate `H982FKL` (99.4% OCR confidence)
- **Explain to Evaluator:**
  - The pipeline does not crash on unseen images or noisy backgrounds.
  - It runs a multi-stage fallback: **YOLOv8 Full Plate Model** $\rightarrow$ **Aspect Ratio Filter** $\rightarrow$ **Morphological Gradient Top-Hat** $\rightarrow$ **Bumper Region Crop**.
  - Any alternative candidate hypotheses are displayed as clickable pills for user selection.

### Demo 2: Week 6–8 Q-Gram Inverted Index & Prefix Filtering
- **Navigate to:** [Integration View (`/integration`)](http://localhost:5173/integration) $\rightarrow$ Tab **⚡ Week 6-8 Indexing & Blocking**
- **Explain to Evaluator:**
  - Demonstrates how to avoid expensive $O(N \cdot M)$ pairwise string comparisons.
  - Generates $q$-gram tokens ($q=3$) with positional boundary markers (`##U`, `UP3`, `P32`, `2$$`).
  - Implements **Sarawagi et al. (SIGMOD 2004)** Inverted Lists.
  - Implements **Arasu et al. (VLDB 2006)** Size Filtering window: $\lceil \tau \cdot |x| \rceil \le |y| \le \lfloor |x| / \tau \rfloor$.
  - Implements **Bayardo et al. (WWW 2007)** Prefix-Inverted Index, indexing only prefix tokens ordered by rarity, reducing index size by over 70%.
- **Live Test:** Type any plate prefix into the interactive search box and compare candidate recall and filter efficiency.

### Demo 3: Data Integration Under Uncertainty & 3-Tier STP Policy
- **Navigate to:** [Integration View (`/integration`)](http://localhost:5173/integration) $\rightarrow$ Tab **🎯 Part B: Uncertainty & Decision Policy (15M)**
- **Explain to Evaluator:**
  - Evaluates all **8 course string similarity metrics** simultaneously:
    1. Levenshtein Distance
    2. Normalized Edit Similarity
    3. Jaro Similarity
    4. Jaro-Winkler Similarity (prefix bonus $p=0.10$)
    5. Q-Gram Jaccard ($q=3$)
    6. Overlap Coefficient (Szymkiewicz-Simpson)
    7. TF-IDF Cosine Similarity
    8. Ratcliff-Obershelp Gestalt Similarity
    9. Soundex Phonetic Encoding
  - Uses an **OCR Character Confusion Matrix** ($8 \leftrightarrow B$, $0 \leftrightarrow O$, $1 \leftrightarrow I$, $5 \leftrightarrow S$, $2 \leftrightarrow Z$).
  - Calibrates match probability via a multi-feature Sigmoid:
    $$P(\text{Match} \mid \phi) = \frac{1}{1 + e^{-(\beta_0 + \sum \beta_k \phi_k)}}$$
  - Enforces the **3-Tier STP (Straight-Through Processing) Policy (Week 2 Slide 24)**:
    - **$P \ge 0.85$**: `AUTO_MERGE` (Straight-through automated resolution)
    - **$0.50 \le P < 0.85$**: `UNCERTAIN_REVIEW` (Flagged for human operator review)
    - **$P < 0.50$**: `REJECT` (Distinct entity)

### Demo 4: Bayesian Truth Discovery for Attribute Conflicts
- In real-world data, independent sources report conflicting values (e.g. camera sensor claims color is `BLUE` while registration claims `WHITE`).
- The system computes Bayesian posterior truth discovery weighting source reliability and sensor confidence, synthesizing the single most probable truth.

---

## 🚗 Pre-Seeded Demo Vehicles

| Plate | Category | Overall Status | What It Demonstrates |
| :--- | :--- | :--- | :--- |
| **`UP32AB1234`** | Clean Car | `INSURED` | Active insurance (NIC-2024-001234), valid RTO registration. |
| **`UP32CD5678`** | Violation | `INSURANCE_EXPIRED` | Expired insurance policy (OIC-2021-115678 expired 2024-10-12). |
| **`MH02EF9012`** | Violation | `UNINSURED` | Vehicle exists in RTO registration but zero insurance records in NIR. |
| **`DL01GH3456`** | Security | `STOLEN` | Active police FIR (`FIR/2024/ROH/12345`) in Crime Records Bureau. |
| **`KA03IJ7890`** | Scrapped | `SCRAPPED` | End-of-life vehicle marked as scrapped in security registry. |
| **`TN05KL1122`** | Conflict | `DATA_CONFLICT` | Camera detects `BLUE` while RTO lists `RED` (Bayesian truth resolution). |
| **`HR26PQ7788`** | Suspicious | `SUSPICIOUS` | Open surveillance case flag in police database. |
| **`UP32AB123B`** | Uncertainty | `AUTO_MERGE (96.8%)` | Noisy OCR plate auto-merged with `UP32AB1234` via Part B engine. |

---

## 💻 SQL Console & Federated Writes

- Navigate to [SQL Query (`/query`)](http://localhost:5173/query)
- **SELECT (Federated Read):** Query "ALL" databases. The mediator queries all 5 databases across nodes and displays results with their respective local column names.
- **INSERT/UPDATE (Distributed Ownership):** Try inserting into `insurance` or `registration`. The UI recognizes that Laptop B owns these databases and forwards the write request over HTTP to Node B!
