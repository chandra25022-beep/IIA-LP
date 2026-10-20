"""
Seed Databases Script

Populates all 5 independent SQLite databases with synthetic vehicle data.
Covers all 8 test scenarios from the project specification.

Run: python scripts/seed_databases.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from backend.app.sources import (
    CaptureSource, InsuranceSource, RegistrationSource, TheftSource, MinistrySource
)

# ─────────────────────────────────────────────────────────────────────────────
# Ensure data directory exists
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────
def fmt_date(d: date) -> str:
    return d.isoformat()

today = date.today()
past_2y = today - timedelta(days=730)
past_1y = today - timedelta(days=365)
past_6m = today - timedelta(days=180)
past_3m = today - timedelta(days=90)
past_1m = today - timedelta(days=30)
past_1w = today - timedelta(days=7)
future_1y = today + timedelta(days=365)
future_6m = today + timedelta(days=180)
past_expired = today - timedelta(days=30)   # expired 30 days ago


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1: VEHICLE CAPTURE (capture.db)
# Uses: plate_number  ← common value, different attribute name
# ─────────────────────────────────────────────────────────────────────────────
def seed_capture(source: CaptureSource):
    print("  Seeding Capture DB (plate_number)...")
    records = [
        # CASE 1: INSURED — UP32AB1234
        ("UP32AB1234", "Car", "WHITE", fmt_date(today - timedelta(hours=2)), "NH-24 Km 45, Ghaziabad", None, 0.97, 0.92, "CAM-001", 1),
        # CASE 2: EXPIRED — UP32CD5678
        ("UP32CD5678", "Car", "SILVER", fmt_date(today - timedelta(hours=5)), "Ring Road, Delhi", None, 0.95, 0.89, "CAM-002", 2),
        # CASE 3: UNINSURED — MH02EF9012
        ("MH02EF9012", "SUV", "BLACK", fmt_date(today - timedelta(hours=1)), "Western Express Hwy, Mumbai", None, 0.96, 0.91, "CAM-003", 1),
        # CASE 4: STOLEN — DL01GH3456
        ("DL01GH3456", "Motorcycle", "RED", fmt_date(today - timedelta(hours=3)), "Connaught Place, Delhi", None, 0.88, 0.85, "CAM-004", 3),
        # CASE 5: SCRAPPED — KA03IJ7890
        ("KA03IJ7890", "Truck", "BLUE", fmt_date(today - timedelta(days=2)), "Outer Ring Road, Bengaluru", None, 0.91, 0.87, "CAM-005", 2),
        # CASE 6: DATA CONFLICT (WHITE vs SILVER) — TN05KL1122
        ("TN05KL1122", "Car", "WHITE", fmt_date(today - timedelta(hours=4)), "Anna Salai, Chennai", None, 0.94, 0.90, "CAM-006", 1),
        # CASE 7: PARTIAL INFO (no insurance) — GJ06MN3344
        ("GJ06MN3344", "Car", "YELLOW", fmt_date(today - timedelta(hours=6)), "SG Highway, Ahmedabad", None, 0.93, 0.88, "CAM-007", 2),
        # CASE 8: FUZZY OCR MATCH — RJ07OP5566 (raw OCR might give RJ07OP556B)
        ("RJ07OP5566", "Car", "GREEN", fmt_date(today - timedelta(hours=8)), "Jaipur-Agra Highway", None, 0.89, 0.82, "CAM-008", 1),
        # CASE 9: SUSPICIOUS — HR26PQ7788
        ("HR26PQ7788", "Car", "BLACK", fmt_date(today - timedelta(hours=2)), "NH-1, Gurugram", None, 0.90, 0.86, "CAM-009", 1),
        # CASE 10: CANCELLED POLICY — PB10RS9900
        ("PB10RS9900", "Car", "SILVER", fmt_date(today - timedelta(hours=3)), "GT Road, Ludhiana", None, 0.92, 0.88, "CAM-010", 2),
        # Additional vehicles for dashboard numbers
        ("UP14TU2211", "Car", "WHITE", fmt_date(today - timedelta(hours=12)), "Agra-Lucknow Expressway", None, 0.96, 0.93, "CAM-011", 1),
        ("MH04VW3322", "Car", "RED", fmt_date(today - timedelta(hours=15)), "Pune Bypass", None, 0.94, 0.91, "CAM-012", 2),
        ("DL07XY4433", "SUV", "WHITE", fmt_date(today - timedelta(hours=20)), "Dwarka Expressway, Delhi", None, 0.97, 0.95, "CAM-013", 1),
        ("KA09ZA5544", "Car", "BLUE", fmt_date(today - timedelta(days=1)), "NICE Road, Bengaluru", None, 0.93, 0.90, "CAM-014", 3),
        ("TN07BC6655", "Truck", "WHITE", fmt_date(today - timedelta(days=1)), "OMR, Chennai", None, 0.88, 0.84, "CAM-015", 1),
        ("GJ01DE7766", "Car", "SILVER", fmt_date(today - timedelta(days=1)), "Expressway, Vadodara", None, 0.95, 0.92, "CAM-016", 2),
        ("RJ14FG8877", "Car", "RED", fmt_date(today - timedelta(days=2)), "NH-48, Jodhpur", None, 0.91, 0.87, "CAM-017", 1),
        ("HR29HI9988", "Car", "BLACK", fmt_date(today - timedelta(days=2)), "Sohna Road, Faridabad", None, 0.90, 0.85, "CAM-018", 2),
        ("PB08JK0011", "Motorcycle", "BLUE", fmt_date(today - timedelta(days=3)), "GT Road, Amritsar", None, 0.87, 0.83, "CAM-019", 1),
        ("MP09LM1122", "Car", "WHITE", fmt_date(today - timedelta(days=3)), "NH-46, Bhopal", None, 0.92, 0.89, "CAM-020", 2),
        # Additional captures for UP32AB1234 (multiple appearances)
        ("UP32AB1234", "Car", "WHITE", fmt_date(today - timedelta(days=1)), "NH-24 Km 50, Ghaziabad", None, 0.98, 0.94, "CAM-001", 2),
        ("UP32AB1234", "Car", "WHITE", fmt_date(today - timedelta(days=5)), "NH-24 Km 42, Ghaziabad", None, 0.96, 0.91, "CAM-002", 1),
        ("UP32CD5678", "Car", "SILVER", fmt_date(today - timedelta(days=2)), "Mathura Road, Delhi", None, 0.94, 0.88, "CAM-003", 1),
    ]

    source.execute_many(
        """INSERT OR IGNORE INTO vehicle_capture
           (plate_number, detected_vehicle_type, detected_color, capture_timestamp,
            capture_location, image_path, detection_confidence, ocr_confidence, camera_id, lane_number)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        records
    )
    print(f"    ✓ {len(records)} capture records seeded")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2: INSURANCE (insurance.db)
# Uses: registration_id  ← DIFFERENT attribute name for same value
# ─────────────────────────────────────────────────────────────────────────────
def seed_insurance(source: InsuranceSource):
    print("  Seeding Insurance DB (registration_id)...")
    records = [
        # CASE 1: ACTIVE insurance
        ("UP32AB1234", "National Insurance Co.", "NIC-2024-001234", fmt_date(past_1y), fmt_date(future_1y), "ACTIVE", "Private Car", 8500.00, "Ramesh Kumar", "COMPREHENSIVE", 0),
        # CASE 2: EXPIRED insurance
        ("UP32CD5678", "Oriental Insurance Co.", "OIC-2023-005678", fmt_date(past_2y), fmt_date(past_expired), "EXPIRED", "Private Car", 7200.00, "Sunita Sharma", "COMPREHENSIVE", 1),
        # CASE 3: No record for MH02EF9012 (UNINSURED)
        # CASE 4: Stolen — has insurance but still stolen
        ("DL01GH3456", "New India Assurance", "NIA-2024-003456", fmt_date(past_6m), fmt_date(future_6m), "ACTIVE", "Two Wheeler", 1500.00, "Mohit Singh", "THIRD_PARTY", 0),
        # CASE 5: Scrapped — no insurance needed
        # CASE 6: DATA CONFLICT — active insurance
        ("TN05KL1122", "United India Insurance", "UII-2024-001122", fmt_date(past_1y), fmt_date(future_6m), "ACTIVE", "Private Car", 9100.00, "Arjun Nair", "COMPREHENSIVE", 0),
        # CASE 7: PARTIAL INFO — no insurance (GJ06MN3344 not seeded here)
        # CASE 8: FUZZY MATCH demo — active insurance
        ("RJ07OP5566", "Bajaj Allianz", "BAJ-2024-005566", fmt_date(past_6m), fmt_date(future_1y), "ACTIVE", "Private Car", 11200.00, "Deepak Verma", "COMPREHENSIVE", 0),
        # CASE 9: SUSPICIOUS — cancelled insurance
        ("HR26PQ7788", "HDFC Ergo", "HDF-2023-007788", fmt_date(past_2y), fmt_date(past_1y), "CANCELLED", "Private Car", 8800.00, "Suresh Yadav", "COMPREHENSIVE", 0),
        # CASE 10: Expired/cancelled — PB10RS9900
        ("PB10RS9900", "IFFCO Tokio", "IFT-2023-009900", fmt_date(past_2y), fmt_date(past_expired), "EXPIRED", "Private Car", 7800.00, "Gurpreet Singh", "COMPREHENSIVE", 2),
        # Additional vehicles — all active insurance
        ("UP14TU2211", "National Insurance Co.", "NIC-2024-002211", fmt_date(past_6m), fmt_date(future_1y), "ACTIVE", "Private Car", 9200.00, "Anil Gupta", "COMPREHENSIVE", 0),
        ("MH04VW3322", "New India Assurance", "NIA-2024-003322", fmt_date(past_3m), fmt_date(future_1y), "ACTIVE", "Private Car", 12000.00, "Priya Desai", "COMPREHENSIVE", 0),
        ("DL07XY4433", "Oriental Insurance Co.", "OIC-2024-004433", fmt_date(past_6m), fmt_date(future_1y), "ACTIVE", "SUV", 15000.00, "Rahul Bhatia", "COMPREHENSIVE", 0),
        ("KA09ZA5544", "ICICI Lombard", "ICL-2024-005544", fmt_date(past_1m), fmt_date(future_1y), "ACTIVE", "Private Car", 10500.00, "Kavya Reddy", "COMPREHENSIVE", 0),
        ("TN07BC6655", "United India Insurance", "UII-2024-006655", fmt_date(past_6m), fmt_date(future_6m), "ACTIVE", "Goods Carrier", 25000.00, "Ravi Kumar", "COMPREHENSIVE", 0),
        ("GJ01DE7766", "Bajaj Allianz", "BAJ-2024-007766", fmt_date(past_3m), fmt_date(future_1y), "ACTIVE", "Private Car", 8900.00, "Hetal Shah", "COMPREHENSIVE", 0),
        ("RJ14FG8877", "HDFC Ergo", "HDF-2024-008877", fmt_date(past_1m), fmt_date(future_1y), "ACTIVE", "Private Car", 9800.00, "Ravi Sharma", "THIRD_PARTY", 0),
        ("MP09LM1122", "SBI General", "SBI-2024-009911", fmt_date(past_6m), fmt_date(future_1y), "ACTIVE", "Private Car", 7600.00, "Supriya Jain", "COMPREHENSIVE", 0),
        # Historical record for UP32CD5678
        ("UP32CD5678", "Oriental Insurance Co.", "OIC-2021-115678", fmt_date(past_2y - timedelta(days=365)), fmt_date(past_2y), "EXPIRED", "Private Car", 6800.00, "Sunita Sharma", "COMPREHENSIVE", 0),
    ]

    source.execute_many(
        """INSERT OR IGNORE INTO insurance_records
           (registration_id, insurer_name, policy_number, policy_start_date, policy_expiry_date,
            insurance_status, vehicle_category, premium_amount, nominee_name, coverage_type, claim_count)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        records
    )
    print(f"    ✓ {len(records)} insurance records seeded")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3: REGISTRATION (registration.db)
# Uses: vehicle_reg_no  ← DIFFERENT attribute name for same value
# ─────────────────────────────────────────────────────────────────────────────
def seed_registration(source: RegistrationSource):
    print("  Seeding Registration DB (vehicle_reg_no)...")
    records = [
        # vehicle_reg_no, owner, contact, address, reg_date, manufacturer, model, class, color, fuel, engine, chassis, seats, status, rto, fitness, tax
        ("UP32AB1234", "Ramesh Kumar", "9876543210", "14 MG Road, Lucknow, UP", fmt_date(past_2y), "Maruti Suzuki", "Swift", "LMV", "WHITE", "Petrol", "K12M1234567", "MA3EYD81S00345678", 5, "ACTIVE", "RTO-UP32-Lucknow", fmt_date(future_1y), fmt_date(future_1y)),
        ("UP32CD5678", "Sunita Sharma", "9876543211", "27 Civil Lines, Agra, UP", fmt_date(past_2y), "Hyundai", "i20", "LMV", "SILVER", "Petrol", "G4FA5678901", "MALAN51BLFM567890", 5, "ACTIVE", "RTO-UP32-Agra", fmt_date(future_1y), fmt_date(past_3m)),
        ("MH02EF9012", "Vijay Patil", "9876543212", "55 Andheri East, Mumbai, MH", fmt_date(past_1y), "Tata Motors", "Nexon", "LMV", "BLACK", "Diesel", "REVTRON9012345", "MAT609525N1234567", 5, "ACTIVE", "RTO-MH02-Mumbai", fmt_date(future_1y), fmt_date(future_6m)),
        ("DL01GH3456", "Mohit Singh", "9876543213", "8 Rohini Sector 3, Delhi", fmt_date(past_1y), "Honda", "CB Shine", "MCWG", "RED", "Petrol", "JC06ETHFA3456", "ME4JC06ATH3456789", 2, "ACTIVE", "RTO-DL01-Delhi", fmt_date(future_1y), fmt_date(future_6m)),
        ("KA03IJ7890", "Lakshmi Prasad", "9876543214", "12 Indiranagar, Bengaluru, KA", fmt_date(past_2y - timedelta(days=365)), "Eicher Motors", "Pro 1000", "HGV", "BLUE", "Diesel", "E483CRS7890123", "MB1PC3FS7H0123456", 3, "SUSPENDED", "RTO-KA03-Bengaluru", fmt_date(past_1y), fmt_date(past_1y)),
        ("TN05KL1122", "Arjun Nair", "9876543215", "7 Adyar, Chennai, TN", fmt_date(past_1y), "Volkswagen", "Polo", "LMV", "SILVER", "Petrol", "CHPA1122345", "WVWZZZ6RZHY112233", 5, "ACTIVE", "RTO-TN05-Chennai", fmt_date(future_1y), fmt_date(future_6m)),
        ("GJ06MN3344", "Hiren Patel", "9876543216", "23 Navrangpura, Ahmedabad, GJ", fmt_date(past_1y), "Mahindra", "XUV300", "LMV", "YELLOW", "Petrol", "mHAWK300G1234", "MA1ZG2KPJM1234567", 5, "ACTIVE", "RTO-GJ06-Ahmedabad", fmt_date(future_1y), fmt_date(future_1y)),
        ("RJ07OP5566", "Deepak Verma", "9876543217", "31 Tonk Road, Jaipur, RJ", fmt_date(past_6m), "Maruti Suzuki", "Dzire", "LMV", "GREEN", "CNG", "K12M5566789", "MA3EYEFAS00556677", 5, "ACTIVE", "RTO-RJ07-Jaipur", fmt_date(future_1y), fmt_date(future_1y)),
        ("HR26PQ7788", "Suresh Yadav", "9876543218", "45 DLF Phase 2, Gurugram, HR", fmt_date(past_2y), "Toyota", "Innova", "LMV", "BLACK", "Diesel", "2KD7788901", "MBJFB8BT900778899", 8, "ACTIVE", "RTO-HR26-Gurugram", fmt_date(future_1y), fmt_date(future_6m)),
        ("PB10RS9900", "Gurpreet Singh", "9876543219", "18 Model Town, Ludhiana, PB", fmt_date(past_1y), "Hyundai", "Verna", "LMV", "SILVER", "Petrol", "G4GC9900123", "MALAN51CLFM990011", 5, "ACTIVE", "RTO-PB10-Ludhiana", fmt_date(future_6m), fmt_date(past_3m)),
        ("UP14TU2211", "Anil Gupta", "9876543220", "12 Hazratganj, Lucknow, UP", fmt_date(past_1y), "Honda", "City", "LMV", "WHITE", "Petrol", "L15B2211345", "MRHGM285XFP221133", 5, "ACTIVE", "RTO-UP14-Lucknow", fmt_date(future_1y), fmt_date(future_1y)),
        ("MH04VW3322", "Priya Desai", "9876543221", "56 Kothrud, Pune, MH", fmt_date(past_6m), "Kia", "Seltos", "LMV", "RED", "Petrol", "G4FG3322456", "KNAB151EBMP332244", 5, "ACTIVE", "RTO-MH04-Pune", fmt_date(future_1y), fmt_date(future_1y)),
        ("DL07XY4433", "Rahul Bhatia", "9876543222", "9 Saket, Delhi", fmt_date(past_6m), "MG Motor", "Hector", "LMV", "WHITE", "Diesel", "D18DTH4433567", "SAHEXXXX3XG443355", 5, "ACTIVE", "RTO-DL07-Delhi", fmt_date(future_1y), fmt_date(future_1y)),
        ("KA09ZA5544", "Kavya Reddy", "9876543223", "88 JP Nagar, Bengaluru, KA", fmt_date(past_3m), "Maruti Suzuki", "Baleno", "LMV", "BLUE", "Petrol", "K12M5544678", "MA3EWDE1S00554466", 5, "ACTIVE", "RTO-KA09-Bengaluru", fmt_date(future_1y), fmt_date(future_1y)),
        ("TN07BC6655", "Ravi Kumar", "9876543224", "71 Ambattur, Chennai, TN", fmt_date(past_1y), "Ashok Leyland", "Dost", "MGV", "WHITE", "Diesel", "4D34T6655789", "MAT7BH4NXNM665566", 3, "ACTIVE", "RTO-TN07-Chennai", fmt_date(future_6m), fmt_date(future_6m)),
        ("GJ01DE7766", "Hetal Shah", "9876543225", "34 Paldi, Ahmedabad, GJ", fmt_date(past_6m), "Ford", "EcoSport", "LMV", "SILVER", "Petrol", "DRAGON7766890", "MAJGXXMRKJEE77667", 5, "ACTIVE", "RTO-GJ01-Ahmedabad", fmt_date(future_1y), fmt_date(future_1y)),
        ("RJ14FG8877", "Ravi Sharma", "9876543226", "22 Bhatta Basti, Jodhpur, RJ", fmt_date(past_3m), "Maruti Suzuki", "WagonR", "LMV", "RED", "CNG", "K10C8877901", "MA3FKEB1S00887788", 5, "ACTIVE", "RTO-RJ14-Jodhpur", fmt_date(future_1y), fmt_date(future_1y)),
        ("HR29HI9988", "Neha Arora", "9876543227", "67 Sector 14, Faridabad, HR", fmt_date(past_6m), "Renault", "Kwid", "LMV", "BLACK", "Petrol", "BR10DE9988012", "VF1BA0B0H56998899", 5, "ACTIVE", "RTO-HR29-Faridabad", fmt_date(future_1y), fmt_date(future_6m)),
        ("PB08JK0011", "Manpreet Kaur", "9876543228", "55 Ranjit Avenue, Amritsar, PB", fmt_date(past_1y), "Hero MotoCorp", "Splendor", "MCWG", "BLUE", "Petrol", "HC15EA0011234", "MBLHA10AXG0001122", 2, "ACTIVE", "RTO-PB08-Amritsar", fmt_date(future_6m), fmt_date(future_6m)),
        ("MP09LM1122", "Supriya Jain", "9876543229", "78 Tulsi Nagar, Bhopal, MP", fmt_date(past_6m), "Tata Motors", "Tiago", "LMV", "WHITE", "Petrol", "REVOTRON1122345", "MAT625636N1122334", 5, "ACTIVE", "RTO-MP09-Bhopal", fmt_date(future_1y), fmt_date(future_1y)),
    ]

    source.execute_many(
        """INSERT OR IGNORE INTO vehicle_registration
           (vehicle_reg_no, owner_name, owner_contact, owner_address, registration_date,
            manufacturer, model_name, vehicle_class, registered_color, fuel_type,
            engine_number, chassis_number, seating_capacity, registration_status,
            rto_office, fitness_valid_until, tax_valid_until)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        records
    )
    print(f"    ✓ {len(records)} registration records seeded")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 4: THEFT/SECURITY (theft.db)
# Uses: vehicle_identifier  ← DIFFERENT attribute name for same value
# ─────────────────────────────────────────────────────────────────────────────
def seed_theft(source: TheftSource):
    print("  Seeding Theft DB (vehicle_identifier)...")
    records = [
        # CASE 4: STOLEN — DL01GH3456
        ("DL01GH3456", "STOLEN", "OPEN", fmt_date(past_1m), None, "PS-ROHINI-2024-1234", "FIR/2024/ROH/12345", "Rohini Police Station", None, "NOT_SCRAPPED", "Reported stolen from parking. No witnesses.", fmt_date(past_1m)),
        # CASE 5: SCRAPPED — KA03IJ7890
        ("KA03IJ7890", "SCRAPPED", "CLOSED", fmt_date(past_6m), fmt_date(past_3m), "SCRAP-KA-2024-0789", None, None, "SCRAP-KA-2024-0789-CERT", "SCRAPPED", "Vehicle declared end-of-life and sent to authorized scrapping facility.", fmt_date(past_3m)),
        # CASE 9: SUSPICIOUS — HR26PQ7788
        ("HR26PQ7788", "SUSPICIOUS", "OPEN", fmt_date(past_1w), None, "PS-GGN-2024-5678", "FIR/2024/GGN/56789", "Gurugram Traffic Police", None, "NOT_SCRAPPED", "Vehicle flagged for suspicious movement patterns near border checkpoints.", fmt_date(past_1w)),
        # Additional security records
        ("UP32AB1234", "RECOVERED", "CLOSED", fmt_date(past_2y), fmt_date(past_2y + timedelta(days=5)), "PS-LKO-2022-0001", "FIR/2022/LKO/00001", "Lucknow Hazratganj PS", None, "NOT_SCRAPPED", "Vehicle was reported stolen 2 years ago but recovered within 5 days.", fmt_date(past_2y + timedelta(days=5))),
    ]

    source.execute_many(
        """INSERT OR IGNORE INTO vehicle_security_records
           (vehicle_identifier, case_type, case_status, reported_date, recovery_date,
            police_reference, fir_number, police_station, shredding_certificate,
            shredding_status, remarks, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        records
    )
    print(f"    ✓ {len(records)} theft/security records seeded")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 5: MINISTRY (ministry.db)
# Uses: vehicle_ref  ← DIFFERENT attribute name for same value
# ─────────────────────────────────────────────────────────────────────────────
def seed_ministry(source: MinistrySource):
    print("  Seeding Ministry DB (vehicle_ref)...")
    records = [
        # Pre-existing reports
        ("UP32CD5678", "EXPIRED_INSURANCE", fmt_date(past_1m), "Insurance expired on " + fmt_date(past_expired) + ". Vehicle found on road.", "HIGH", "PENDING", "SYSTEM", None, None, None),
        ("MH02EF9012", "UNINSURED_VEHICLE", fmt_date(past_1m), "No insurance record found for vehicle.", "HIGH", "PENDING", "SYSTEM", None, None, None),
        ("DL01GH3456", "STOLEN_VEHICLE", fmt_date(past_1m), "Vehicle reported stolen. FIR: FIR/2024/ROH/12345", "CRITICAL", "ACTIONED", "SYSTEM", "Alert issued to all checkposts", None, None),
        ("KA03IJ7890", "SUSPICIOUS_VEHICLE", fmt_date(past_3m), "Scrapped vehicle found on road. Shredding certificate verified.", "HIGH", "RESOLVED", "SYSTEM", "Vehicle impounded", fmt_date(past_3m), None),
        ("HR26PQ7788", "SUSPICIOUS_VEHICLE", fmt_date(past_1w), "Vehicle flagged as suspicious by traffic surveillance AI.", "MEDIUM", "PENDING", "SYSTEM", None, None, None),
        ("PB10RS9900", "EXPIRED_INSURANCE", fmt_date(past_3m), "Insurance policy expired 3 months ago. Vehicle still operating.", "HIGH", "RESOLVED", "SYSTEM", "Fine issued, owner notified", fmt_date(past_3m - timedelta(days=5)), None),
        ("TN05KL1122", "REGISTRATION_MISMATCH", fmt_date(past_2y + timedelta(days=10)), "Detected color WHITE does not match registered color SILVER.", "MEDIUM", "RESOLVED", "SYSTEM", "Owner verified — vehicle repainted, records updated", fmt_date(past_2y + timedelta(days=30)), None),
    ]

    source.execute_many(
        """INSERT OR IGNORE INTO transport_reports
           (vehicle_ref, report_type, report_date, reason, severity, report_status,
            submitted_by, action_taken, resolution_date, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        records
    )
    print(f"    ✓ {len(records)} ministry reports seeded")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("IIA Vehicle Integration System — Database Seeding")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print()

    # Initialize all sources (creates DBs if not exist)
    print("Initializing database schemas...")
    capture = CaptureSource()
    insurance = InsuranceSource()
    registration = RegistrationSource()
    theft = TheftSource()
    ministry = MinistrySource()
    print("  ✓ All 5 database schemas initialized")
    print()

    # Seed each source
    print("Seeding data sources with synthetic vehicle data...")
    seed_capture(capture)
    seed_insurance(insurance)
    seed_registration(registration)
    seed_theft(theft)
    seed_ministry(ministry)

    print()
    print("=" * 60)
    print("✓ All 5 databases seeded successfully!")
    print()
    print("Demo vehicles available:")
    demo_cases = [
        ("UP32AB1234", "CASE 1 — INSURED"),
        ("UP32CD5678", "CASE 2 — INSURANCE EXPIRED"),
        ("MH02EF9012", "CASE 3 — UNINSURED"),
        ("DL01GH3456", "CASE 4 — STOLEN"),
        ("KA03IJ7890", "CASE 5 — SCRAPPED"),
        ("TN05KL1122", "CASE 6 — DATA CONFLICT (color mismatch)"),
        ("GJ06MN3344", "CASE 7 — PARTIAL INFO (no insurance)"),
        ("RJ07OP5566", "CASE 8 — FUZZY OCR MATCH"),
        ("HR26PQ7788", "CASE 9 — SUSPICIOUS"),
        ("PB10RS9900", "CASE 10 — CANCELLED POLICY"),
    ]
    for plate, description in demo_cases:
        print(f"  {plate}  →  {description}")
    print("=" * 60)
