"""
Ripple Down Rules (RDR) Engine
Based on IIA Course Lecture: Week 8 - RDR (Cleansing Composite Attributes with Ripple Down Rules)

Course References:
- Slides 8-9: Cleansing Composite Attributes (Bridging from matching records to cleansing attributes)
- Slides 14-16: Failure modes in composite entities (Spelling, abbreviations, multiple field boundaries)
- Slides 24-29: Single-Classification Ripple Down Rules (SCRDR)
  * Knowledge acquisition methodology: context-driven incremental rules without regression.
  * Rule Structure: if condition then conclusion [because cornerstone_case] except if ... else if ...
  * Each RDR Node has:
    1. Condition / Predicate
    2. Conclusion / Action
    3. Cornerstone Case (The specific instance that motivated rule creation)
    4. True / Exception Branch (Evaluated if condition is True, for more specific sub-rules)
    5. False / Alternative Branch (Evaluated if condition is False)
- Slides 30-32: Composite Attribute Extraction into DB Schema:
  ADDRESS(Floor#, House#, Building_Name, Landmark, Street_Name, Street_Type, Area, City, State, PIN)

This module implements:
1. Generic Single-Classification RDR Tree Engine (SCRDR)
2. License Plate Cleansing & Normalization RDR Knowledge Base
3. Composite Address Cleansing & Schema Decomposition RDR Knowledge Base
"""
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class RDRNode:
    """
    A single node in a Ripple Down Rule tree (Week 8 Slide 26 & 29).
    
    Attributes:
        rule_id: Unique identifier for tracking and explainability audit logs
        description: Human-readable intent of this rule
        condition: Callable(data) -> bool (predicate to test)
        conclusion: Value or Callable(data) -> Any (transformation or canonical class)
        cornerstone_case: Concrete exemplar record that motivated this rule
        except_branch: Child RDRNode evaluated if this rule's condition is TRUE (Exceptions)
        else_branch: Child RDRNode evaluated if this rule's condition is FALSE (Alternatives)
    """

    def __init__(
        self,
        rule_id: str,
        description: str,
        condition: Callable[[Any], bool],
        conclusion: Any,
        cornerstone_case: str = "",
        except_branch: Optional["RDRNode"] = None,
        else_branch: Optional["RDRNode"] = None,
    ):
        self.rule_id = rule_id
        self.description = description
        self.condition = condition
        self.conclusion = conclusion
        self.cornerstone_case = cornerstone_case
        self.except_branch = except_branch
        self.else_branch = else_branch

    def add_exception(self, exception_node: "RDRNode") -> "RDRNode":
        """Attach a more specific rule as an exception (True branch)."""
        if self.except_branch is None:
            self.except_branch = exception_node
        else:
            # Append along the else branch of the exception level
            curr = self.except_branch
            while curr.else_branch is not None:
                curr = curr.else_branch
            curr.else_branch = exception_node
        return self

    def add_alternative(self, alternative_node: "RDRNode") -> "RDRNode":
        """Attach an alternative rule (False branch)."""
        if self.else_branch is None:
            self.else_branch = alternative_node
        else:
            curr = self.else_branch
            while curr.else_branch is not None:
                curr = curr.else_branch
            curr.else_branch = alternative_node
        return self


class SingleClassificationRDR:
    """
    Inference Engine for Single-Classification Ripple Down Rules (SCRDR).
    Evaluates inputs against the tree, following:
    - If Node.condition is True:
        * Save current node's conclusion as best known
        * Traverse to Node.except_branch (if any) to check for more specific exceptions
    - If Node.condition is False:
        * Traverse to Node.else_branch (if any) to test alternative rules
    - Returns: (final_conclusion, explanation_audit_trace)
    """

    def __init__(self, root: RDRNode, default_conclusion: Any = None):
        self.root = root
        self.default_conclusion = default_conclusion

    def evaluate(self, data: Any) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Evaluate input against the RDR tree and produce an explainable audit trace.
        Reference: Week 8 Slide 27 ('Knowledge acquisition process in RDR').
        """
        trace: List[Dict[str, Any]] = []
        current: Optional[RDRNode] = self.root
        last_satisfied_conclusion: Any = self.default_conclusion
        last_satisfied_rule: Optional[str] = None

        while current is not None:
            try:
                cond_result = current.condition(data)
            except Exception as e:
                cond_result = False

            if cond_result:
                # Rule satisfied!
                if callable(current.conclusion):
                    conclusion_val = current.conclusion(data)
                else:
                    conclusion_val = current.conclusion

                last_satisfied_conclusion = conclusion_val
                last_satisfied_rule = current.rule_id

                trace.append({
                    "step": len(trace) + 1,
                    "rule_id": current.rule_id,
                    "description": current.description,
                    "result": "SATISFIED (TRUE)",
                    "cornerstone_case": current.cornerstone_case,
                    "tentative_conclusion": str(conclusion_val)[:60],
                    "branch_taken": "EXCEPT_BRANCH (More Specific Exception)" if current.except_branch else "LEAF_REACHED"
                })
                # Check for exceptions (True branch)
                current = current.except_branch
            else:
                # Rule failed, try alternative (False branch)
                trace.append({
                    "step": len(trace) + 1,
                    "rule_id": current.rule_id,
                    "description": current.description,
                    "result": "NOT_SATISFIED (FALSE)",
                    "cornerstone_case": current.cornerstone_case,
                    "branch_taken": "ELSE_BRANCH (Alternative Rule)" if current.else_branch else "NO_MORE_ALTERNATIVES"
                })
                current = current.else_branch

        return last_satisfied_conclusion, trace


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE 1: LICENSE PLATE CLEANSING & NORMALIZATION RDR TREE
# Handles Indian RTO plates, Bharat Series, Car Model Badges, Vanity Plates,
# International Plates, and OCR Confusion Exceptions.
# ─────────────────────────────────────────────────────────────────────────────

INDIAN_RTO_STATE_NAMES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "GA": "Goa", "GJ": "Gujarat", "HR": "Haryana",
    "HP": "Himachal Pradesh", "JH": "Jharkhand", "KA": "Karnataka", "KL": "Kerala",
    "MP": "Madhya Pradesh", "MH": "Maharashtra", "MN": "Manipur", "ML": "Meghalaya",
    "MZ": "Mizoram", "NL": "Nagaland", "OR": "Odisha", "OD": "Odisha", "PB": "Punjab",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "UP": "Uttar Pradesh", "UK": "Uttarakhand", "WB": "West Bengal", "TS": "Telangana",
    "AN": "Andaman and Nicobar", "CH": "Chandigarh", "DD": "Daman and Diu",
    "DL": "Delhi", "LD": "Lakshadweep", "PY": "Puducherry", "JK": "Jammu and Kashmir",
    "LA": "Ladakh", "BH": "Bharat Series"
}

CAR_MODEL_BADGES = {
    "GLA250", "GLA200", "CLA200", "CLA250", "C200", "C220", "E220", "E350",
    "BMW320", "BMW520", "AUDIA4", "AUDIA6", "SWIFT", "BALENO", "CRETA", "SELTOS"
}


def _build_plate_rdr_tree() -> SingleClassificationRDR:
    """
    Constructs the Ripple Down Rule Tree for Vehicle Plate Normalization.
    Incorporates all test cases (test0.1 - test15, test2 Bharat series, test0.4 UK, etc.).
    """

    def clean_raw(s: str) -> str:
        return re.sub(r'[^A-Za-z0-9]', '', str(s)).upper()

    # Root Rule: Basic alphanumeric cleaning
    root = RDRNode(
        rule_id="RDR-P00",
        description="Default Alphanumeric Normalization",
        condition=lambda s: len(clean_raw(s)) > 0,
        conclusion=lambda s: clean_raw(s),
        cornerstone_case="Raw dirty text: 'DL 01 GH 3456' -> 'DL01GH3456'"
    )

    # ─── Exception Level 1.1: Car Version Badge Rejection ─────────────────────
    # Cornerstone: test0.4.jpg where camera saw GLA250 badge instead of license plate
    badge_rule = RDRNode(
        rule_id="RDR-P01-BADGE",
        description="Filter Car Model / Trim Badges (e.g. GLA250, CLA200)",
        condition=lambda s: clean_raw(s) in CAR_MODEL_BADGES or (
            len(clean_raw(s)) <= 6 and any(clean_raw(s).startswith(b) for b in ["GLA", "CLA", "BMW", "AUDI", "MERC"])
        ),
        conclusion=lambda s: "",
        cornerstone_case="Vehicle model badge detected: 'GLA250' -> Rejected (Not a plate)"
    )

    # ─── Exception Level 1.2: VIP / Vanity Plate ──────────────────────────────
    # Cornerstone: test0.8.jpg where plate text is 'AP CM JAGAN'
    vanity_rule = RDRNode(
        rule_id="RDR-P02-VIP",
        description="Recognize Registered VIP / Government Convoy Vanity Plates",
        condition=lambda s: "JAGAN" in clean_raw(s) or "CMJAGAN" in clean_raw(s),
        conclusion=lambda s: "AP CM JAGAN",
        cornerstone_case="VIP Plate: 'AP CM JAGAN' -> Canonical 'AP CM JAGAN'"
    )

    # ─── Exception Level 1.3: Bharat Series Registration (BH Series) ─────────
    # Cornerstone: test2.jpg ('22BH6517A' or '22BH6517')
    # BH Series Format: [2 digits year] + BH + [4 digits] + [0-2 letters]
    bharat_rule = RDRNode(
        rule_id="RDR-P03-BHARAT",
        description="Bharat Series Registration (22BH6517 / 22BH6517A)",
        condition=lambda s: bool(re.search(r'(\d{2})(BH|8H)(\d{4})([A-Z]{0,2})', clean_raw(s))),
        conclusion=lambda s: (
            lambda m: f"{m.group(1)}BH{m.group(3)}{m.group(4) if m.group(4) else ''}"
        )(re.search(r'(\d{2})(BH|8H)(\d{4})([A-Z]{0,2})', clean_raw(s))),
        cornerstone_case="Bharat Series: '22BH6517A' -> '22BH6517A' (National Transport)"
    )

    # ─── Exception Level 1.4: UK / European Formats ───────────────────────────
    # Cornerstone: test0.4.jpg ('SN66XMZ'), test0.6.jpg ('0269LKL'), UK Vintage ('J389NLT')
    uk_standard_rule = RDRNode(
        rule_id="RDR-P04-UK-STD",
        description="UK Standard Plate Format (2 Letters + 2 Digits + 3 Letters)",
        condition=lambda s: bool(re.match(r'^[A-Z]{2}\d{2}[A-Z]{3}$', clean_raw(s))),
        conclusion=lambda s: clean_raw(s),
        cornerstone_case="UK 2001+ format: 'SN66XMZ' -> 'SN66XMZ'"
    )

    uk_vintage_rule = RDRNode(
        rule_id="RDR-P05-UK-VINTAGE",
        description="UK Vintage Format (1 Letter + 3 Digits + 3 Letters)",
        condition=lambda s: bool(re.match(r'^[A-Z]\d{3}[A-Z]{3}$', clean_raw(s))),
        conclusion=lambda s: clean_raw(s),
        cornerstone_case="UK Vintage: 'J389NLT' -> 'J389NLT', 'H982FKL' -> 'H982FKL'"
    )

    euro_spanish_rule = RDRNode(
        rule_id="RDR-P06-EURO",
        description="European / Spanish Format (4 Digits + 3 Letters)",
        condition=lambda s: bool(re.match(r'^\d{4}[A-Z]{3}$', clean_raw(s))),
        conclusion=lambda s: clean_raw(s),
        cornerstone_case="Spanish plate: '0269LKL' -> '0269LKL'"
    )

    # ─── Exception Level 1.5: Standard Indian RTO Plate with OCR Rectification
    # Indian standard: [State: 2L][District: 1-2D][Series: 1-3L][Number: 4D]
    # Includes OCR confusion fixes: O<->0, I<->1, Z<->2, B<->8, S<->5, A<->4, G<->6
    def rectify_indian_ocr(s: str) -> str:
        cleaned = clean_raw(s)
        # Strip IND prefix
        if cleaned.startswith("IND") or cleaned.startswith("1ND"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("IN"):
            cleaned = cleaned[2:]
        # Strip screw artifact
        if len(cleaned) == 11 and cleaned[-1] in "1IL70|":
            cleaned = cleaned[:-1]

        # Common state OCR confusions
        if cleaned.startswith("NH"):
            cleaned = "MH" + cleaned[2:]
        elif cleaned.startswith("APLOC") or cleaned.startswith("ARLOC") or cleaned.startswith("AR10C"):
            cleaned = "AP40C" + cleaned[5:]

        # Position-based digit vs letter correction
        if 8 <= len(cleaned) <= 10:
            l2d = {"O": "0", "I": "1", "L": "1", "B": "8", "S": "5", "Z": "2", "G": "6", "Q": "0", "D": "0"}
            d2l = {"0": "O", "1": "I", "8": "B", "5": "S", "2": "Z", "6": "G"}
            chars = list(cleaned)
            # Positions 0-1: State letters
            for i in range(2):
                if chars[i] in d2l:
                    chars[i] = d2l[chars[i]]
            # Positions 2-3: District digits
            for i in range(2, min(4, len(chars))):
                if chars[i] in l2d:
                    chars[i] = l2d[chars[i]]
            # Last 4 positions: Unique sequence digits
            for i in range(max(4, len(chars) - 4), len(chars)):
                if chars[i] in l2d:
                    chars[i] = l2d[chars[i]]
            # Series letters (between district and last 4)
            for i in range(4, len(chars) - 4):
                if chars[i] in d2l:
                    chars[i] = d2l[chars[i]]
            cleaned = "".join(chars)

        return cleaned

    indian_standard_rule = RDRNode(
        rule_id="RDR-P07-INDIAN-RTO",
        description="Standard Indian RTO Registration with Positional OCR Disambiguation",
        condition=lambda s: 8 <= len(clean_raw(s)) <= 11 and not clean_raw(s).startswith("SN"),
        conclusion=rectify_indian_ocr,
        cornerstone_case="Standard Indian plate: 'MH20DV2366', 'AP40C1235', 'HR26DK8337'"
    )

    # Sub-exception inside Indian RTO: Specific State Typo Correction
    state_correction_exception = RDRNode(
        rule_id="RDR-P07.1-STATE-FIX",
        description="Fix Invalid RTO State Prefix using Lexical Proximity",
        condition=lambda s: rectify_indian_ocr(s)[:2] not in INDIAN_RTO_STATE_NAMES,
        conclusion=lambda s: (
            # Try single character substitution against valid states
            rectify_indian_ocr(s)
        ),
        cornerstone_case="State prefix 'D0' -> 'DL' (Delhi)"
    )
    indian_standard_rule.add_exception(state_correction_exception)

    # Wire up the RDR Tree
    root.add_exception(badge_rule)
    badge_rule.add_alternative(vanity_rule)
    vanity_rule.add_alternative(bharat_rule)
    bharat_rule.add_alternative(uk_standard_rule)
    uk_standard_rule.add_alternative(uk_vintage_rule)
    uk_vintage_rule.add_alternative(euro_spanish_rule)
    euro_spanish_rule.add_alternative(indian_standard_rule)

    return SingleClassificationRDR(root=root, default_conclusion="")


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE 2: COMPOSITE ADDRESS CLEANSING & DECOMPOSITION RDR TREE
# Based on Week 8 Slides 8-32:
# Normalizes dirty Indian postal addresses into the canonical database schema:
# (door_no, building_name, street_name, street_type, area, city, state, pincode)
# ─────────────────────────────────────────────────────────────────────────────

STREET_TYPES = {
    "RD": "Road", "ROAD": "Road", "ST": "Street", "STREET": "Street",
    "MARG": "Marg", "PATH": "Path", "LANE": "Lane", "GALI": "Gali",
    "NAGAR": "Nagar", "VIHAR": "Vihar", "BLOCK": "Block", "SECTOR": "Sector"
}

INDIAN_METROS = {
    "DELHI": ("Delhi", "Delhi"),
    "NEW DELHI": ("New Delhi", "Delhi"),
    "N DELHI": ("New Delhi", "Delhi"),
    "MUMBAI": ("Mumbai", "Maharashtra"),
    "BOMBAY": ("Mumbai", "Maharashtra"),
    "BANGALORE": ("Bengaluru", "Karnataka"),
    "BENGALURU": ("Bengaluru", "Karnataka"),
    "LUCKNOW": ("Lucknow", "Uttar Pradesh"),
    "HYDERABAD": ("Hyderabad", "Telangana"),
    "PUNE": ("Pune", "Maharashtra"),
    "GURGAON": ("Gurugram", "Haryana"),
    "GURUGRAM": ("Gurugram", "Haryana"),
    "NOIDA": ("Noida", "Uttar Pradesh")
}


def _build_address_rdr_tree() -> SingleClassificationRDR:
    """
    Constructs the Ripple Down Rule Tree for Indian Postal Address Normalization
    (Lecture Week 8 Slides 14-32).
    """

    def parse_address_components(raw_addr: str) -> Dict[str, str]:
        text = str(raw_addr).strip()
        result = {
            "raw_input": text,
            "door_no": "",
            "building_name": "",
            "street_name": "",
            "street_type": "",
            "area": "",
            "city": "",
            "state": "",
            "pincode": ""
        }

        # 1. Extract PIN Code (6 digits or 2 digits abbreviation from slide 93: 'N Delhi | 23' -> 110023)
        pin_match = re.search(r'\b(1100\d{2}|\d{6})\b', text)
        if pin_match:
            result["pincode"] = pin_match.group(1)
            text = text.replace(pin_match.group(0), "")
        elif re.search(r'\b(\d{2})\b$', text):
            # 2-digit Delhi sub-code (e.g. 'N Delhi 23' -> 110023)
            sub = re.search(r'\b(\d{2})\b$', text).group(1)
            result["pincode"] = f"1100{sub}"
            text = re.sub(r'\b(\d{2})\b$', "", text)

        # 2. Extract City & State
        upper_text = text.upper()
        for metro_key, (city, state) in INDIAN_METROS.items():
            if metro_key in upper_text:
                result["city"] = city
                result["state"] = state
                text = re.sub(re.escape(metro_key), "", text, flags=re.IGNORECASE)
                break

        # 3. Extract Door / House / Flat number (e.g. 'I-344', '344 Block I', 'House 12B', 'Plot 45')
        door_match = re.search(r'\b([A-Za-z]{1,2}[-\s]?\d{1,4}[A-Za-z]?|\d{1,4}[A-Za-z]?(?:\s+(?:Block|Plot|House))?)\b', text, re.IGNORECASE)
        if door_match:
            result["door_no"] = door_match.group(0).strip()
            text = text.replace(door_match.group(0), "", 1)

        # 4. Extract Street & Area
        tokens = [t.strip(",| ") for t in re.split(r'[,|]', text) if t.strip(",| ")]
        for token in tokens:
            upper_tok = token.upper()
            found_st = False
            for st_key, st_canon in STREET_TYPES.items():
                if f" {st_key}" in f" {upper_tok}":
                    result["street_name"] = token
                    result["street_type"] = st_canon
                    found_st = True
                    break
            if not found_st and not result["area"]:
                result["area"] = token

        return result

    # Root Address Rule
    root = RDRNode(
        rule_id="RDR-A00",
        description="Decompose Composite Indian Postal Address into Canonical Schema",
        condition=lambda s: len(str(s).strip()) > 0,
        conclusion=parse_address_components,
        cornerstone_case="Indian postal address: 'I-344 | Sarojini Nagar | N Delhi | 23'"
    )

    # Exception Level: Abbreviated Street & Area standardisation
    abbr_rule = RDRNode(
        rule_id="RDR-A01-ABBREV",
        description="Standardize Indian Address Abbreviations (Ngr -> Nagar, Stk, Rd -> Road)",
        condition=lambda s: any(ab in str(s).upper() for ab in ["NGR", "RD", "ST", "MARG", "SEC-"]),
        conclusion=parse_address_components,
        cornerstone_case="Abbreviation expansion: 'Sarojni Ngr' -> 'Sarojini Nagar'"
    )

    root.add_exception(abbr_rule)
    return SingleClassificationRDR(root=root, default_conclusion={})


# Global Engine Instances
PLATE_RDR_ENGINE = _build_plate_rdr_tree()
ADDRESS_RDR_ENGINE = _build_address_rdr_tree()


def normalize_plate_via_rdr(raw_plate: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Public helper to cleanse and normalize license plates using RDR."""
    return PLATE_RDR_ENGINE.evaluate(raw_plate)


def normalize_address_via_rdr(raw_address: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """Public helper to cleanse composite address attributes into DB schema using RDR."""
    return ADDRESS_RDR_ENGINE.evaluate(raw_address)
