"""
Seed 1000 Vehicles Script for IIA Distributed Vehicle Integration System
Populates all 5 independent SQLite databases with 1,000 coherent, realistic vehicles.
Includes all asset image vehicles extracted with Google Gemini Vision & local ANPR:
  - test0.9.jpeg: DL7CQ1939 (Hyundai Creta, BLACK, SUV)
  - test1.jpg:    MH20DV2366 (Maruti Suzuki Swift, WHITE, Hatchback)
  - test2.jpg:    22BH6517A (Mahindra Scorpio, WHITE, SUV)
  - tes3.jpg:     J389NLT (Ford Fiesta, RED, Car)
  - test4.jpg:    TN09BY9726 (Hyundai i20, SILVER, Car)
  - test5.jpg:    AP40C1235 (Toyota Innova, WHITE, MUV)
  - test6.jpg:    AP CM JAGAN (Toyota Fortuner, BLACK, SUV)
  - test0.4.jpg:  SN66XMZ (Ford Focus, SILVER, Car)

Run: python scripts/seed_1000_records.py
"""
import sys
import os
import random
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, date

# Set UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_CAPTURE = str(DATA_DIR / "capture.db")
DB_INSURANCE = str(DATA_DIR / "insurance.db")
DB_REGISTRATION = str(DATA_DIR / "registration.db")
DB_THEFT = str(DATA_DIR / "theft.db")
DB_MINISTRY = str(DATA_DIR / "ministry.db")

random.seed(42)  # Deterministic seed for reproducible evaluation

# ── Realistic Vehicle Data Pools ──
INDIAN_STATES = [
    ("DL", "Delhi", ["DL-01 North Delhi (Mall Road)", "DL-02 New Delhi (Tilak Marg)", "DL-07 South West Delhi (Dwarka)", "DL-09 West Delhi (Janakpuri)", "DL-10 West Delhi (Raja Garden)"]),
    ("MH", "Maharashtra", ["MH-01 Mumbai South", "MH-02 Mumbai West (Andheri)", "MH-04 Thane", "MH-12 Pune Central", "MH-20 Aurangabad"]),
    ("KA", "Karnataka", ["KA-01 Bangalore Central (Koramangala)", "KA-03 Bangalore East (Indiranagar)", "KA-05 Bangalore South (Jayanagar)", "KA-09 Mysore"]),
    ("UP", "Uttar Pradesh", ["UP-14 Ghaziabad", "UP-16 Noida (Gautam Buddha Nagar)", "UP-32 Lucknow Central", "UP-78 Kanpur"]),
    ("TN", "Tamil Nadu", ["TN-01 Chennai Central", "TN-05 Chennai North", "TN-07 Chennai South", "TN-09 Chennai West"]),
    ("HR", "Haryana", ["HR-26 Gurugram North", "HR-29 Faridabad", "HR-05 Karnal"]),
    ("GJ", "Gujarat", ["GJ-01 Ahmedabad West", "GJ-06 Vadodara", "GJ-27 Ahmedabad East"]),
    ("RJ", "Rajasthan", ["RJ-14 Jaipur South", "RJ-27 Udaipur", "RJ-07 Bikaner"]),
    ("PB", "Punjab", ["PB-10 Ludhiana", "PB-08 Jalandhar", "PB-65 Mohali"]),
    ("MP", "Madhya Pradesh", ["MP-09 Indore", "MP-04 Bhopal"]),
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepak", "Divya", "Gaurav", "Harish", "Ishaan",
    "Kavita", "Karan", "Manish", "Meera", "Mohit", "Neha", "Nikhil", "Pooja", "Pranav", "Priya",
    "Rahul", "Rakesh", "Ramesh", "Ritu", "Rohan", "Sanjay", "Siddharth", "Sneha", "Sunil", "Sunita",
    "Tanvi", "Varun", "Vikram", "Vivek", "Anupama", "Charan", "Suresh", "Rajesh", "Pankaj", "Vikas"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Reddy", "Nair", "Rao", "Iyer",
    "Chopra", "Malhotra", "Mehta", "Joshi", "Bhatia", "Saxena", "Deshmukh", "Kulkarni", "Banerjee", "Chatterjee",
    "Mishra", "Pandey", "Agarwal", "Jain", "Shah", "Kapoor", "Bose", "Ghosh", "Das", "Yadav"
]

MANUFACTURERS_MODELS = [
    ("Hyundai", [("Creta 1.6 VTVT", "SUV / Private"), ("i20 Asta", "Hatchback"), ("Venue SX", "Compact SUV"), ("Verna SX(O)", "Sedan"), ("Tucson 2.0 CRDi", "Premium SUV")]),
    ("Maruti Suzuki", [("Swift ZXi", "Hatchback"), ("Baleno Alpha", "Premium Hatchback"), ("Brezza ZXi+", "Compact SUV"), ("Dzire ZXi", "Compact Sedan"), ("Ertiga ZXi", "MUV")]),
    ("Tata Motors", [("Nexon Fearless", "Compact SUV"), ("Harrier XZA+", "Mid-size SUV"), ("Safari Accomplished", "Full-size SUV"), ("Punch Creative", "Micro SUV"), ("Altroz XZ+", "Hatchback")]),
    ("Mahindra", [("Scorpio-N Z8L", "SUV / Private"), ("XUV700 AX7L", "Premium SUV"), ("Thar LX 4x4", "Off-road SUV"), ("Bolero Neo N10", "Utility SUV")]),
    ("Honda", [("City ZX CVT", "Sedan"), ("Amaze VX", "Compact Sedan"), ("Elevate ZX", "Mid-size SUV")]),
    ("Toyota", [("Innova Hycross ZX", "Premium MUV"), ("Fortuner 4x4", "Full-size SUV"), ("Urban Cruiser Hyryder", "Hybrid SUV"), ("Glanza V", "Hatchback")]),
    ("Kia", [("Seltos GTX+", "Mid-size SUV"), ("Sonet HTX", "Compact SUV"), ("Carens Luxury Plus", "MUV")]),
    ("Volkswagen", [("Virtus GT Plus", "Sedan"), ("Taigun GT Plus", "Compact SUV")]),
    ("Skoda", [("Slavia Style", "Sedan"), ("Kushaq Monte Carlo", "Compact SUV")]),
    ("Mercedes-Benz", [("C-Class C300", "Luxury Sedan"), ("E-Class E220d", "Executive Sedan"), ("GLC 300 4MATIC", "Luxury SUV")]),
    ("BMW", [("3 Series 330Li", "Luxury Sedan"), ("X3 xDrive30i", "Luxury SUV")]),
]

COLORS = ["WHITE", "SILVER", "BLACK", "GREY", "RED", "BLUE", "BROWN", "GOLDEN"]
FUEL_TYPES = ["PETROL", "DIESEL", "CNG", "ELECTRIC", "HYBRID"]

INSURERS = [
    "HDFC ERGO General Insurance",
    "ICICI Lombard General Insurance",
    "Bajaj Allianz General Insurance",
    "Tata AIG General Insurance",
    "New India Assurance Co.",
    "National Insurance Co.",
    "Oriental Insurance Co.",
    "United India Insurance Co.",
    "SBI General Insurance",
    "Reliance General Insurance"
]

COVERAGE_TYPES = ["Comprehensive", "Zero Depreciation Bumper-to-Bumper", "Third Party Only", "Comprehensive with Engine Protect"]

CAMERAS = [
    ("CAM-DEL-01", "Sarita Vihar Checkpost, Delhi", 1),
    ("CAM-DEL-02", "DND Flyway Toll Plaza, Delhi-Noida", 2),
    ("CAM-DEL-03", "Connaught Place Outer Circle, Delhi", 1),
    ("CAM-DEL-04", "Dwarka Expressway Km 12, Delhi", 3),
    ("CAM-MUM-01", "Bandra-Worli Sea Link Toll, Mumbai", 2),
    ("CAM-MUM-02", "Western Express Highway, Andheri", 1),
    ("CAM-BLR-01", "Electronic City Elevated Tollway, Bengaluru", 1),
    ("CAM-BLR-02", "Outer Ring Road (Marathahalli), Bengaluru", 2),
    ("CAM-HYD-01", "Gachibowli Junction Toll Plaza, Hyderabad", 2),
    ("CAM-CHN-01", "OMR IT Corridor Checkpoint, Chennai", 1),
    ("CAM-PUN-01", "Mumbai-Pune Expressway Toll Gate 3", 3),
    ("CAM-AHM-01", "SG Highway Flyover, Ahmedabad", 2),
]


def create_schema_if_needed():
    """Ensure all 5 tables exist with exact schemas."""
    # Capture DB
    conn = sqlite3.connect(DB_CAPTURE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_capture (
            capture_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            detected_vehicle_type TEXT,
            detected_color TEXT,
            capture_timestamp TEXT NOT NULL,
            capture_location TEXT,
            image_path TEXT,
            detection_confidence REAL,
            ocr_confidence REAL,
            camera_id TEXT,
            lane_number INTEGER
        )
    """)
    conn.close()

    # Registration DB
    conn = sqlite3.connect(DB_REGISTRATION)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_registration (
            reg_serial INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_reg_no TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            owner_contact TEXT,
            owner_address TEXT,
            registration_date TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            model_name TEXT NOT NULL,
            vehicle_class TEXT NOT NULL,
            registered_color TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            engine_number TEXT,
            chassis_number TEXT,
            seating_capacity INTEGER,
            registration_status TEXT NOT NULL,
            rto_office TEXT NOT NULL,
            fitness_valid_until TEXT,
            tax_valid_until TEXT
        )
    """)
    conn.close()

    # Insurance DB
    conn = sqlite3.connect(DB_INSURANCE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS insurance_records (
            policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id TEXT NOT NULL,
            insurer_name TEXT NOT NULL,
            policy_number TEXT UNIQUE NOT NULL,
            policy_start_date TEXT NOT NULL,
            policy_expiry_date TEXT NOT NULL,
            insurance_status TEXT NOT NULL,
            vehicle_category TEXT,
            premium_amount REAL,
            nominee_name TEXT,
            coverage_type TEXT,
            claim_count INTEGER DEFAULT 0
        )
    """)
    conn.close()

    # Theft DB
    conn = sqlite3.connect(DB_THEFT)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_security_records (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_identifier TEXT NOT NULL,
            case_type TEXT NOT NULL,
            case_status TEXT NOT NULL,
            reported_date TEXT NOT NULL,
            police_reference TEXT,
            shredding_status TEXT,
            fir_number TEXT
        )
    """)
    conn.close()

    # Ministry DB
    conn = sqlite3.connect(DB_MINISTRY)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transport_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            report_type TEXT NOT NULL,
            report_date TEXT NOT NULL,
            reason TEXT,
            severity TEXT NOT NULL,
            report_status TEXT NOT NULL,
            action_taken TEXT
        )
    """)
    conn.close()


def generate_1000_vehicles():
    print("=" * 70)
    print("🚀 GENERATING 1,000 VEHICLE RECORDS ACROSS ALL 5 INDEPENDENT DATABASES")
    print("=" * 70)

    create_schema_if_needed()

    # Clear existing records for clean seed
    for db_path, table in [
        (DB_CAPTURE, "vehicle_capture"),
        (DB_REGISTRATION, "vehicle_registration"),
        (DB_INSURANCE, "insurance_records"),
        (DB_THEFT, "vehicle_security_records"),
        (DB_MINISTRY, "transport_reports"),
    ]:
        conn = sqlite3.connect(db_path)
        conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()

    today = date(2026, 10, 21)

    # ── 1. Priority Anchor Vehicles from Image Assets ──
    anchor_vehicles = [
        {
            "plate": "DL7CQ1939",
            "make": "Hyundai",
            "model": "Creta 1.6 VTVT",
            "vclass": "SUV / Private",
            "color": "BLACK",
            "fuel": "PETROL",
            "owner": "Rahul Sharma",
            "rto": "DL-07 South West Delhi (Dwarka)",
            "address": "Pocket A, Sarita Vihar, South Delhi",
            "phone": "+91-98110-12345",
            "image": "test_assets/assets/test0.9.jpeg",
            "insurance_status": "ACTIVE",
            "insurer": "HDFC ERGO General Insurance",
            "policy_no": "HDFC-COMP-778899",
            "theft_status": "OPEN",
            "ministry_report": "THEFT_ALERT",
        },
        {
            "plate": "MH20DV2366",
            "make": "Maruti Suzuki",
            "model": "Swift ZXi",
            "vclass": "Hatchback",
            "color": "WHITE",
            "fuel": "PETROL",
            "owner": "Ganesh Kulkarni",
            "rto": "MH-20 Aurangabad",
            "address": "Samarth Nagar, Aurangabad",
            "phone": "+91-98220-44556",
            "image": "test_assets/assets/test1.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "Bajaj Allianz General Insurance",
            "policy_no": "BAJAJ-2025-112233",
            "theft_status": None,
            "ministry_report": None,
        },
        {
            "plate": "22BH6517A",
            "make": "Mahindra",
            "model": "Scorpio-N Z8L",
            "vclass": "SUV / Private",
            "color": "WHITE",
            "fuel": "DIESEL",
            "owner": "Maj. Vikramaditya Rathore",
            "rto": "Central RTO (Bharat Series HQ)",
            "address": "Defence Colony Officers Mess, New Delhi",
            "phone": "+91-98101-77889",
            "image": "test_assets/assets/test2.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "National Insurance Co.",
            "policy_no": "NIC-BH-2025-9988",
            "theft_status": None,
            "ministry_report": None,
        },
        {
            "plate": "SN66XMZ",
            "make": "Ford",
            "model": "Focus Titanium",
            "vclass": "Sedan",
            "color": "SILVER",
            "fuel": "PETROL",
            "owner": "Edward Sterling",
            "rto": "International Transport Registry (DVLA UK)",
            "address": "14 Kensington Road, London / Diplomatic Mission Delhi",
            "phone": "+44-7700-900123",
            "image": "test_assets/assets/test0.4.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "Aviva International Insurance",
            "policy_no": "UK-AVIVA-2025-4433",
            "theft_status": None,
            "ministry_report": None,
        },
        {
            "plate": "J389NLT",
            "make": "Ford",
            "model": "Fiesta Classic",
            "vclass": "Hatchback",
            "color": "RED",
            "fuel": "PETROL",
            "owner": "Arthur Pendelton",
            "rto": "International Transport Registry (DVLA UK)",
            "address": "Embassy of Great Britain, Shantipath, New Delhi",
            "phone": "+44-7911-123456",
            "image": "test_assets/assets/tes3.jpg",
            "insurance_status": "EXPIRED",
            "insurer": "Direct Line UK",
            "policy_no": "DL-UK-2023-8877",
            "theft_status": None,
            "ministry_report": "UNINSURED_VEHICLE",
        },
        {
            "plate": "TN09BY9726",
            "make": "Hyundai",
            "model": "i20 Asta",
            "vclass": "Hatchback",
            "color": "SILVER",
            "fuel": "PETROL",
            "owner": "Karthik Subramanian",
            "rto": "TN-09 Chennai West",
            "address": "T. Nagar, Chennai, Tamil Nadu",
            "phone": "+91-98400-33221",
            "image": "test_assets/assets/test4.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "United India Insurance Co.",
            "policy_no": "UII-TN-2025-6677",
            "theft_status": None,
            "ministry_report": None,
        },
        {
            "plate": "AP40C1235",
            "make": "Toyota",
            "model": "Innova Hycross ZX",
            "vclass": "Premium MUV",
            "color": "WHITE",
            "fuel": "HYBRID",
            "owner": "Venkata Raman",
            "rto": "AP-40 Vijayawada Central",
            "address": "MG Road, Vijayawada, Andhra Pradesh",
            "phone": "+91-98480-11223",
            "image": "test_assets/assets/test5.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "Tata AIG General Insurance",
            "policy_no": "TATA-AP-2025-8844",
            "theft_status": None,
            "ministry_report": None,
        },
        {
            "plate": "AP CM JAGAN",
            "make": "Toyota",
            "model": "Fortuner 4x4",
            "vclass": "Full-size SUV",
            "color": "BLACK",
            "fuel": "DIESEL",
            "owner": "VIP State Protocol Division",
            "rto": "Government Convoy Registry (AP VIP)",
            "address": "Secretariat Complex, Velagapudi, Andhra Pradesh",
            "phone": "+91-863-2444555",
            "image": "test_assets/assets/test6.jpg",
            "insurance_status": "ACTIVE",
            "insurer": "New India Assurance Co.",
            "policy_no": "NIA-GOV-2025-0001",
            "theft_status": None,
            "ministry_report": None,
        },
    ]

    all_plates = set()
    vehicles = []

    # Add anchors first
    for a in anchor_vehicles:
        all_plates.add(a["plate"])
        vehicles.append(a)

    # ── 2. Generate 992 Remaining Vehicles up to 1,000 ──
    series_letters = ["AB", "CD", "EF", "GH", "JK", "MN", "PQ", "RS", "TU", "VW", "XY", "ZA", "BC", "DE"]

    while len(vehicles) < 1000:
        # Choose state
        state_code, state_name, rtos = random.choice(INDIAN_STATES)
        rto_choice = random.choice(rtos)
        rto_num = rto_choice.split()[0]  # e.g. DL-07

        # 95% standard format: SS-DD-LL-NNNN, 5% Bharat Series: YY-BH-NNNN-L
        if random.random() < 0.05:
            yr = random.choice(["21", "22", "23", "24", "25"])
            num = f"{random.randint(1000, 9999)}"
            let = random.choice(["A", "B", "C", "D", "E"])
            plate = f"{yr}BH{num}{let}"
            rto_choice = "Central RTO (Bharat Series HQ)"
        else:
            state_prefix = state_code
            dist_code = rto_num.split("-")[1]
            letters = random.choice(series_letters)
            number = f"{random.randint(1000, 9999)}"
            plate = f"{state_prefix}{dist_code}{letters}{number}"

        if plate in all_plates:
            continue
        all_plates.add(plate)

        owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = f"+91-{random.randint(90000, 99999)}-{random.randint(10000, 99999)}"
        address = f"House No. {random.randint(1, 450)}, Sector {random.randint(1, 65)}, {state_name}"
        
        mfg, models = random.choice(MANUFACTURERS_MODELS)
        model_name, vclass = random.choice(models)
        color = random.choice(COLORS)
        fuel = random.choice(FUEL_TYPES)

        # Insurance distribution:
        # 70% ACTIVE, 15% EXPIRED, 5% CANCELLED, 10% UNINSURED (no record in insurance.db)
        rand_ins = random.random()
        if rand_ins < 0.70:
            ins_status = "ACTIVE"
        elif rand_ins < 0.85:
            ins_status = "EXPIRED"
        elif rand_ins < 0.90:
            ins_status = "CANCELLED"
        else:
            ins_status = None  # Completely Uninsured!

        insurer = random.choice(INSURERS) if ins_status else None
        policy_no = f"{insurer[:3].upper()}-{random.randint(1000, 9999)}-{plate}" if ins_status else None

        # Theft status: 92% None, 5% THEFT, 2% WANTED, 1% SCRAPPED
        rand_theft = random.random()
        if rand_theft < 0.05:
            theft_status = "THEFT"
        elif rand_theft < 0.07:
            theft_status = "WANTED"
        elif rand_theft < 0.08:
            theft_status = "SCRAPPED"
        else:
            theft_status = None

        # Ministry report:
        if ins_status is None:
            ministry_report = "UNINSURED_VEHICLE"
        elif theft_status == "THEFT":
            ministry_report = "THEFT_ALERT"
        elif theft_status == "SCRAPPED":
            ministry_report = "SCRAP_VIOLATION"
        elif random.random() < 0.03:
            ministry_report = "SUSPICIOUS_MOVEMENT"
        else:
            ministry_report = None

        vehicles.append({
            "plate": plate,
            "make": mfg,
            "model": model_name,
            "vclass": vclass,
            "color": color,
            "fuel": fuel,
            "owner": owner,
            "rto": rto_choice,
            "address": address,
            "phone": phone,
            "image": None,
            "insurance_status": ins_status,
            "insurer": insurer,
            "policy_no": policy_no,
            "theft_status": theft_status,
            "ministry_report": ministry_report,
        })

    print(f"Generated {len(vehicles)} vehicles in memory. Inserting into 5 SQLite databases...")

    # ── Database Batch Inserts ──
    reg_rows = []
    ins_rows = []
    theft_rows = []
    min_rows = []
    cap_rows = []

    for v in vehicles:
        reg_date = (today - timedelta(days=random.randint(60, 2000))).isoformat()
        fitness = (today + timedelta(days=random.randint(200, 1500))).isoformat()
        tax = (today + timedelta(days=random.randint(300, 2000))).isoformat()

        # 1. Registration Row
        reg_rows.append((
            v["plate"], v["owner"], v["phone"], v["address"], reg_date,
            v["make"], v["model"], v["vclass"], v["color"], v["fuel"],
            f"ENG-{v['plate']}-{random.randint(100, 999)}",
            f"CHS-{v['plate']}-{random.randint(1000, 9999)}",
            random.choice([5, 7, 4]),
            "ACTIVE", v["rto"], fitness, tax
        ))

        # 2. Insurance Row (if insured)
        if v["insurance_status"]:
            if v["insurance_status"] == "ACTIVE":
                p_start = (today - timedelta(days=random.randint(10, 300))).isoformat()
                p_exp = (today + timedelta(days=random.randint(60, 400))).isoformat()
            else:
                p_start = (today - timedelta(days=random.randint(400, 800))).isoformat()
                p_exp = (today - timedelta(days=random.randint(10, 150))).isoformat()

            prem = round(random.uniform(8500.0, 48000.0), 2)
            ins_rows.append((
                v["plate"], v["insurer"], v["policy_no"], p_start, p_exp,
                v["insurance_status"], v["vclass"], prem,
                f"Nominee {v['owner'].split()[0]}", random.choice(COVERAGE_TYPES),
                random.randint(0, 2)
            ))

        # 3. Theft Row (if any)
        if v["theft_status"]:
            rep_date = (today - timedelta(days=random.randint(2, 60))).isoformat()
            fir = f"FIR-{v['plate'][:4]}-{random.randint(1000, 9999)}"
            shred = "SCRAPPED" if v["theft_status"] == "SCRAPPED" else "NOT_SCRAPPED"
            theft_rows.append((
                v["plate"], v["theft_status"], "OPEN" if v["theft_status"] != "SCRAPPED" else "CLOSED",
                rep_date, f"PS-{random.randint(10, 99)}-REF", shred, fir
            ))

        # 4. Ministry Row (if any)
        if v["ministry_report"]:
            rep_date = (today - timedelta(days=random.randint(1, 30))).isoformat()
            sev = "CRITICAL" if v["ministry_report"] == "THEFT_ALERT" else ("HIGH" if v["ministry_report"] == "UNINSURED_VEHICLE" else "MEDIUM")
            reason = f"Automated camera detection: {v['ministry_report']}"
            action = "Alert sent to nearest interception checkpoint" if sev == "CRITICAL" else "Notice sent to registered vehicle owner"
            min_rows.append((
                v["plate"], v["ministry_report"], rep_date, reason, sev, "ACTIONED", action
            ))

        # 5. Capture Row (Surveillance simulation: 60% of vehicles appear in traffic camera feeds)
        if v["image"] or random.random() < 0.60:
            cam_id, cam_loc, lane = random.choice(CAMERAS)
            cap_time = (today - timedelta(hours=random.randint(1, 72))).isoformat()
            det_conf = round(random.uniform(0.92, 0.99), 2)
            ocr_conf = round(random.uniform(0.88, 0.98), 4)
            cap_rows.append((
                v["plate"], v["vclass"].split("/")[0].strip(), v["color"], cap_time,
                cam_loc, v["image"], det_conf, ocr_conf, cam_id, lane
            ))

    # Commit Registration
    conn = sqlite3.connect(DB_REGISTRATION)
    conn.executemany("""
        INSERT INTO vehicle_registration (
            vehicle_reg_no, owner_name, owner_contact, owner_address, registration_date,
            manufacturer, model_name, vehicle_class, registered_color, fuel_type,
            engine_number, chassis_number, seating_capacity, registration_status,
            rto_office, fitness_valid_until, tax_valid_until
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, reg_rows)
    conn.commit()
    conn.close()
    print(f"  ✓ registration.db:  {len(reg_rows)} vehicles inserted")

    # Commit Insurance
    conn = sqlite3.connect(DB_INSURANCE)
    conn.executemany("""
        INSERT INTO insurance_records (
            registration_id, insurer_name, policy_number, policy_start_date,
            policy_expiry_date, insurance_status, vehicle_category, premium_amount,
            nominee_name, coverage_type, claim_count
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, ins_rows)
    conn.commit()
    conn.close()
    print(f"  ✓ insurance.db:     {len(ins_rows)} policies inserted ({len(reg_rows) - len(ins_rows)} Uninsured vehicles)")

    # Commit Theft
    conn = sqlite3.connect(DB_THEFT)
    conn.executemany("""
        INSERT INTO vehicle_security_records (
            vehicle_identifier, case_type, case_status, reported_date,
            police_reference, shredding_status, fir_number
        ) VALUES (?,?,?,?,?,?,?)
    """, theft_rows)
    conn.commit()
    conn.close()
    print(f"  ✓ theft.db:         {len(theft_rows)} security/theft cases inserted")

    # Commit Ministry
    conn = sqlite3.connect(DB_MINISTRY)
    conn.executemany("""
        INSERT INTO transport_reports (
            vehicle_ref, report_type, report_date, reason, severity, report_status, action_taken
        ) VALUES (?,?,?,?,?,?,?)
    """, min_rows)
    conn.commit()
    conn.close()
    print(f"  ✓ ministry.db:      {len(min_rows)} ministry violation reports inserted")

    # Commit Capture
    conn = sqlite3.connect(DB_CAPTURE)
    conn.executemany("""
        INSERT INTO vehicle_capture (
            plate_number, detected_vehicle_type, detected_color, capture_timestamp,
            capture_location, image_path, detection_confidence, ocr_confidence,
            camera_id, lane_number
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, cap_rows)
    conn.commit()
    conn.close()
    print(f"  ✓ capture.db:       {len(cap_rows)} surveillance camera captures inserted")

    print("\n" + "=" * 70)
    print("🎉 SUCCESS: ALL 5 DATABASES SEEDED WITH 1,000 VEHICLES AND ANCHOR ASSETS!")
    print("=" * 70)


if __name__ == "__main__":
    generate_1000_vehicles()
