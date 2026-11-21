"""
Phase 3 Database Migration Script
==================================
Expands each of the 5 databases from 1 table to 4-5 tables with FK-PK relationships.
Migrates existing data and seeds related records.

Run: python scripts/migrate_phase3.py
"""
import sys, os, random, sqlite3
from pathlib import Path
from datetime import datetime, timedelta, date

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DB_CAPTURE = str(DATA_DIR / "capture.db")
DB_INSURANCE = str(DATA_DIR / "insurance.db")
DB_REGISTRATION = str(DATA_DIR / "registration.db")
DB_THEFT = str(DATA_DIR / "theft.db")
DB_MINISTRY = str(DATA_DIR / "ministry.db")

random.seed(42)
today = date(2026, 11, 21)

# ─────────────────────────────────────────────────────────────────────
# 1. CAPTURE.DB — Traffic Surveillance Company (4 tables)
# ─────────────────────────────────────────────────────────────────────
def migrate_capture():
    print("\n📸 Migrating capture.db → 4 tables with FK-PK...")
    conn = sqlite3.connect(DB_CAPTURE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Table 1: cameras
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cameras (
            camera_id TEXT PRIMARY KEY,
            location TEXT NOT NULL,
            city TEXT,
            state TEXT,
            camera_type TEXT DEFAULT 'ANPR',
            installation_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            resolution TEXT DEFAULT '4K',
            coverage_range_m REAL DEFAULT 50.0
        );
    """)

    # Extract unique camera_ids from existing captures
    existing = conn.execute("SELECT DISTINCT camera_id, capture_location FROM vehicle_capture WHERE camera_id IS NOT NULL").fetchall()
    camera_data = {
        "CAM-DEL-01": ("Sarita Vihar Checkpost, Delhi", "Delhi", "DL", "ANPR Fixed", "2024-01-15"),
        "CAM-DEL-02": ("DND Flyway Toll Plaza, Delhi-Noida", "Delhi", "DL", "ANPR Speed", "2023-06-20"),
        "CAM-DEL-03": ("Connaught Place Outer Circle, Delhi", "Delhi", "DL", "ANPR PTZ", "2024-03-10"),
        "CAM-DEL-04": ("Dwarka Expressway Km 12, Delhi", "Delhi", "DL", "ANPR Speed", "2024-07-01"),
        "CAM-MUM-01": ("Bandra-Worli Sea Link Toll, Mumbai", "Mumbai", "MH", "ANPR Toll", "2023-11-05"),
        "CAM-MUM-02": ("Western Express Highway, Andheri", "Mumbai", "MH", "ANPR Fixed", "2024-02-28"),
        "CAM-BLR-01": ("Electronic City Elevated Tollway, Bengaluru", "Bengaluru", "KA", "ANPR Toll", "2024-05-15"),
        "CAM-BLR-02": ("Outer Ring Road (Marathahalli), Bengaluru", "Bengaluru", "KA", "ANPR Fixed", "2023-09-20"),
        "CAM-HYD-01": ("Gachibowli Junction Toll Plaza, Hyderabad", "Hyderabad", "TS", "ANPR Toll", "2024-04-01"),
        "CAM-CHN-01": ("OMR IT Corridor Checkpoint, Chennai", "Chennai", "TN", "ANPR Fixed", "2023-12-10"),
        "CAM-PUN-01": ("Mumbai-Pune Expressway Toll Gate 3", "Pune", "MH", "ANPR Speed", "2024-01-25"),
        "CAM-AHM-01": ("SG Highway Flyover, Ahmedabad", "Ahmedabad", "GJ", "ANPR Fixed", "2024-06-15"),
    }
    for cam_id, (loc, city, state, ctype, inst) in camera_data.items():
        conn.execute(
            "INSERT OR IGNORE INTO cameras (camera_id, location, city, state, camera_type, installation_date) VALUES (?,?,?,?,?,?)",
            (cam_id, loc, city, state, ctype, inst)
        )

    # Ensure vehicle_capture has speed_kmph column
    cols = [r[1] for r in conn.execute("PRAGMA table_info(vehicle_capture)").fetchall()]
    if "speed_kmph" not in cols:
        conn.execute("ALTER TABLE vehicle_capture ADD COLUMN speed_kmph REAL")
        # Populate with random speeds
        captures = conn.execute("SELECT capture_id FROM vehicle_capture").fetchall()
        for cap in captures:
            speed = round(random.uniform(30, 120), 1)
            conn.execute("UPDATE vehicle_capture SET speed_kmph = ? WHERE capture_id = ?", (speed, cap[0]))

    # Table 3: capture_alerts (FK → vehicle_capture)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS capture_alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            alert_severity TEXT NOT NULL DEFAULT 'MEDIUM',
            alert_timestamp TEXT NOT NULL,
            alert_message TEXT,
            acknowledged INTEGER DEFAULT 0,
            acknowledged_by TEXT,
            FOREIGN KEY (capture_id) REFERENCES vehicle_capture(capture_id)
        );
        CREATE INDEX IF NOT EXISTS idx_alert_capture ON capture_alerts(capture_id);
    """)

    # Table 4: operator_logs (FK → vehicle_capture)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS operator_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_id INTEGER NOT NULL,
            operator_name TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            notes TEXT,
            log_timestamp TEXT NOT NULL,
            FOREIGN KEY (capture_id) REFERENCES vehicle_capture(capture_id)
        );
        CREATE INDEX IF NOT EXISTS idx_oplog_capture ON operator_logs(capture_id);
    """)

    # Seed alerts for captures with high speed or specific plates
    captures = conn.execute("SELECT capture_id, plate_number, speed_kmph, capture_timestamp FROM vehicle_capture").fetchall()
    alert_types = ["OVERSPEED", "STOLEN_MATCH", "UNINSURED_ALERT", "REPEAT_OFFENDER", "BLACKLISTED"]
    operators = ["Insp. Rajesh Kumar", "ASI Priya Singh", "Const. Arun Verma", "SI Meena Sharma", "HC Deepak Yadav"]

    for cap in captures:
        cap_id, plate, speed, ts = cap[0], cap[1], cap[2] or 60, cap[3]
        # Generate alerts for overspeed
        if speed and speed > 80:
            conn.execute(
                "INSERT OR IGNORE INTO capture_alerts (capture_id, alert_type, alert_severity, alert_timestamp, alert_message) VALUES (?,?,?,?,?)",
                (cap_id, "OVERSPEED", "HIGH" if speed > 100 else "MEDIUM",
                 ts, f"Vehicle {plate} detected at {speed} km/h in speed-limited zone")
            )
        # Random other alerts
        if random.random() < 0.08:
            atype = random.choice(alert_types[1:])
            conn.execute(
                "INSERT OR IGNORE INTO capture_alerts (capture_id, alert_type, alert_severity, alert_timestamp, alert_message, acknowledged) VALUES (?,?,?,?,?,?)",
                (cap_id, atype, random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                 ts, f"Alert for {plate}: {atype}", random.choice([0, 1]))
            )

    # Seed operator logs
    for cap in random.sample(list(captures), min(len(captures), 100)):
        cap_id, plate, _, ts = cap[0], cap[1], cap[2], cap[3]
        conn.execute(
            "INSERT INTO operator_logs (capture_id, operator_name, action_taken, notes, log_timestamp) VALUES (?,?,?,?,?)",
            (cap_id, random.choice(operators),
             random.choice(["VERIFIED", "FLAGGED_FOR_REVIEW", "DISMISSED", "ESCALATED", "FORWARDED_TO_PATROL"]),
             f"Reviewed capture of {plate}", ts)
        )

    conn.commit()
    # Print stats
    for tbl in ["cameras", "vehicle_capture", "capture_alerts", "operator_logs"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ {tbl}: {cnt} rows")
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# 2. REGISTRATION.DB — RTO Authority (5 tables)
# ─────────────────────────────────────────────────────────────────────
def migrate_registration():
    print("\n🏛️ Migrating registration.db → 5 tables with FK-PK...")
    conn = sqlite3.connect(DB_REGISTRATION)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Table 1: vehicle_owners
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicle_owners (
            owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            owner_contact TEXT,
            owner_address TEXT,
            aadhar_hash TEXT,
            pan_number TEXT,
            date_of_birth TEXT,
            gender TEXT,
            email TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_owner_name ON vehicle_owners(owner_name);
    """)

    # Migrate owner data from vehicle_registration
    existing_owners = conn.execute("SELECT COUNT(*) FROM vehicle_owners").fetchone()[0]
    if existing_owners == 0:
        rows = conn.execute("SELECT DISTINCT owner_name, owner_contact, owner_address FROM vehicle_registration").fetchall()
        for r in rows:
            name, contact, addr = r[0], r[1], r[2]
            aadhar = f"XXXX-XXXX-{random.randint(1000, 9999)}"
            pan = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}{random.randint(1000, 9999)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}"
            dob = (today - timedelta(days=random.randint(8000, 22000))).isoformat()
            gender = random.choice(["M", "F"])
            email_name = name.lower().replace(" ", ".").replace("'", "")
            email = f"{email_name}@{'gmail.com' if random.random() < 0.6 else 'yahoo.in'}"
            conn.execute(
                "INSERT INTO vehicle_owners (owner_name, owner_contact, owner_address, aadhar_hash, pan_number, date_of_birth, gender, email) VALUES (?,?,?,?,?,?,?,?)",
                (name, contact, addr, aadhar, pan, dob, gender, email)
            )
        conn.commit()

    # Add owner_id FK column to vehicle_registration if not exists
    cols = [r[1] for r in conn.execute("PRAGMA table_info(vehicle_registration)").fetchall()]
    if "owner_id" not in cols:
        conn.execute("ALTER TABLE vehicle_registration ADD COLUMN owner_id INTEGER REFERENCES vehicle_owners(owner_id)")
        # Link registrations to owners by name
        regs = conn.execute("SELECT reg_serial, owner_name FROM vehicle_registration").fetchall()
        for reg in regs:
            owner = conn.execute("SELECT owner_id FROM vehicle_owners WHERE owner_name = ? LIMIT 1", (reg[1],)).fetchone()
            if owner:
                conn.execute("UPDATE vehicle_registration SET owner_id = ? WHERE reg_serial = ?", (owner[0], reg[0]))
        conn.commit()

    # Table 3: vehicle_specs (FK → vehicle_registration)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicle_specs (
            spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_serial INTEGER NOT NULL,
            manufacturer TEXT NOT NULL,
            model_name TEXT NOT NULL,
            vehicle_class TEXT NOT NULL,
            registered_color TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            engine_number TEXT,
            chassis_number TEXT,
            seating_capacity INTEGER,
            engine_cc INTEGER,
            manufacture_year INTEGER,
            gross_weight_kg REAL,
            wheelbase_mm REAL,
            emission_norm TEXT DEFAULT 'BS6',
            FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
        );
        CREATE INDEX IF NOT EXISTS idx_specs_reg ON vehicle_specs(reg_serial);
    """)

    # Migrate specs data from vehicle_registration
    existing_specs = conn.execute("SELECT COUNT(*) FROM vehicle_specs").fetchone()[0]
    if existing_specs == 0:
        regs = conn.execute("""
            SELECT reg_serial, manufacturer, model_name, vehicle_class, registered_color,
                   fuel_type, engine_number, chassis_number, seating_capacity
            FROM vehicle_registration
        """).fetchall()
        for r in regs:
            engine_cc = random.choice([998, 1197, 1248, 1497, 1582, 1998, 2179, 2993])
            mfg_year = random.randint(2018, 2026)
            weight = round(random.uniform(900, 2500), 1)
            wheelbase = random.choice([2430, 2500, 2600, 2700, 2750, 2810])
            emission = random.choice(["BS4", "BS6", "BS6 Stage II"])
            conn.execute(
                """INSERT INTO vehicle_specs (reg_serial, manufacturer, model_name, vehicle_class,
                   registered_color, fuel_type, engine_number, chassis_number, seating_capacity,
                   engine_cc, manufacture_year, gross_weight_kg, wheelbase_mm, emission_norm)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                 engine_cc, mfg_year, weight, wheelbase, emission)
            )
        conn.commit()

    # Table 4: rto_transactions (FK → vehicle_registration)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rto_transactions (
            txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_serial INTEGER NOT NULL,
            txn_type TEXT NOT NULL,
            txn_date TEXT NOT NULL,
            fee_amount REAL,
            processed_by TEXT,
            remarks TEXT,
            FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
        );
        CREATE INDEX IF NOT EXISTS idx_txn_reg ON rto_transactions(reg_serial);
    """)

    # Table 5: fitness_certificates (FK → vehicle_registration)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fitness_certificates (
            cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_serial INTEGER NOT NULL,
            cert_number TEXT UNIQUE,
            issue_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            inspector_name TEXT,
            inspection_center TEXT,
            result TEXT NOT NULL DEFAULT 'PASS',
            remarks TEXT,
            FOREIGN KEY (reg_serial) REFERENCES vehicle_registration(reg_serial)
        );
        CREATE INDEX IF NOT EXISTS idx_fitness_reg ON fitness_certificates(reg_serial);
    """)

    # Seed transactions and fitness certs
    existing_txn = conn.execute("SELECT COUNT(*) FROM rto_transactions").fetchone()[0]
    if existing_txn == 0:
        regs = conn.execute("SELECT reg_serial, vehicle_reg_no, registration_date FROM vehicle_registration").fetchall()
        txn_types = ["NEW_REGISTRATION", "TAX_RENEWAL", "FITNESS_RENEWAL", "ADDRESS_CHANGE", "OWNERSHIP_TRANSFER", "HYPOTHECATION_ADD", "HYPOTHECATION_REMOVE", "NOC_ISSUED"]
        inspectors = ["R.K. Mehra (AEI)", "S. Patel (MEI)", "V. Krishnan (AEI)", "M. Das (SEI)", "K. Reddy (MEI)"]
        centers = ["RTO Inspection Bay - Main", "Authorised Testing Station - Sector 15", "Vehicle Fitness Center - Highway"]

        for r in regs:
            # Initial registration transaction
            conn.execute(
                "INSERT INTO rto_transactions (reg_serial, txn_type, txn_date, fee_amount, processed_by, remarks) VALUES (?,?,?,?,?,?)",
                (r[0], "NEW_REGISTRATION", r[2], round(random.uniform(2000, 15000), 2),
                 f"Clerk-{random.randint(100, 999)}", f"New registration for {r[1]}")
            )
            # Random additional transactions
            for _ in range(random.randint(0, 3)):
                txn_date = (datetime.fromisoformat(r[2]) + timedelta(days=random.randint(30, 800))).date().isoformat()
                conn.execute(
                    "INSERT INTO rto_transactions (reg_serial, txn_type, txn_date, fee_amount, processed_by, remarks) VALUES (?,?,?,?,?,?)",
                    (r[0], random.choice(txn_types[1:]), txn_date,
                     round(random.uniform(500, 8000), 2), f"Clerk-{random.randint(100, 999)}",
                     f"Transaction for {r[1]}")
                )

            # Fitness certificate
            issue = (today - timedelta(days=random.randint(30, 700))).isoformat()
            expiry = (today + timedelta(days=random.randint(-60, 500))).isoformat()
            result = random.choices(["PASS", "PASS", "PASS", "CONDITIONAL", "FAIL"], weights=[60, 20, 10, 7, 3])[0]
            cert_num = f"FC-{r[1]}-{random.randint(1000, 9999)}"
            conn.execute(
                "INSERT OR IGNORE INTO fitness_certificates (reg_serial, cert_number, issue_date, expiry_date, inspector_name, inspection_center, result, remarks) VALUES (?,?,?,?,?,?,?,?)",
                (r[0], cert_num, issue, expiry, random.choice(inspectors), random.choice(centers),
                 result, "Annual fitness inspection" if result == "PASS" else "Re-inspection required")
            )
        conn.commit()

    for tbl in ["vehicle_owners", "vehicle_registration", "vehicle_specs", "rto_transactions", "fitness_certificates"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ {tbl}: {cnt} rows")
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# 3. INSURANCE.DB — Insurance Company (4 tables)
# ─────────────────────────────────────────────────────────────────────
def migrate_insurance():
    print("\n🛡️ Migrating insurance.db → 4 tables with FK-PK...")
    conn = sqlite3.connect(DB_INSURANCE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Rename insurance_records to insurance_policies if needed (keep both for compat)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "insurance_policies" not in tables and "insurance_records" in tables:
        # Create insurance_policies as copy of insurance_records
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS insurance_policies (
                policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id TEXT NOT NULL,
                insurer_name TEXT NOT NULL,
                policy_number TEXT UNIQUE NOT NULL,
                policy_start_date TEXT NOT NULL,
                policy_expiry_date TEXT NOT NULL,
                insurance_status TEXT NOT NULL DEFAULT 'ACTIVE',
                vehicle_category TEXT,
                premium_amount REAL,
                nominee_name TEXT,
                coverage_type TEXT DEFAULT 'COMPREHENSIVE',
                claim_count INTEGER DEFAULT 0
            );
        """)
        # Copy data
        existing = conn.execute("SELECT COUNT(*) FROM insurance_policies").fetchone()[0]
        if existing == 0:
            conn.execute("""
                INSERT INTO insurance_policies
                SELECT * FROM insurance_records
            """)
            conn.commit()
    elif "insurance_policies" not in tables:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS insurance_policies (
                policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_id TEXT NOT NULL,
                insurer_name TEXT NOT NULL,
                policy_number TEXT UNIQUE NOT NULL,
                policy_start_date TEXT NOT NULL,
                policy_expiry_date TEXT NOT NULL,
                insurance_status TEXT NOT NULL DEFAULT 'ACTIVE',
                vehicle_category TEXT,
                premium_amount REAL,
                nominee_name TEXT,
                coverage_type TEXT DEFAULT 'COMPREHENSIVE',
                claim_count INTEGER DEFAULT 0
            );
        """)

    # Table 2: insurance_claims (FK → insurance_policies)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS insurance_claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL,
            claim_date TEXT NOT NULL,
            claim_amount REAL NOT NULL,
            claim_type TEXT NOT NULL,
            claim_status TEXT NOT NULL DEFAULT 'FILED',
            description TEXT,
            settlement_amount REAL,
            settlement_date TEXT,
            surveyor_name TEXT,
            FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
        );
        CREATE INDEX IF NOT EXISTS idx_claim_policy ON insurance_claims(policy_id);
    """)

    # Table 3: policy_endorsements (FK → insurance_policies)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS policy_endorsements (
            endorsement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL,
            endorsement_type TEXT NOT NULL,
            endorsement_date TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            processed_by TEXT,
            FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
        );
        CREATE INDEX IF NOT EXISTS idx_endorse_policy ON policy_endorsements(policy_id);
    """)

    # Table 4: premium_payments (FK → insurance_policies)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS premium_payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT NOT NULL DEFAULT 'ONLINE',
            receipt_number TEXT,
            transaction_ref TEXT,
            FOREIGN KEY (policy_id) REFERENCES insurance_policies(policy_id)
        );
        CREATE INDEX IF NOT EXISTS idx_payment_policy ON premium_payments(policy_id);
    """)

    # Seed claims, endorsements, payments
    existing_claims = conn.execute("SELECT COUNT(*) FROM insurance_claims").fetchone()[0]
    if existing_claims == 0:
        policies = conn.execute("SELECT policy_id, registration_id, policy_start_date, premium_amount, insurance_status FROM insurance_policies").fetchall()
        claim_types = ["ACCIDENT", "THEFT", "THIRD_PARTY", "NATURAL_CALAMITY", "FIRE", "VANDALISM"]
        surveyors = ["Ajay Mehta (Sr. Surveyor)", "Neelam Kapoor (Motor Surveyor)", "Ravi Shankar (Loss Assessor)"]
        endorsement_types = ["ADDRESS_CHANGE", "NOMINEE_CHANGE", "VEHICLE_MODIFICATION", "COVERAGE_UPGRADE", "NCB_TRANSFER"]

        for p in policies:
            pid, reg_id, start, premium, status = p[0], p[1], p[2], p[3] or 10000, p[4]

            # Claims: ~15% of policies have claims
            if random.random() < 0.15:
                claim_date = (datetime.fromisoformat(start) + timedelta(days=random.randint(30, 300))).date().isoformat()
                claim_amt = round(random.uniform(5000, 200000), 2)
                ctype = random.choice(claim_types)
                cstatus = random.choice(["FILED", "UNDER_SURVEY", "APPROVED", "SETTLED", "REJECTED"])
                settlement = round(claim_amt * random.uniform(0.5, 0.95), 2) if cstatus == "SETTLED" else None
                conn.execute(
                    "INSERT INTO insurance_claims (policy_id, claim_date, claim_amount, claim_type, claim_status, description, settlement_amount, surveyor_name) VALUES (?,?,?,?,?,?,?,?)",
                    (pid, claim_date, claim_amt, ctype, cstatus,
                     f"{ctype} claim for vehicle {reg_id}", settlement, random.choice(surveyors))
                )

            # Endorsements: ~20% of policies
            if random.random() < 0.20:
                e_date = (datetime.fromisoformat(start) + timedelta(days=random.randint(10, 200))).date().isoformat()
                etype = random.choice(endorsement_types)
                conn.execute(
                    "INSERT INTO policy_endorsements (policy_id, endorsement_type, endorsement_date, old_value, new_value, processed_by) VALUES (?,?,?,?,?,?)",
                    (pid, etype, e_date, "Previous value", "Updated value", f"Agent-{random.randint(100, 999)}")
                )

            # Premium payment
            conn.execute(
                "INSERT INTO premium_payments (policy_id, payment_date, amount, payment_mode, receipt_number, transaction_ref) VALUES (?,?,?,?,?,?)",
                (pid, start, premium or 10000,
                 random.choice(["ONLINE", "UPI", "CHEQUE", "DEBIT_CARD", "NET_BANKING"]),
                 f"RCP-{random.randint(100000, 999999)}", f"TXN-{random.randint(1000000, 9999999)}")
            )
        conn.commit()

    for tbl in ["insurance_policies", "insurance_claims", "policy_endorsements", "premium_payments"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ {tbl}: {cnt} rows")
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# 4. THEFT.DB — Police Records Bureau (4 tables)
# ─────────────────────────────────────────────────────────────────────
def migrate_theft():
    print("\n🚔 Migrating theft.db → 4 tables with FK-PK...")
    conn = sqlite3.connect(DB_THEFT)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Ensure base table has all needed columns
    cols = [r[1] for r in conn.execute("PRAGMA table_info(vehicle_security_records)").fetchall()]
    if "police_station" not in cols:
        conn.execute("ALTER TABLE vehicle_security_records ADD COLUMN police_station TEXT")
    if "recovery_date" not in cols:
        conn.execute("ALTER TABLE vehicle_security_records ADD COLUMN recovery_date TEXT")
    if "remarks" not in cols:
        conn.execute("ALTER TABLE vehicle_security_records ADD COLUMN remarks TEXT")
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE vehicle_security_records ADD COLUMN updated_at TEXT")
    conn.commit()

    # Table 2: investigation_details (FK → vehicle_security_records)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS investigation_details (
            investigation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            investigator_name TEXT NOT NULL,
            police_station TEXT,
            investigation_status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
            last_update TEXT,
            sighting_location TEXT,
            sighting_date TEXT,
            evidence_notes TEXT,
            witness_count INTEGER DEFAULT 0,
            FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
        );
        CREATE INDEX IF NOT EXISTS idx_inv_case ON investigation_details(case_id);
    """)

    # Table 3: recovery_records (FK → vehicle_security_records)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recovery_records (
            recovery_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            recovery_date TEXT NOT NULL,
            recovery_location TEXT NOT NULL,
            condition_on_recovery TEXT,
            recovered_by TEXT,
            handover_date TEXT,
            damage_estimate REAL,
            FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
        );
        CREATE INDEX IF NOT EXISTS idx_rec_case ON recovery_records(case_id);
    """)

    # Table 4: suspect_info (FK → vehicle_security_records)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS suspect_info (
            suspect_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            suspect_name TEXT,
            suspect_description TEXT,
            last_known_location TEXT,
            identified_date TEXT,
            arrest_status TEXT DEFAULT 'AT_LARGE',
            FOREIGN KEY (case_id) REFERENCES vehicle_security_records(case_id)
        );
        CREATE INDEX IF NOT EXISTS idx_susp_case ON suspect_info(case_id);
    """)

    # Seed investigation, recovery, suspect records
    existing_inv = conn.execute("SELECT COUNT(*) FROM investigation_details").fetchone()[0]
    if existing_inv == 0:
        cases = conn.execute("SELECT case_id, vehicle_identifier, case_type, case_status, reported_date FROM vehicle_security_records").fetchall()
        investigators = ["SI Raman Kumar", "Insp. Deepa Nair", "ASI Sunil Yadav", "DSP Arvind Kejriwal", "CI Meera Deshmukh"]
        stations = ["Sarita Vihar PS", "Dwarka Sector 7 PS", "Koramangala PS", "Andheri West PS", "Noida Sector 20 PS", "Cyber Crime Cell HQ"]
        locations = ["Near Noida Expressway", "Faridabad-Palwal Highway", "Gurgaon Industrial Area",
                     "Mumbai-Nashik Highway", "Bangalore Whitefield", "Chennai Ambattur"]

        for c in cases:
            cid, vid, ctype, cstatus, rep_date = c[0], c[1], c[2], c[3], c[4]

            # Investigation details
            for i in range(random.randint(1, 3)):
                inv_status = "CLOSED" if cstatus == "CLOSED" else random.choice(["IN_PROGRESS", "LEAD_FOUND", "DEAD_END", "TRANSFERRED"])
                sighting = random.choice(locations) if random.random() < 0.4 else None
                s_date = (datetime.fromisoformat(rep_date) + timedelta(days=random.randint(1, 30))).date().isoformat() if sighting else None
                conn.execute(
                    "INSERT INTO investigation_details (case_id, investigator_name, police_station, investigation_status, last_update, sighting_location, sighting_date, evidence_notes, witness_count) VALUES (?,?,?,?,?,?,?,?,?)",
                    (cid, random.choice(investigators), random.choice(stations), inv_status,
                     (datetime.fromisoformat(rep_date) + timedelta(days=random.randint(1, 60))).date().isoformat(),
                     sighting, s_date,
                     f"Investigation update for case {vid}: {inv_status}",
                     random.randint(0, 5))
                )

            # Recovery records (for some cases)
            if cstatus == "CLOSED" or random.random() < 0.3:
                rec_date = (datetime.fromisoformat(rep_date) + timedelta(days=random.randint(5, 90))).date().isoformat()
                conn.execute(
                    "INSERT INTO recovery_records (case_id, recovery_date, recovery_location, condition_on_recovery, recovered_by, damage_estimate) VALUES (?,?,?,?,?,?)",
                    (cid, rec_date, random.choice(locations),
                     random.choice(["INTACT", "MINOR_DAMAGE", "MAJOR_DAMAGE", "STRIPPED", "BURNT"]),
                     random.choice(investigators), round(random.uniform(0, 500000), 2))
                )

            # Suspect info (for some cases)
            if random.random() < 0.4:
                suspect_names = ["Unknown Male", "Raju alias Spider", "Mohammad Sharif", "Govind Verma", "Unidentified"]
                conn.execute(
                    "INSERT INTO suspect_info (case_id, suspect_name, suspect_description, last_known_location, identified_date, arrest_status) VALUES (?,?,?,?,?,?)",
                    (cid, random.choice(suspect_names),
                     f"Height ~{random.randint(155, 185)}cm, age ~{random.randint(20, 45)}",
                     random.choice(locations),
                     (datetime.fromisoformat(rep_date) + timedelta(days=random.randint(2, 40))).date().isoformat(),
                     random.choice(["AT_LARGE", "ARRESTED", "ABSCONDING", "RELEASED_ON_BAIL"]))
                )
        conn.commit()

    for tbl in ["vehicle_security_records", "investigation_details", "recovery_records", "suspect_info"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ {tbl}: {cnt} rows")
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# 5. MINISTRY.DB — Ministry of Transport (4 tables)
# ─────────────────────────────────────────────────────────────────────
def migrate_ministry():
    print("\n🏢 Migrating ministry.db → 4 tables with FK-PK...")
    conn = sqlite3.connect(DB_MINISTRY)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Ensure base table columns
    cols = [r[1] for r in conn.execute("PRAGMA table_info(transport_reports)").fetchall()]
    if "action_taken" not in cols:
        conn.execute("ALTER TABLE transport_reports ADD COLUMN action_taken TEXT")
    if "resolution_date" not in cols:
        conn.execute("ALTER TABLE transport_reports ADD COLUMN resolution_date TEXT")
    if "notes" not in cols:
        conn.execute("ALTER TABLE transport_reports ADD COLUMN notes TEXT")
    if "submitted_by" not in cols:
        conn.execute("ALTER TABLE transport_reports ADD COLUMN submitted_by TEXT")
    conn.commit()

    # Table 2: enforcement_actions (FK → transport_reports)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS enforcement_actions (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_date TEXT NOT NULL,
            fine_amount REAL,
            action_status TEXT NOT NULL DEFAULT 'PENDING',
            officer_name TEXT,
            enforcement_zone TEXT,
            FOREIGN KEY (report_id) REFERENCES transport_reports(report_id)
        );
        CREATE INDEX IF NOT EXISTS idx_enf_report ON enforcement_actions(report_id);
    """)

    # Table 3: compliance_history
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS compliance_history (
            compliance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            report_id INTEGER,
            compliance_type TEXT NOT NULL,
            compliance_date TEXT NOT NULL,
            was_compliant INTEGER DEFAULT 0,
            remarks TEXT,
            FOREIGN KEY (report_id) REFERENCES transport_reports(report_id)
        );
        CREATE INDEX IF NOT EXISTS idx_comp_vref ON compliance_history(vehicle_ref);
        CREATE INDEX IF NOT EXISTS idx_comp_report ON compliance_history(report_id);
    """)

    # Table 4: blacklisted_vehicles
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS blacklisted_vehicles (
            blacklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            blacklist_reason TEXT NOT NULL,
            blacklist_date TEXT NOT NULL,
            removal_date TEXT,
            is_active INTEGER DEFAULT 1,
            blacklisted_by TEXT,
            jurisdiction TEXT DEFAULT 'NATIONAL'
        );
        CREATE INDEX IF NOT EXISTS idx_bl_vref ON blacklisted_vehicles(vehicle_ref);
        CREATE INDEX IF NOT EXISTS idx_bl_active ON blacklisted_vehicles(is_active);
    """)

    # Seed enforcement, compliance, blacklist
    existing_enf = conn.execute("SELECT COUNT(*) FROM enforcement_actions").fetchone()[0]
    if existing_enf == 0:
        reports = conn.execute("SELECT report_id, vehicle_ref, report_type, severity, report_date FROM transport_reports").fetchall()
        officers = ["ATO K. Sharma", "RTO M. Patel", "DTO S. Reddy", "JTO A. Kumar", "MVI R. Singh"]
        zones = ["Delhi NCR", "Mumbai Metropolitan", "Bangalore Urban", "Chennai Zone-1", "Kolkata Central", "Hyderabad IT Corridor"]
        compliance_types = ["INSURANCE_CHECK", "FITNESS_CHECK", "TAX_CHECK", "EMISSION_CHECK", "PERMIT_CHECK"]

        for r in reports:
            rid, vref, rtype, severity, rdate = r[0], r[1], r[2], r[3], r[4]

            # Enforcement actions
            action_types_map = {
                "UNINSURED_VEHICLE": ["NOTICE_ISSUED", "FINE_IMPOSED", "VEHICLE_SEIZED"],
                "THEFT_ALERT": ["ALERT_BROADCAST", "CHECKPOINT_FLAGGED", "IMPOUND_ORDER"],
                "SCRAP_VIOLATION": ["NOTICE_ISSUED", "FINE_IMPOSED", "BLACKLISTED"],
                "SUSPICIOUS_MOVEMENT": ["SURVEILLANCE_ORDER", "CHECKPOINT_FLAGGED"],
            }
            atypes = action_types_map.get(rtype, ["NOTICE_ISSUED"])
            for atype in random.sample(atypes, min(len(atypes), random.randint(1, 2))):
                fine = round(random.uniform(500, 25000), 2) if "FINE" in atype else 0
                conn.execute(
                    "INSERT INTO enforcement_actions (report_id, action_type, action_date, fine_amount, action_status, officer_name, enforcement_zone) VALUES (?,?,?,?,?,?,?)",
                    (rid, atype,
                     (datetime.fromisoformat(rdate) + timedelta(days=random.randint(1, 15))).date().isoformat(),
                     fine, random.choice(["PENDING", "EXECUTED", "APPEALED"]),
                     random.choice(officers), random.choice(zones))
                )

            # Compliance history
            conn.execute(
                "INSERT INTO compliance_history (vehicle_ref, report_id, compliance_type, compliance_date, was_compliant, remarks) VALUES (?,?,?,?,?,?)",
                (vref, rid, random.choice(compliance_types), rdate,
                 0, f"Non-compliance detected: {rtype}")
            )

            # Blacklist (for severe cases)
            if severity in ("CRITICAL", "HIGH") and random.random() < 0.4:
                conn.execute(
                    "INSERT INTO blacklisted_vehicles (vehicle_ref, blacklist_reason, blacklist_date, is_active, blacklisted_by, jurisdiction) VALUES (?,?,?,?,?,?)",
                    (vref, f"Blacklisted due to {rtype}", rdate, 1,
                     random.choice(officers), random.choice(["NATIONAL", "STATE", "CITY"]))
                )
        conn.commit()

    for tbl in ["transport_reports", "enforcement_actions", "compliance_history", "blacklisted_vehicles"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  ✓ {tbl}: {cnt} rows")
    conn.close()


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 PHASE 3 DATABASE MIGRATION — Expanding to 4-5 Tables with FK-PK")
    print("=" * 70)

    migrate_capture()
    migrate_registration()
    migrate_insurance()
    migrate_theft()
    migrate_ministry()

    print("\n" + "=" * 70)
    print("🎉 PHASE 3 MIGRATION COMPLETE — All 5 databases expanded with FK-PK!")
    print("=" * 70)
    print("\nFK-PK Relationships Created:")
    print("  capture.db:      cameras ← vehicle_capture → capture_alerts, operator_logs")
    print("  registration.db: vehicle_owners ← vehicle_registration → vehicle_specs, rto_transactions, fitness_certificates")
    print("  insurance.db:    insurance_policies → insurance_claims, policy_endorsements, premium_payments")
    print("  theft.db:        vehicle_security_records → investigation_details, recovery_records, suspect_info")
    print("  ministry.db:     transport_reports → enforcement_actions, compliance_history, blacklisted_vehicles")
