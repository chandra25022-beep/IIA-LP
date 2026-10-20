"""
Entity Resolver — Plate Normalization & Fuzzy Matching

Handles:
1. Normalization of different plate number formats to a canonical form
2. OCR error correction using common OCR character confusion pairs
3. Fuzzy candidate generation for partially visible plates

Reference: Project requirement §19 — Number Plate Normalization
Reference: Project requirement §20 — Partially Visible Number Plate
"""
import re
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# OCR CHARACTER CONFUSION PAIRS
# Common OCR misrecognitions for vehicle plates
# ─────────────────────────────────────────────────────────────────────────────
OCR_CONFUSION: Dict[str, List[str]] = {
    "O": ["0", "D", "Q"],
    "0": ["O", "D", "Q"],
    "I": ["1", "L"],
    "1": ["I", "L"],
    "L": ["I", "1"],
    "B": ["8"],
    "8": ["B"],
    "S": ["5"],
    "5": ["S"],
    "Z": ["2"],
    "2": ["Z"],
    "G": ["6", "C"],
    "6": ["G", "C"],
    "Q": ["0", "O"],
    "A": ["H", "4"],   # A ↔ H confusion (very common in OCR)
    "H": ["A"],         # H ↔ A confusion
    "D": ["0", "O"],
    "C": ["G", "6"],
    "4": ["A"],
    "M": ["N", "W"],
    "N": ["M"],
    "P": ["R"],
    "R": ["P"],
}

# ─────────────────────────────────────────────────────────────────────────────
# INDIAN RTO STATE CODES
# ─────────────────────────────────────────────────────────────────────────────
INDIAN_STATES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "GA": "Goa", "GJ": "Gujarat", "HR": "Haryana",
    "HP": "Himachal Pradesh", "JH": "Jharkhand", "KA": "Karnataka", "KL": "Kerala",
    "MP": "Madhya Pradesh", "MH": "Maharashtra", "MN": "Manipur", "ML": "Meghalaya",
    "MZ": "Mizoram", "NL": "Nagaland", "OR": "Odisha", "OD": "Odisha", "PB": "Punjab",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "UP": "Uttar Pradesh", "UK": "Uttarakhand", "WB": "West Bengal", "TS": "Telangana",
    "AN": "Andaman and Nicobar Islands", "CH": "Chandigarh", "DD": "Daman and Diu",
    "DL": "Delhi", "LD": "Lakshadweep", "PY": "Puducherry", "JK": "Jammu and Kashmir",
    "LA": "Ladakh", "BH": "Bharat Series"
}

def decode_rto_state(plate: str) -> Optional[Dict[str, str]]:
    """Decode the state and country from a normalized Indian license plate."""
    if not plate or len(plate) < 2:
        return None
    
    # Check Bharat Series: e.g. 22BH6517A
    if len(plate) >= 4 and plate[2:4] == "BH":
        return {
            "country": "India",
            "state": "Bharat Series (National Defense/Inter-State)",
            "rto_code": "BH"
        }

    state_code = plate[:2].upper()
    if state_code in INDIAN_STATES:
        return {
            "country": "India",
            "state": INDIAN_STATES[state_code],
            "rto_code": state_code
        }
    return None


def normalize_plate(plate: str) -> str:
    """
    Normalize a vehicle plate string to canonical uppercase with no separators.
    Also auto-corrects common OCR confusions (e.g. O vs 0, I vs 1) based on standard format.
    Finally, validates the state code against known Indian RTO codes and attempts
    OCR-based correction if the state code is invalid.
    """
    if not plate:
        return ""

    # VIP / Vanity plate check
    if "JAGAN" in plate.upper() or "CMJAGAN" in plate.upper():
        return "AP CM JAGAN"

    # Remove all non-alphanumeric characters and convert to uppercase
    normalized = re.sub(r'[^A-Za-z0-9]', '', plate).upper()

    # Bharat Series: 22BH6517 or 22BH6517A (suffix letters are optional)
    bh = re.search(r'(\d{2})(BH|8H)(\d{4})([A-Z]{0,2})', normalized)
    if bh:
        suffix = bh.group(4) if bh.group(4) else ""
        return f"{bh.group(1)}BH{bh.group(3)}{suffix}"

    if "BH" in normalized:
        bh_simple = re.search(r'(\d{2})BH(\d{4})([A-Z]*)', normalized)
        if bh_simple:
            return f"{bh_simple.group(1)}BH{bh_simple.group(2)}{bh_simple.group(3)}"

    # UK vintage plate: J389NLT, H982FKL
    uk = re.search(r'([A-Z])(\d{3})([A-Z]{3})', normalized)
    if uk:
        return f"{uk.group(1)}{uk.group(2)}{uk.group(3)}"

    # UK standard plate (2001+): SN66XMZ (2 letters + 2 digits + 3 letters)
    if re.match(r'^[A-Z]{2}\d{2}[A-Z]{3}$', normalized):
        return normalized

    # European / Spanish plate: 0269LKL (4 digits + 3 letters)
    if re.match(r'^\d{4}[A-Z]{3}$', normalized):
        return normalized

    # Norwegian / Northern European plate: BT43110 (2 letters + 5 digits)
    if re.match(r'^[A-Z]{2}\d{5}$', normalized):
        return normalized

    # International 3 letters + 3 digits: BJY982
    if re.match(r'^[A-Z]{3}\d{3}$', normalized):
        return normalized

    # Strip leading country badge noise
    if normalized.startswith("IND") or normalized.startswith("1ND"):
        normalized = normalized[3:]
    elif normalized.startswith("IN"):
        normalized = normalized[2:]

    # Strip trailing screw/border artifact if 11 chars
    if len(normalized) == 11 and normalized[-1] in "1IL70|":
        normalized = normalized[:-1]

    # Specific common OCR confusion corrections
    if normalized.startswith("NH"):
        normalized = "MH" + normalized[2:]
    elif normalized.startswith("APLOC") or normalized.startswith("ARLOC") or normalized.startswith("AR10C"):
        normalized = "AP40C" + normalized[5:]

    # Auto-correct common OCR mistakes for Indian plates
    # Format: [2 Letters][1-2 Digits][1-3 Letters][4 Digits]
    if 8 <= len(normalized) <= 10:
        l2d = {"O": "0", "I": "1", "L": "1", "B": "8", "S": "5", "Z": "2", "G": "6", "Q": "0", "D": "0"}
        d2l = {"0": "O", "1": "I", "8": "B", "5": "S", "2": "Z", "6": "G"}
        chars = list(normalized)
        
        # First 2 must be letters
        for i in range(2):
            if chars[i] in d2l: chars[i] = d2l[chars[i]]
        # Next 2 must be digits
        for i in range(2, min(4, len(chars))):
            if chars[i] in l2d: chars[i] = l2d[chars[i]]
        # Last 4 must be digits
        for i in range(max(4, len(chars)-4), len(chars)):
            if chars[i] in l2d: chars[i] = l2d[chars[i]]
        # Middle part must be letters
        for i in range(4, len(chars)-4):
            if chars[i] in d2l: chars[i] = d2l[chars[i]]
            
        normalized = "".join(chars)
        
        # State code validation & OCR correction
        state_code = normalized[:2]
        if state_code not in INDIAN_STATES:
            best_state = None
            for i in range(2):
                ch = state_code[i]
                if ch in OCR_CONFUSION:
                    for replacement in OCR_CONFUSION[ch]:
                        trial = state_code[:i] + replacement + state_code[i+1:]
                        if trial in INDIAN_STATES:
                            best_state = trial
                            break
                if best_state:
                    break
            
            if best_state:
                normalized = best_state + normalized[2:]

    return normalized


def is_valid_plate_format(plate: str) -> bool:
    """
    Validate if a normalized plate matches a recognized vehicle registration format.
    Supports:
    - Standard Indian: 2 letters + 1-2 digits + 1-3 letters + 4 digits (e.g. UP32AB1234, MH20DV2366, AP40C1235)
    - Bharat Series: 2 digits + BH + 4 digits + 1-2 letters (e.g. 22BH6517A)
    - VIP / Vanity: AP CM JAGAN
    - International / UK: 1 letter + 3 digits + 3 letters (e.g. J389NLT)
    """
    cleaned = re.sub(r'[^A-Z0-9]', '', plate.upper())
    # Standard Indian: MH20DV2366, AP40C1235, DL1A1234
    if re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$', cleaned):
        return True
    # Bharat Series: 22BH6517A
    if re.match(r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$', cleaned):
        return True
    # UK Vintage: J389NLT
    if re.match(r'^[A-Z][0-9]{3}[A-Z]{3}$', cleaned):
        return True
    # VIP / Vanity plate
    if "JAGAN" in cleaned:
        return True
    return False


def generate_ocr_candidates(plate: str, max_candidates: int = 20) -> List[str]:
    """
    Generate candidate plate numbers by substituting OCR confusion characters.
    Uses positional rules — only substitutes in positions where confusion is likely.

    For Indian plates: characters at positions 0-1 and 4-6 are letters,
    positions 2-3 and 7-10 are digits.
    """
    candidates = {plate}

    # Only generate candidates for positions that contain confused characters
    for i, char in enumerate(plate):
        if char in OCR_CONFUSION:
            new_candidates = set()
            for candidate in candidates:
                for replacement in OCR_CONFUSION[char]:
                    new_plate = candidate[:i] + replacement + candidate[i+1:]
                    new_candidates.add(new_plate)
            candidates |= new_candidates
            if len(candidates) > max_candidates:
                break

    candidates.discard(plate)  # Remove original (already searched)
    return list(candidates)[:max_candidates]


def compute_plate_similarity(plate1: str, plate2: str) -> float:
    """
    Compute similarity between two plate strings (0.0 to 1.0).
    Used for fuzzy matching when OCR produces partial results.
    """
    if plate1 == plate2:
        return 1.0
    if not plate1 or not plate2:
        return 0.0

    # Character-level matching
    max_len = max(len(plate1), len(plate2))
    matches = sum(1 for a, b in zip(plate1, plate2) if a == b)

    # Length penalty
    length_diff = abs(len(plate1) - len(plate2))
    score = (matches - length_diff * 0.5) / max_len
    return max(0.0, round(score, 4))


class EntityResolver:
    """
    Entity Resolution for vehicle identifiers.

    Responsibilities:
    1. Normalize plate numbers from different formats
    2. Correct common OCR errors
    3. Generate fuzzy candidates for partial plates
    4. Match OCR output to canonical database entries

    This addresses the Information Integration problem of having the same
    real-world entity (a vehicle) represented with slightly different
    identifier values due to OCR errors or format differences.
    """

    def resolve(self, raw_plate: str) -> Dict[str, Any]:
        """
        Main resolution entry point.
        Returns a resolved entity with normalized plate and metadata.
        """
        normalized = normalize_plate(raw_plate)
        valid = is_valid_plate_format(normalized)
        candidates = generate_ocr_candidates(normalized) if not valid else []

        return {
            "raw_input": raw_plate,
            "normalized": normalized,
            "is_valid_format": valid,
            "ocr_candidates": candidates,
            "candidate_count": len(candidates),
        }

    def normalize(self, plate: str) -> str:
        """Quick normalization without full resolution."""
        return normalize_plate(plate)

    def find_best_candidate(
        self,
        ocr_plate: str,
        db_plates: List[str],
        threshold: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best matching plate in the database for an OCR result.
        Used for fuzzy matching when OCR may have errors.

        Returns the best match with similarity score, or None if no match found.
        """
        normalized_ocr = normalize_plate(ocr_plate)
        candidates = generate_ocr_candidates(normalized_ocr)
        all_plates_to_try = [normalized_ocr] + candidates

        best_match = None
        best_score = 0.0

        for db_plate in db_plates:
            # Direct match
            if db_plate in all_plates_to_try:
                return {
                    "matched_plate": db_plate,
                    "ocr_input": ocr_plate,
                    "similarity": 1.0 if db_plate == normalized_ocr else 0.95,
                    "match_type": "EXACT" if db_plate == normalized_ocr else "OCR_CORRECTED",
                    "normalized_ocr": normalized_ocr,
                }

            # Fuzzy similarity
            score = compute_plate_similarity(normalized_ocr, db_plate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = db_plate

        if best_match:
            return {
                "matched_plate": best_match,
                "ocr_input": ocr_plate,
                "similarity": best_score,
                "match_type": "FUZZY",
                "normalized_ocr": normalized_ocr,
            }

        return None

    def extract_partial_pattern(self, partial_plate: str) -> str:
        """
        Convert a partial plate (e.g., "UP32AB12?4") to a SQL LIKE pattern.
        '?' → '_' (SQL single-char wildcard)
        '*' → '%' (SQL multi-char wildcard)
        """
        normalized = normalize_plate(partial_plate.replace("?", "X").replace("*", "X"))
        pattern = partial_plate.replace("?", "_").replace("*", "%")
        return normalize_plate(pattern.replace("_", "?")).replace("X", "_")
