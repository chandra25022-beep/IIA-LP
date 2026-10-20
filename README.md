# 🚗 IIA Project — Identification of Uninsured Vehicles
### Information Integration System | IIIT Delhi — M.Tech 3rd Semester
### Course: Information Integration and Applications (IIA)
### Project-Part B: Data Integration Under Uncertainty (15 Marks)

---

## 📋 Project Overview

A comprehensive **Information Integration** platform that detects uninsured and suspicious vehicles on roadways by federating **5 independently designed databases** across a distributed multi-node network using **Mediation / Global-As-View (GAV)** architecture and advanced **probabilistic entity resolution under uncertainty**.

### Key Architectural Highlights
- 🌐 **True Distributed Multi-Node Architecture:**
  - **Master Laptop (Port 8000):** Hosts `capture.db`, Mediator, ANPR Pipeline, Part B Indexing & Uncertainty Engines.
  - **Node B (Port 8001):** Hosts `insurance.db` and `registration.db`.
  - **Node C (Port 8002):** Hosts `theft.db` and `ministry.db`.
  - Nodes communicate over RESTful HTTP (LAN or ngrok tunnels).
- 🔍 **Robust Multi-Strategy ANPR Pipeline:**
  - Multi-stage detection: YOLOv8 vehicle detection + YOLOv8 plate detection + Quadrilateral aspect-ratio contour filter + Top-hat morphological gradient filter + Bumper region fallback + EasyOCR.
  - Handles real-world noisy images, different angles, and lighting conditions without throwing 500 errors.
  - Generates ranked candidate hypotheses for fuzzy match evaluation.
- ⚡ **Week 6–8 Indexing & Candidate Filtering:**
  - $Q$-gram tokenization ($q=3$) with positional boundary markers.
  - **Inverted Lists** (*Sarawagi et al., SIGMOD 2004*).
  - **Size Filtering** (*Arasu et al., VLDB 2006*) with bounds $\lceil \tau \cdot |x| \rceil \le |y| \le \lfloor |x| / \tau \rfloor$.
  - **Prefix-Inverted Index** (*Bayardo et al., WWW 2007*), ordering tokens by rarity and indexing only prefix tokens to reduce index size by over 70%.
- 🎯 **Part B: Data Integration Under Uncertainty (15 Marks):**
  - Live computation of **all 8 course similarity metrics**: Levenshtein, Normalized Edit, Jaro, Jaro-Winkler ($p=0.10$), $Q$-Gram Jaccard, Overlap Coefficient, TF-IDF Cosine, Ratcliff-Obershelp, Soundex.
  - **OCR Character Confusion Matrix** ($8 \leftrightarrow B$, $0 \leftrightarrow O$, $1 \leftrightarrow I$, $5 \leftrightarrow S$, $2 \leftrightarrow Z$).
  - **Calibrated Sigmoid Matching Probability** combining textual similarity, OCR confusion likelihood, attribute agreement, and sensor confidence.
  - **3-Tier STP Decision Routing (*Week 2 Slide 24*)**:
    - $\mathbf{P \ge 0.85}$: `AUTO_MERGE` (Automated Straight-Through Processing)
    - $\mathbf{0.50 \le P < 0.85}$: `UNCERTAIN_REVIEW` (Routed to audit queue)
    - $\mathbf{P < 0.50}$: `REJECT` (Distinct entity)
  - **Bayesian Truth Discovery:** Resolves multi-source conflicting attributes (e.g., conflicting vehicle colors) using source reliability priors.
- 💻 **Interactive SQL Console & Federated Writes:**
  - Run federated `SELECT` queries across all 5 databases.
  - Run `INSERT`/`UPDATE` writes with automated HTTP forwarding to the owning node.

---

## 🏗️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend & Node Servers** | Python 3.12 + FastAPI + Uvicorn |
| **Frontend** | React 18 + TypeScript + Vite + Recharts |
| **Databases** | SQLite (5 isolated, independently designed schemas) |
| **Distributed Protocol** | HTTP / REST + ngrok tunnels |
| **Vision & ANPR** | Ultralytics YOLOv8n + Custom `plate_model.pt` + OpenCV + EasyOCR |
| **Integration & Indexing** | Custom Q-Gram Index + Prefix Filtering + RapidFuzz |

---

## 🚀 Quick Start Guide

### Option 1: 1-Click Local Multi-Node Simulation (Recommended for Evaluation)
To run the full multi-node architecture on a single machine:
```cmd
start_all_local.bat
```
This automatically launches all 4 services on separate ports:
- **Frontend UI:** [http://localhost:5173](http://localhost:5173)
- **Master Backend:** [http://localhost:8000](http://localhost:8000) (Docs: [/docs](http://localhost:8000/docs))
- **Node B Server:** [http://localhost:8001](http://localhost:8001)
- **Node C Server:** [http://localhost:8002](http://localhost:8002)

### Option 2: Real 3-Laptop Distributed Setup
1. **Laptop B:** `cd node_backend && start_node_B.bat` (Port 8001)
2. **Laptop C:** `cd node_backend && start_node_C.bat` (Port 8002)
3. **Master Laptop:**
   ```cmd
   set NODE_B_URL=http://<Laptop-B-IP>:8001
   set NODE_C_URL=http://<Laptop-C-IP>:8002
   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. **Frontend:** `cd frontend && npm run dev -- --host 0.0.0.0 --port 5173`

*(Refer to [SHARING_GUIDE.md](file:///f:/M%20Tech%20IIITD/M%20Tech%203rd%20Sem/IIA/project/Car/SHARING_GUIDE.md) for detailed LAN/ngrok instructions).*

---

## 🗄️ Database Schemas & GAV Mappings

| Database | Host Node | Key Attribute | Organization | Mapped Global Attribute |
| :--- | :--- | :--- | :--- | :--- |
| `capture.db` | **Master** | `plate_number` | Traffic Surveillance Dept | `registration_number` |
| `insurance.db` | **Node B** | `registration_id` | National Insurance Registry | `registration_number` |
| `registration.db` | **Node B** | `vehicle_reg_no` | Regional Transport Office | `registration_number` |
| `theft.db` | **Node C** | `vehicle_identifier` | Police Crime Records Bureau | `registration_number` |
| `ministry.db` | **Node C** | `vehicle_ref` | Ministry of Transportation | `registration_number` |

---

## 🎯 Verification & Demonstration Highlights

1. **Scan Vehicle (`/scan`):** Drag-and-drop any test image from `test_assets/assets/`. Observe real-time pipeline stages, detected plate, OCR confidence, strategy badge, and the unified 5-source vehicle view.
2. **Week 6–8 Indexing (`/integration` $\rightarrow$ Indexing tab):** View live index statistics (postings, vocabulary) and run queries comparing Prefix-Inverted Indexing vs Standard Inverted Lists.
3. **Part B Uncertainty (`/integration` $\rightarrow$ Uncertainty tab):** Test live string similarity across all 8 metrics, inspect OCR character confusion penalties, and view the calibrated $P(\text{Match})$ with 3-tier routing.
4. **SQL Query Console (`/query`):** Execute federated cross-database SQL queries and verify remote write delegation.
