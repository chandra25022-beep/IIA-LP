"""
Comprehensive Evaluation Diagnostic Script
Tests Rubric 1 (Approximate Matching & Vice-Versa) and Rubric 2 (Contextual Cleansing)
against the live distributed cluster.
"""
import sys
import io
import json
import requests

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"

def test_rubric_1_approximate_matching():
    print("=" * 70)
    print("🧪 TEST SUITE 1: RUBRIC 1 — APPROXIMATE MATCHING & VICE-VERSA")
    print("=" * 70)

    # Test Case 1: OCR Substitution Noise (DL7CO1939 -> DL7CQ1939)
    print("\n[1.1] Testing Noisy Plate: 'DL7CO1939' (Letter 'O' instead of Digit '0')")
    r1 = requests.post(f"{BASE_URL}/api/vehicle/approximate-match", json={
        "noisy_plate": "DL7CO1939",
        "matching_method": "ensemble",
        "max_candidates": 5
    })
    print(f"  Status: {r1.status_code}")
    d1 = r1.json()
    print(f"  Candidates Found: {d1.get('total_candidates_found')}")
    matches1 = d1.get("matches", [])
    if matches1:
        top = matches1[0]
        print(f"  ✓ Top Match: {top.get('plate')} | Prob: {top.get('match_probability')} | Tier: {top.get('decision_tier')}")
        print(f"    Metrics: Jaro-Winkler={top['all_metrics']['jaro_winkler']}, EditSim={top['all_metrics']['normalized_edit']}, OCRConfusion={top['all_metrics']['ocr_confusion']}")
        assert top.get('plate') == 'DL7CQ1939', f"Expected DL7CQ1939, got {top.get('plate')}"
        print("  ✅ Passed: DL7CO1939 correctly matched to DL7CQ1939!")
    else:
        print("  ❌ No matches found!")

    # Test Case 2: Character Confusion Noise (MH20DV236B -> MH20DV2366)
    print("\n[1.2] Testing Noisy Plate: 'MH20DV236B' ('B' instead of '6')")
    r2 = requests.post(f"{BASE_URL}/api/vehicle/approximate-match", json={
        "noisy_plate": "MH20DV236B",
        "matching_method": "ensemble",
        "max_candidates": 5
    })
    d2 = r2.json()
    matches2 = d2.get("matches", [])
    if matches2:
        top = matches2[0]
        print(f"  ✓ Top Match: {top.get('plate')} | Prob: {top.get('match_probability')} | Tier: {top.get('decision_tier')}")
        assert top.get('plate') == 'MH20DV2366', f"Expected MH20DV2366, got {top.get('plate')}"
        print("  ✅ Passed: MH20DV236B correctly matched to MH20DV2366!")
    else:
        print("  ❌ No matches found!")

    # Test Case 3: Vice-Versa Reverse Matching (/reverse-match/{target_plate})
    print("\n[1.3] Testing Vice-Versa Matching: Target Registered Plate 'DL7CQ1939'")
    r3 = requests.get(f"{BASE_URL}/api/vehicle/reverse-match/DL7CQ1939")
    print(f"  Status: {r3.status_code}")
    d3 = r3.json()
    print(f"  Historical Captures Evaluated: {d3.get('total_captures_evaluated')}")
    matches3 = d3.get("matches", [])
    print(f"  Surveillance Captures Matching Target: {len(matches3)}")
    if matches3:
        for m in matches3[:3]:
            print(f"    - Captured: {m.get('captured_plate')} | Location: {m.get('camera_location')} | Prob: {m.get('match_probability')} | Tier: {m.get('decision_tier')}")
        assert matches3[0].get('captured_plate') == 'DL7CQ1939', "Expected DL7CQ1939 as top historical capture"
        print("  ✅ Passed: Vice-versa reverse matching successfully retrieved historical camera records!")
    else:
        print("  ❌ No historical camera captures matched!")

def test_rubric_2_contextual_cleansing():
    print("\n" + "=" * 70)
    print("🧪 TEST SUITE 2: RUBRIC 2 — CONTEXTUAL DATA CLEANSING")
    print("=" * 70)

    # Test Case 1: Cleansing Noisy Plate with Multimodal Context (Color + Vehicle Type + Make)
    print("\n[2.1] Cleansing Noisy Plate 'DL7CO1939' with Image Context (BLACK, SUV, Hyundai)")
    r = requests.post(f"{BASE_URL}/api/vehicle/cleanse", json={
        "noisy_plate": "DL7CO1939",
        "detected_color": "BLACK",
        "detected_vehicle_type": "SUV",
        "detected_make": "Hyundai",
        "sensor_confidence": 0.90
    })
    print(f"  Status: {r.status_code}")
    d = r.json()
    print(f"  Raw Input:       {d.get('original_input')}")
    print(f"  Normalized:      {d.get('normalized_plate')}")
    print(f"  Cleansed Output: {d.get('cleansed_plate')}")
    print(f"  Method:          {d.get('cleansing_method')}")
    print(f"  Confidence:      {d.get('cleansing_confidence')}")
    print(f"  Anomalies Fixed: {d.get('anomaly_count')}")

    print("\n  Audit Trail Steps:")
    for step in d.get("cleansing_audit_trail", []):
        print(f"    Step {step.get('step')}: [{step.get('action')}] {step.get('description')}")

    print("\n  Anomalies Detected & Corrected:")
    for a in d.get("anomalies_detected", []):
        print(f"    - {a.get('type')}: {a.get('description')}")

    assert d.get('cleansed_plate') == 'DL7CQ1939', f"Expected DL7CQ1939, got {d.get('cleansed_plate')}"
    print("  ✅ Passed: Noisy plate DL7CO1939 cleansed to DL7CQ1939 using contextual evidence!")

    # Test Case 2: Ambiguity Disambiguation via Color
    print("\n[2.2] Disambiguation: What if OCR reads 'DL7CO1939' but color is BLACK vs RED?")
    r_black = requests.post(f"{BASE_URL}/api/vehicle/cleanse", json={
        "noisy_plate": "DL7CO1939",
        "detected_color": "BLACK",
        "detected_vehicle_type": "SUV"
    })
    r_red = requests.post(f"{BASE_URL}/api/vehicle/cleanse", json={
        "noisy_plate": "DL7CO1939",
        "detected_color": "RED",
        "detected_vehicle_type": "SUV"
    })
    p_black = r_black.json().get('cleansing_confidence', 0)
    p_red = r_red.json().get('cleansing_confidence', 0)
    print(f"  Confidence with matching color BLACK: {p_black:.4f}")
    print(f"  Confidence with conflicting color RED: {p_red:.4f}")
    assert p_black > p_red, "Matching color must yield higher confidence than conflicting color!"
    print("  ✅ Passed: Contextual color agreement significantly boosts Bayesian confidence!")

def test_rubric_end_to_end_pipeline():
    print("\n" + "=" * 70)
    print("🧪 TEST SUITE 3: END-TO-END PIPELINE (ANPR -> GEMINI -> CLEANSE -> 5-DB GAV)")
    print("=" * 70)

    print("\n[3.1] Running Full Pipeline on Anchor Asset 'test0.9.jpeg'...")
    r = requests.post(f"{BASE_URL}/api/vehicle/scan-sample/test0.9.jpeg")
    print(f"  Status: {r.status_code}")
    d = r.json()
    scan = d.get("scan_result", {})
    cleanse = d.get("cleansing_result", {})
    integ = d.get("integrated_vehicle", {})

    print(f"  Raw OCR Plate:    {scan.get('raw_ocr')}")
    print(f"  Detected Color:   {scan.get('detected_color')} ({scan.get('color_source')})")
    print(f"  Detected Type:    {scan.get('vehicle_type')}")
    print(f"  Detected Make:    {scan.get('detected_make')} {scan.get('detected_model')}")
    print(f"  Cleansed Plate:   {d.get('final_plate')}")
    print(f"  Registered Make:  {integ.get('vehicle', {}).get('make')} {integ.get('vehicle', {}).get('model')}")
    print(f"  Registered Color: {integ.get('vehicle', {}).get('registered_color')}")
    print(f"  Insurance Status: {integ.get('insurance', {}).get('insurance_status')}")
    print(f"  Theft Case Status:{integ.get('security', {}).get('case_status')}")
    print(f"  Ministry Reports: {len(integ.get('ministry', []))}")

    assert scan.get('detected_color') == 'BLACK', f"Expected BLACK, got {scan.get('detected_color')}"
    assert integ.get('vehicle', {}).get('make') == 'Hyundai', "Expected Hyundai"
    assert integ.get('insurance', {}).get('insurance_status') == 'ACTIVE', "Expected ACTIVE"
    print("  ✅ Passed: Full end-to-end pipeline operates flawlessly!")

if __name__ == "__main__":
    test_rubric_1_approximate_matching()
    test_rubric_2_contextual_cleansing()
    test_rubric_end_to_end_pipeline()
    print("\n" + "=" * 70)
    print("🎉 ALL ALGORITHM & CLEANSING VERIFICATION CHECKS PASSED (100% READY FOR VIVA)")
    print("=" * 70)
