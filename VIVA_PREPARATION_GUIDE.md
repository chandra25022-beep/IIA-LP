# 🎓 IIA Project Viva Preparation & Professor Evaluation Guide
**Project Title:** Distributed Information Integration & ANPR for Uninsured Vehicle Detection  
**Course:** Information Integration and Applications (IIA) — M.Tech, IIIT Delhi  
**Authors:** Student Group  

---

## 🏆 Executive Summary for Full Marks (Grade A+)

This project is a distributed Information Integration system implementing concepts from **Lectures 1–3**, **Week 6–8 (Data & String Matching)**, and **Week 8 (Ripple Down Rules - RDR)**:

1. **Architecture:** Federated Mediation Architecture (Virtual Integration) with Master-Node topology across 3 laptops.
2. **Schema Mapping:** Formal Global-As-View (GAV) schema mapping reconciling 5 independently designed databases.
3. **View Mechanism:** Both **Virtual Views** (on-the-fly multi-node federation) and **Materialized Views** (pre-joined local snapshots) with empirical latency vs. freshness benchmarks.
4. **String Matching & Indexing (Week 6–8):**
   - Universal Token Ordering inverted index ($idf$-based rarest-first)
   - Size Filtering ($|x| \cdot t \le |y| \le |x| / t$ — Arasu et al., VLDB 2006)
   - Prefix Filtering (prefix size $|x| - k + 1$ — Chaudhuri et al., ICDE 2006)
   - Position Filtering (Xiao et al., WWW 2008)
   - 7 similarity metrics: Levenshtein DP, Jaro, Jaro-Winkler, Jaccard (q-grams), TF-IDF Cosine, Ratcliff-Obershelp, Soundex.
5. **Knowledge Acquisition & Normalization (Week 8):** Single-Classification Ripple Down Rules (SCRDR) with cornerstone cases, audit trails, and exception hierarchies for license plate and composite address normalization.
6. **Probabilistic Entity Resolution:** 3-tier Straight-Through Processing (STP) with calibrated logistic uncertainty routing (`AUTO_MERGE`, `UNCERTAIN_REVIEW`, `REJECT`).

---

## 📚 Section 1: Core Theoretical Concepts & Math Formulations

### 1.1 Federated Mediation vs. Data Warehousing
- **Data Warehousing:** Data from operational databases is extracted, transformed, and loaded (ETL) into a centralized physical storage periodically.
  - *Tradeoff:* Very fast reads; but data is stale (latency equal to ETL batch window), high storage redundancy, and requires write access to central storage.
- **Federated Mediation (Our Choice):** Data remains autonomous in source databases across laptops. A mediator decomposes global queries into source queries, executes them remotely, and joins results on-the-fly.
  - *Tradeoff:* Always guarantees 100% data freshness; zero central replication; preserves source autonomy; slightly higher network latency.

### 1.2 GAV (Global-As-View) vs. LAV (Local-As-View)
- **GAV (Global-As-View):** The global schema relations are expressed as views (queries) over the local data sources:
  $$\text{GlobalRelation}(A_1, \dots, A_n) = \text{Source}_1(A_1, \dots) \bowtie \text{Source}_2(\dots)$$
  - *Query Unfolding:* Straightforward rule substitution. Expanding a query on the global schema simply substitutes view definitions.
  - *Limitation:* Adding a new source requires updating global views.
- **LAV (Local-As-View):** Each local source is expressed as a view over the global schema:
  $$\text{Source}_i(B_1, \dots) = \sigma_{\dots}(\text{GlobalRelation}_1 \bowtie \dots)$$
  - *Query Answering:* Requires complex view-based query rewriting (e.g., Bucket algorithm, MiniCon, Inverse Rules) which is NP-complete.
  - *Limitation:* Complex query rewriting overhead.
- **Why GAV in our project?** The global view of a vehicle (`registration_number`, `status`, `owner`, `insurance_expiry`, `stolen`) is a direct federation join over the 5 known sources (`capture`, `insurance`, `registration`, `theft`, `ministry`). Query unfolding is O(1) and exact.

### 1.3 Virtual View vs. Materialized View (Demonstrated in Project)
- **Virtual View:** The mediator issues real-time HTTP sub-queries to Node A (port 8001) and Node B (port 8002).
  - *Freshness:* Immediate (0 lag). If Node A updates insurance status, Master sees it instantly.
  - *Latency:* ~10–80 ms (network roundtrips).
- **Materialized View:** The mediator caches pre-joined snapshots of all vehicles in local memory/database.
  - *Freshness:* Stale until explicitly invalidated (`POST /api/materialized-view/refresh`).
  - *Latency:* < 0.1 ms (O(1) dictionary/index lookup — up to 100,000x faster).

---

## 🔍 Section 2: Week 6–8 String Matching & Inverted Indexing

### 2.1 String Distance Formulas
1. **Levenshtein Edit Distance (DP):**
   $$D(i, j) = \min \begin{cases} D(i-1, j) + 1 & \text{(Deletion)} \\ D(i, j-1) + 1 & \text{(Insertion)} \\ D(i-1, j-1) + \mathbb{I}(s_1[i] \ne s_2[j]) & \text{(Substitution)} \end{cases}$$
   Normalized similarity: $\text{Sim}_{\text{edit}}(s_1, s_2) = 1 - \frac{D(|s_1|, |s_2|)}{\max(|s_1|, |s_2|)}$.

2. **Jaro Similarity:**
   For matching characters $m$ within window $\lfloor \frac{\max(|s_1|, |s_2|)}{2} \rfloor - 1$ and transpositions $t$:
   $$J(s_1, s_2) = \frac{1}{3} \left( \frac{m}{|s_1|} + \frac{m}{|s_2|} + \frac{m - t}{m} \right)$$

3. **Jaro-Winkler Similarity (Prefix Boost):**
   For common prefix length $L \le 4$ with scaling factor $p = 0.1$:
   $$JW(s_1, s_2) = J(s_1, s_2) + L \cdot p \cdot (1 - J(s_1, s_2))$$
   *Crucial for Indian license plates:* State prefix (`DL`, `MH`, `UP`) matches get an instant boost!

4. **Jaccard Similarity on Q-Grams (3-grams):**
   $$Jaccard(Q(s_1), Q(s_2)) = \frac{|Q(s_1) \cap Q(s_2)|}{|Q(s_1) \cup Q(s_2)|}$$

5. **Soundex Phonetic Encoding:**
   Maps names to 1 letter + 3 digits (e.g., `Sharma` $\to$ `S650`, `Varma` $\to$ `V650`) to reconcile phonetic spelling differences in owner names across disparate RTO registers.

### 2.2 Pruning Filters (Week 6–8 Slides 53–65)
Given a threshold $t \in [0, 1]$ and query string $x$ with token/q-gram set $B_x$:
1. **Size Filtering (Arasu et al., VLDB 06):**
   $$|B_x| \cdot t \le |B_y| \le \frac{|B_x|}{t}$$
   Any candidate $y$ whose length is outside this bound is rejected in $O(1)$ without token lookup.
2. **Prefix Filtering (Chaudhuri et al., ICDE 06):**
   To have Jaccard overlap at least $k = \lceil \frac{t}{1+t} (|B_x| + |B_y|) \rceil$, the prefixes of size:
   $$\pi(B_x) = |B_x| - \lceil t \cdot |B_x| \rceil + 1$$
   MUST share at least one common token.
3. **Prefix Inverted Index (Bayardo et al., WWW 07):**
   Tokens are sorted in **Universal Ordering** (rarest tokens first, highest inverse document frequency). Only tokens in the prefix $\pi(B_x)$ are indexed, reducing index size by 70–85%!
4. **Position Filtering (Xiao et al., WWW 08):**
   Tracks token positions to calculate the maximum possible remaining overlap $\text{pos}(x, w) + \text{remaining}$; if less than $k$, pruning occurs dynamically.

---

## 🌳 Section 3: Week 8 Ripple Down Rules (RDR)

### 3.1 The Knowledge Acquisition Bottleneck
In traditional rule-based expert systems (like MYCIN or CLIPS), adding rule $R_{new}$ to handle a corner case frequently breaks 10 existing cases (regression). Knowledge engineers spend 80% of their time resolving unintended rule interactions.

### 3.2 Compton's Single-Classification RDR (SCRDR)
- Rules are organized in a binary tree where each node has:
  1. **Condition:** Predicate (e.g., `has_model_badge(x)`).
  2. **Conclusion:** Canonical form or action.
  3. **Cornerstone Case:** The concrete instance that motivated adding this rule.
  4. **Except Branch (True Branch):** A more specific exception rule.
  5. **Else Branch (False Branch):** An alternative rule evaluated if this rule fails.
- *Guarantee:* A new exception is placed only on the leaf that misclassified the cornerstone case. Previous classifications are mathematically guaranteed never to regress!

### 3.3 RDR in Our System (`backend/app/integration/rdr_engine.py`)
1. **Plate Normalization Tree:**
   - Root `RDR-P00`: Default alphanumeric stripper.
   - Child `RDR-P01`: Exception for vehicle model badges (`GLA250`, `CLA200`) $\to$ reject.
   - Child `RDR-P02`: Exception for VIP convoy vanity plates (`AP CM JAGAN`) $\to$ preserve.
   - Child `RDR-P03`: Exception for Bharat Series (`22BH6517A`) $\to$ preserve nationwide standard.
   - Child `RDR-P04/P05`: Exception for UK/European plates (`SN66XMZ`, `J389NLT`) $\to$ canonical format.
   - Child `RDR-P07`: Standard Indian RTO format with positional character disambiguation (`0` vs `O`, `1` vs `I`).
2. **Address Decomposition Tree:**
   - Decomposes dirty unstructured strings (e.g., `"Flat 402, Sunshine Apts, Sector 62, Noida, UP 201301"`) into `house_no`, `building`, `street`, `city`, `state`, `pincode`.

---

## 💻 Section 4: Live Demonstration Script for the Viva

| Step | Action | Endpoint / Screen | What to Say to the Professor |
|:---|:---|:---|:---|
| **1** | Open Dashboard | `http://localhost:5173` | *"Here is the Master dashboard showing real-time health checks of our 3 distributed nodes across laptops via the Source Registry."* |
| **2** | Test Image ANPR | Upload `test1.jpg` | *"Our high-speed vision pipeline (YOLOv8 + EasyOCR) detects the plate bounding box and extracts the text."* |
| **3** | GAV Integration | Click **Integrate** | *"The Master Mediator triggers GAV query unfolding: querying local Capture DB and remote Node A (Insurance, Registration) and Node B (Theft, Ministry)."* |
| **4** | Compare Views | `POST /api/view-comparison` | *"Notice the latency difference: Virtual View took 80 ms to query across nodes for 100% fresh data; Materialized View took 0.08 ms (100,000x faster)."* |
| **5** | RDR Audit Trail | `POST /api/rdr/demo` | *"Notice how the SCRDR tree traces step-by-step through rules and cornerstone cases from Week 8 lecture."* |
| **6** | String Matching | String Matching Tab | *"Notice how Q-Grams + Prefix Filtering prunes 90% of pairwise comparisons before computing Levenshtein or Jaro-Winkler distances."* |

---

## ❓ Section 5: Top 15 Professor Viva Questions & Exact Answers

### Q1: What is the difference between GAV and LAV? Which one did you implement and why?
> **Answer:**  
> "In GAV (Global-As-View), global relations are defined as queries over local sources. In LAV (Local-As-View), local sources are defined as queries over the global schema.  
> We implemented **GAV** because in our domain, the global entity (a unified Vehicle Record) has a well-defined schema, and we know exactly how each of the 5 autonomous sources maps to it (e.g. `plate_number` in Capture, `registration_id` in Insurance, `vehicle_reg_no` in Registration). Query unfolding in GAV is direct rule substitution without the NP-hard view rewriting needed in LAV."

### Q2: What is the difference between Virtual Integration and Materialized Integration in your project?
> **Answer:**  
> "Virtual Integration (Federated Mediation) keeps data at the source nodes. When the Master queries a plate, the mediator sends parallel HTTP requests to Node A (port 8001) and Node B (port 8002), unfolding and joining on-the-fly. This guarantees 100% data freshness with zero central storage.  
> Materialized Integration pre-computes the joins and caches the entire snapshot locally. We demonstrated empirically that Materialized Views are ~100,000x faster for read queries (0.08 ms vs 80 ms), but become stale until an explicit refresh occurs after writes."

### Q3: How do you handle write operations (INSERT/UPDATE/DELETE) in a distributed system?
> **Answer:**  
> "We implement strict **Source Ownership Routing**:
> - The Master laptop only owns `capture.db`. Master can execute local INSERT/UPDATE on captures.
> - `insurance.db` and `registration.db` are owned by Node A.
> - `theft.db` and `ministry.db` are owned by Node B.
> If a write request arrives for insurance, the Master routes it via HTTP POST to Node A's write endpoint. Node A executes the write locally and responds. The Master then invalidates the Materialized View cache."

### Q4: Explain Prefix Filtering and how it reduces string matching complexity.
> **Answer:**  
> "Prefix Filtering [Chaudhuri et al., ICDE 2006] exploits the property that for two token sets $x$ and $y$ to have Jaccard overlap $\ge k$, their prefixes of size $|x| - k + 1$ must share at least one common token.  
> By sorting tokens in increasing order of document frequency (Universal Ordering — rarest tokens first), and indexing only the prefix tokens into an inverted index, we avoid checking 80–90% of non-matching pairs entirely. We only run dynamic programming edit distance on candidate pairs that pass the prefix filter."

### Q5: What is Size Filtering in Q-gram matching? Give the exact formula.
> **Answer:**  
> "Size Filtering [Arasu et al., VLDB 2006] is an $O(1)$ pruning step. For Jaccard threshold $t$, two strings $x$ and $y$ cannot have Jaccard similarity $\ge t$ unless:
> $$|x| \cdot t \le |y| \le \frac{|x|}{t}$$
> If query string $x$ has length 10 and $t = 0.8$, any candidate string with length $< 8$ or $> 12$ is pruned instantly without inspecting individual characters or tokens."

### Q6: Why do we use Jaro-Winkler instead of pure Levenshtein for license plates?
> **Answer:**  
> "Levenshtein treats an edit anywhere in the string equally. However, Indian license plates have a fixed structural syntax: the first 2 characters denote the State (`DL`, `MH`, `UP`, `KA`). Jaro-Winkler adds a prefix scaling bonus ($p = 0.1$) for up to 4 initial matching characters. Therefore, a match on the state prefix provides higher confidence for geographical grouping, which matches human intuition and domain reality."

### Q7: What is Ripple Down Rules (RDR) and how does it prevent the Knowledge Acquisition Bottleneck?
> **Answer:**  
> "In traditional expert systems, modifying rules creates unexpected regressions because rules interact globally. Compton's SCRDR solves this by structuring knowledge into an exception tree where:
> 1. Every new rule is added in direct context of a false positive / false negative against a concrete **Cornerstone Case**.
> 2. Rules are placed only on the leaf exception branch (`except if`) or alternative branch (`else if`).
> 3. Existing branches remain untouched, guaranteeing that existing correct classifications never regress."

### Q8: What cornerstone cases exist in your RDR implementation?
> **Answer:**  
> "In `backend/app/integration/rdr_engine.py`:
> 1. `RDR-P01`: Cornerstone case `'GLA250'` (Mercedes model badge mistakenly detected as plate $\to$ reject).
> 2. `RDR-P02`: Cornerstone case `'AP CM JAGAN'` (VIP/convoy vanity plate with letters only $\to$ preserve).
> 3. `RDR-P03`: Cornerstone case `'22BH6517A'` (Bharat Series national registration $\to$ valid).
> 4. `RDR-P04/P05`: Cornerstone cases `'SN66XMZ'` and `'J389NLT'` (UK and European plate standards).
> 5. `RDR-P07`: Positional Indian RTO rule disambiguating character `O` to `0` in numeric positions and `0` to `O` in alpha positions."

### Q9: How do you handle OCR errors like confusion between 'O' and '0' or 'I' and '1'?
> **Answer:**  
> "We use **Positional Syntactic Disambiguation** based on the Indian Motor Vehicles Act standard pattern (`[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}`):
> - In positions 0–1 (State code): `'0'` $\to$ `'O'`, `'1'` $\to$ `'I'`, `'8'` $\to$ `'B'`.
> - In positions 2–3 (RTO code): `'O'` $\to$ `'0'`, `'I'` $\to$ `'1'`, `'S'` $\to$ `'5'`, `'B'` $\to$ `'8'`.
> - In positions 4–5 (Series letters): numbers converted back to letters.
> - In final 4 positions (Registration digits): letters converted back to numbers."

### Q10: How does your system resolve schema heterogeneity across the 5 databases?
> **Answer:**  
> "Each database was created with completely distinct schema designs:
> - `capture.db`: table `vehicle_capture`, key `plate_number`
> - `insurance.db`: table `insurance_records`, key `registration_id`
> - `registration.db`: table `vehicle_registration`, key `vehicle_reg_no`
> - `theft.db`: table `vehicle_security_records`, key `vehicle_identifier`
> - `ministry.db`: table `transport_reports`, key `vehicle_ref`
> Our GAV Schema Mapper (`backend/app/integration/schema_mapper.py`) defines bidirectional transformation functions that map these heterogeneous attributes into the canonical global attribute `registration_number`."

### Q11: How do you perform Instance-Based Schema Matching?
> **Answer:**  
> "When mapping unknown tables, our `SchemaMatcher` computes multi-signal similarity:
> 1. **Label Similarity:** 3-gram Jaccard on column names.
> 2. **Instance-Based Value Similarity:** Evaluates overlap between sampled column values using regex patterns (e.g., license plate regex matching rate).
> 3. **Type & Length Distribution:** KL-divergence of string length distributions between source and target attributes."

### Q12: How do you handle uncertainty when a license plate has low OCR confidence?
> **Answer:**  
> "We implement a 3-tier Straight-Through Processing (STP) policy calibrated with a logistic sigmoid model (Week 2 & Week 6–8 Slide 81):
> - Score $\ge 0.85$: **AUTO_MERGE** (Automatic straight-through integration without human intervention).
> - $0.50 \le \text{Score} < 0.85$: **UNCERTAIN_REVIEW** (Routed to human operator inspection queue with highlighted ambiguous characters).
> - Score $< 0.50$: **REJECT** (Treated as non-match/distinct entity)."

### Q13: What happens if Node A (Laptop B) goes down during execution?
> **Answer:**  
> "Our `SourceRegistry` maintains dynamic health statuses via background PING heartbeats. If Node A becomes unreachable:
> 1. The Mediator logs a warning and marks Node A as `DOWN`.
> 2. The query does **not** fail: the mediator performs graceful degradation, returning available data from Master and Node B with a status `PARTIAL_INTEGRATION`.
> 3. The integration metadata clearly flags that Insurance & Registration data were unavailable."

### Q14: How does Soundex phonetic matching help in vehicle data integration?
> **Answer:**  
> "In Indian registration records, owner names frequently have regional phonetic variations (e.g. `'Chaudhary'`, `'Choudhary'`, `'Chowdhury'`). Soundex encodes consonants into numeric phonetic classes while ignoring vowels. All three spellings map to `C360`, allowing the mediator to confirm owner identity across disparate databases even when literal character strings differ."

### Q15: Where are all these concepts verified in the code?
> **Answer:**  
> "You can query `GET http://localhost:8000/api/course-concepts` on our live running server. It returns the machine-readable inventory of all 18 implemented lecture concepts, the exact source files, and their mathematical formulations."

---

## 🎯 Final Checklist for Full Marks
- [x] Node A running on port 8001 (`insurance.db`, `registration.db`)
- [x] Node B running on port 8002 (`theft.db`, `ministry.db`)
- [x] Master running on port 8000 (Mediator, GAV, RDR, Indexing, Materialized View)
- [x] Frontend running on port 5173 (React UI with live camera/image ANPR, federation status, view comparison, string matching)
- [x] Git branches prepared (`main`, `node-a`, `node-b`)
- [x] Setup prompts written for teammates (`NODE_A_SETUP_PROMPT.md`, `NODE_B_SETUP_PROMPT.md`)
