"""
Database Manager & Reset Tool
==============================
Usage:
  python scripts/db_manager.py --clean
      -> Empties all tables across all 5 databases (Master, Node A, Node B)
  
  python scripts/db_manager.py --seed
      -> Seeds fresh test vehicles (DL7CQ1939, MH20DV2366, 22BH6517A, SN66XMZ)

  python scripts/db_manager.py --demo-crud
      -> Runs live INSERT -> UPDATE -> DELETE demo across distributed nodes
"""
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DBS = {
    "capture": {
        "file": DATA_DIR / "capture.db",
        "table": "vehicle_capture",
        "node": "Master (Laptop 1)"
    },
    "insurance": {
        "file": DATA_DIR / "insurance.db",
        "table": "insurance_records",
        "node": "Node A (Laptop 2)"
    },
    "registration": {
        "file": DATA_DIR / "registration.db",
        "table": "vehicle_registration",
        "node": "Node A (Laptop 2)"
    },
    "theft": {
        "file": DATA_DIR / "theft.db",
        "table": "vehicle_security_records",
        "node": "Node B (Laptop 3)"
    },
    "ministry": {
        "file": DATA_DIR / "ministry.db",
        "table": "transport_reports",
        "node": "Node B (Laptop 3)"
    }
}


def clean_all_databases():
    print("=" * 60)
    print("🧹 CLEANING ALL DATABASES ACROSS MASTER, NODE A, & NODE B")
    print("=" * 60)
    total_deleted = 0
    for name, info in DBS.items():
        db_path = info["file"]
        table = info["table"]
        if not db_path.exists():
            print(f"⚠️  {name} database does not exist at {db_path}")
            continue
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count_before = cur.fetchone()[0]
        cur.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        print(f"  ✓ {name:12} [{info['node']}]: Cleared {count_before} records from {table}")
        total_deleted += count_before
    print(f"\n✅ All databases are now CLEAN! Total rows deleted: {total_deleted}\n")


def seed_fresh_records():
    print("=" * 60)
    print("🌱 SEEDING PRISTINE TEST VEHICLES ACROSS DISTRIBUTED NODES")
    print("=" * 60)
    
    today = date.today().isoformat()
    past_1y = (date.today() - timedelta(days=365)).isoformat()
    future_1y = (date.today() + timedelta(days=365)).isoformat()
    expired = (date.today() - timedelta(days=30)).isoformat()

    # 1. NODE A: registration.db
    conn_reg = sqlite3.connect(DBS["registration"]["file"])
    cur_reg = conn_reg.cursor()
    reg_rows = [
        (1, "DL7CQ1939", "Rahul Sharma", "+91-98110-12345", "Pocket A, Sarita Vihar, South Delhi", past_1y, "Hyundai", "Creta 1.6 VTVT", "SUV / Private", "BLACK", "PETROL", "ENG-HYU-7719", "CHS-HYU-9921", 5, "ACTIVE", "DL-07 South West Delhi", future_1y, future_1y),
        (2, "MH20DV2366", "Amit Patel", "+91-98220-45678", "Aurangabad Cantonment, MH", past_1y, "Tata", "Nexon EV Max", "SUV / EV", "WHITE", "ELECTRIC", "ENG-TAT-8820", "CHS-TAT-4421", 5, "ACTIVE", "MH-20 Aurangabad", future_1y, future_1y),
        (3, "22BH6517A", "Col. Vikram Malhotra", "+91-99440-11223", "Defence Colony, New Delhi", past_1y, "Mahindra", "XUV700 AX7", "SUV / BH Series", "WHITE", "DIESEL", "ENG-MAH-1102", "CHS-MAH-3388", 7, "ACTIVE", "BH Series (Central RTO)", future_1y, future_1y),
        (4, "SN66XMZ", "John Davies", "+44-7700-900077", "Baker Street, London", past_1y, "Mercedes-Benz", "GLA 250 4MATIC", "Compact Luxury SUV", "SILVER", "PETROL", "ENG-MB-6601", "CHS-MB-9022", 5, "ACTIVE", "DVLA Swansea", future_1y, future_1y)
    ]
    cur_reg.executemany("""
        INSERT INTO vehicle_registration (
            reg_serial, vehicle_reg_no, owner_name, owner_contact, owner_address,
            registration_date, manufacturer, model_name, vehicle_class, registered_color,
            fuel_type, engine_number, chassis_number, seating_capacity,
            registration_status, rto_office, fitness_valid_until, tax_valid_until
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, reg_rows)
    conn_reg.commit()
    conn_reg.close()
    print("  ✓ Node A (registration.db): Inserted 4 vehicles (DL7CQ1939, MH20DV2366, 22BH6517A, SN66XMZ)")

    # 2. NODE A: insurance.db
    conn_ins = sqlite3.connect(DBS["insurance"]["file"])
    cur_ins = conn_ins.cursor()
    ins_rows = [
        (1, "DL7CQ1939", "HDFC ERGO General Insurance", "HDFC-COMP-778899", past_1y, future_1y, "ACTIVE", "Private Car", 14500.0, "Sunita Sharma", "Comprehensive", 0),
        (2, "MH20DV2366", "ICICI Lombard", "ICICI-EXP-334455", past_1y, expired, "EXPIRED", "Private EV", 11200.0, "Amit Patel", "Third Party", 1),
        (3, "22BH6517A", "Bajaj Allianz", "BAJAJ-BH-882211", past_1y, future_1y, "ACTIVE", "Private Car", 18500.0, "Anjali Malhotra", "Bumper-to-Bumper Zero Dep", 0),
        (4, "SN66XMZ", "Aviva UK Insurance", "AVIVA-INT-665544", past_1y, future_1y, "ACTIVE", "Luxury Car", 32000.0, "John Davies", "Comprehensive Overseas", 0)
    ]
    cur_ins.executemany("""
        INSERT INTO insurance_records (
            policy_id, registration_id, insurer_name, policy_number,
            policy_start_date, policy_expiry_date, insurance_status,
            vehicle_category, premium_amount, nominee_name, coverage_type, claim_count
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, ins_rows)
    conn_ins.commit()
    conn_ins.close()
    print("  ✓ Node A (insurance.db): Inserted 4 insurance policies (1 Active, 1 Expired, 2 Comprehensive)")

    # 3. NODE B: theft.db (MH20DV2366 is stolen!)
    conn_thf = sqlite3.connect(DBS["theft"]["file"])
    cur_thf = conn_thf.cursor()
    thf_rows = [
        (1, "MH20DV2366", "THEFT", "OPEN", today, None, "CR-2026/044", "FIR-992/2026", "Aurangabad City Police Station", None, "NOT_SCRAPPED", "Vehicle stolen from parking complex; Alert broadcasted", today)
    ]
    cur_thf.executemany("""
        INSERT INTO vehicle_security_records (
            case_id, vehicle_identifier, case_type, case_status, reported_date,
            recovery_date, police_reference, fir_number, police_station,
            shredding_certificate, shredding_status, remarks, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, thf_rows)
    conn_thf.commit()
    conn_thf.close()
    print("  ✓ Node B (theft.db): Inserted active theft case for MH20DV2366 (STOLEN)")

    # 4. NODE B: ministry.db
    conn_min = sqlite3.connect(DBS["ministry"]["file"])
    cur_min = conn_min.cursor()
    min_rows = [
        (1, "22BH6517A", "INTERSTATE_TRANSFER_NOTICE", today, "Central Armed Forces Interstate Relocation", "LOW", "RESOLVED", "Ministry of Road Transport & Highways", "Exempt from local state road taxes", today, "BH Series compliance verified")
    ]
    cur_min.executemany("""
        INSERT INTO transport_reports (
            report_id, vehicle_ref, report_type, report_date, reason,
            severity, report_status, submitted_by, action_taken, resolution_date, notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, min_rows)
    conn_min.commit()
    conn_min.close()
    print("  ✓ Node B (ministry.db): Inserted Ministry compliance report for 22BH6517A")

    # 5. MASTER: capture.db
    conn_cap = sqlite3.connect(DBS["capture"]["file"])
    cur_cap = conn_cap.cursor()
    cap_rows = [
        ("DL7CQ1939", "Car", "BLACK", today, "Sarita Vihar Checkpost, Delhi", "test_assets/assets/test0.9.jpeg", 0.96, 0.9078, "CAM-DEL-01", 1),
        ("MH20DV2366", "SUV", "WHITE", today, "Highway Toll Gate 4, Aurangabad", "test_assets/assets/test1.jpg", 0.98, 0.9927, "CAM-MH-02", 2),
        ("22BH6517A", "SUV", "WHITE", today, "Defence Colony Gate 2, Delhi", "test_assets/assets/test2.jpg", 0.97, 0.9677, "CAM-DEL-02", 1),
        ("SN66XMZ", "Car", "SILVER", today, "Airport Flyover Camera 3, London", "test_assets/assets/test0.4.jpg", 0.95, 0.9669, "CAM-LND-03", 1)
    ]
    cur_cap.executemany("""
        INSERT INTO vehicle_capture (
            plate_number, detected_vehicle_type, detected_color, capture_timestamp,
            capture_location, image_path, detection_confidence, ocr_confidence,
            camera_id, lane_number
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, cap_rows)
    conn_cap.commit()
    conn_cap.close()
    print("  ✓ Master (capture.db): Inserted 4 local vision camera captures")

    print("\n✅ SEEDING COMPLETE! All 4 test vehicles are populated with clear real-world states.")


def demo_crud():
    print("=" * 60)
    print("🔄 DEMONSTRATING DISTRIBUTED CRUD (INSERT -> UPDATE -> DELETE)")
    print("=" * 60)
    
    test_plate = "KA01AB9999"
    today = date.today().isoformat()
    future_1y = (date.today() + timedelta(days=365)).isoformat()
    
    # ── STEP 1: INSERT ON NODE A ──
    print(f"\n[1] INSERTING NEW CAR '{test_plate}' ON NODE A (registration.db)...")
    conn = sqlite3.connect(DBS["registration"]["file"])
    cur = conn.cursor()
    cur.execute("DELETE FROM vehicle_registration WHERE vehicle_reg_no = ?", (test_plate,))
    cur.execute("""
        INSERT INTO vehicle_registration (
            vehicle_reg_no, owner_name, owner_contact, manufacturer, model_name,
            registration_status, registration_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (test_plate, "Pooja Reddy", "+91-99887-11223", "Toyota", "Innova Hycross", "ACTIVE", today))
    conn.commit()
    conn.close()
    print(f"  ✓ Row inserted into Node A!")

    # Verify on Node A
    conn = sqlite3.connect(DBS["registration"]["file"])
    cur = conn.cursor()
    cur.execute("SELECT vehicle_reg_no, owner_name, manufacturer FROM vehicle_registration WHERE vehicle_reg_no = ?", (test_plate,))
    row = cur.fetchone()
    print(f"  ✓ Verified on Node A: {row}")
    conn.close()

    # ── STEP 2: UPDATE ON NODE B (Report car as Stolen) ──
    print(f"\n[2] UPDATING THEFT STATUS FOR '{test_plate}' ON NODE B (theft.db)...")
    conn = sqlite3.connect(DBS["theft"]["file"])
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO vehicle_security_records (
            case_id, vehicle_identifier, case_type, case_status, reported_date, remarks
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (99, test_plate, "THEFT", "OPEN", today, "Live Demo: Vehicle marked stolen during viva"))
    conn.commit()
    conn.close()
    print(f"  ✓ Theft alert logged into Node B!")

    # Verify on Node B
    conn = sqlite3.connect(DBS["theft"]["file"])
    cur = conn.cursor()
    cur.execute("SELECT vehicle_identifier, case_type, case_status, remarks FROM vehicle_security_records WHERE vehicle_identifier = ?", (test_plate,))
    row = cur.fetchone()
    print(f"  ✓ Verified on Node B: {row}")
    conn.close()

    # ── STEP 3: DELETE TEST RECORD CLEANUP ──
    print(f"\n[3] DELETING TEMPORARY TEST RECORD '{test_plate}' FROM NODE A & NODE B...")
    conn = sqlite3.connect(DBS["registration"]["file"])
    cur = conn.cursor()
    cur.execute("DELETE FROM vehicle_registration WHERE vehicle_reg_no = ?", (test_plate,))
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect(DBS["theft"]["file"])
    cur = conn.cursor()
    cur.execute("DELETE FROM vehicle_security_records WHERE vehicle_identifier = ?", (test_plate,))
    conn.commit()
    conn.close()
    print(f"  ✓ Test vehicle '{test_plate}' successfully deleted from Node A and Node B!")
    print("\n✅ CRUD DEMO FINISHED SUCCESSFULLY!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database manager for IIA vehicle project")
    parser.add_argument("--clean", action="store_true", help="Delete all rows from all 5 databases")
    parser.add_argument("--seed", action="store_true", help="Seed pristine test records")
    parser.add_argument("--demo-crud", action="store_true", help="Demonstrate live Insert/Update/Delete")
    args = parser.parse_args()

    if args.clean:
        clean_all_databases()
    elif args.seed:
        clean_all_databases()
        seed_fresh_records()
    elif args.demo_crud:
        demo_crud()
    else:
        print("Please provide --clean, --seed, or --demo-crud. See --help for details.")
