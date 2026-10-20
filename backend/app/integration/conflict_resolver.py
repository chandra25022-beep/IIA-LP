"""
Conflict Resolver — Handling Data Conflicts Across Independent Sources

When multiple independently designed databases provide conflicting values
for the same real-world entity, we must detect and handle the conflict.

From IIA-1 lecture:
  "When two sources disagree, how should an intelligent system decide what to believe?"

Conflict types handled:
  1. VALUE CONFLICT: Two sources report different values for the same attribute
     (e.g., Capture DB says WHITE, Registration DB says SILVER)
  2. TEMPORAL CONFLICT: Records have different timestamps
  3. MISSING DATA: One source has a value, another doesn't

Reference: IIA-1 slide 8 — "Integration is the process of constructing
defensible knowledge from heterogeneous evidence."
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class ConflictRecord:
    """Represents a detected conflict between two sources."""

    def __init__(
        self,
        attribute: str,
        source1: str,
        value1: Any,
        source2: str,
        value2: Any,
        conflict_type: str = "VALUE_CONFLICT",
        resolved_value: Any = None,
        resolution_strategy: str = "REPORTED_TO_USER",
    ):
        self.attribute = attribute
        self.source1 = source1
        self.value1 = value1
        self.source2 = source2
        self.value2 = value2
        self.conflict_type = conflict_type
        self.resolved_value = resolved_value
        self.resolution_strategy = resolution_strategy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "source1": self.source1,
            "value1": str(self.value1) if self.value1 is not None else None,
            "source2": self.source2,
            "value2": str(self.value2) if self.value2 is not None else None,
            "conflict_type": self.conflict_type,
            "resolved_value": str(self.resolved_value) if self.resolved_value is not None else None,
            "resolution_strategy": self.resolution_strategy,
        }


class ConflictResolver:
    """
    Detects and resolves conflicts between independently designed data sources.

    Resolution strategies (configurable per attribute):
    - TRUST_REGISTRATION: Registration DB is authoritative (for registered_color, owner)
    - TRUST_INSURANCE: Insurance DB is authoritative (for insurance_status)
    - TRUST_MOST_RECENT: Most recently updated record wins
    - TRUST_MAJORITY: Value present in majority of sources wins
    - REPORT_CONFLICT: Cannot resolve; expose conflict to the user
    """

    # Attribute-level resolution strategies
    RESOLUTION_STRATEGIES = {
        "color":                 "TRUST_REGISTRATION",  # Registered color is authoritative
        "registered_color":      "TRUST_REGISTRATION",
        "detected_color":        "REPORT_CONFLICT",      # Detection may be wrong
        "registration_status":   "TRUST_REGISTRATION",
        "insurance_status":      "TRUST_INSURANCE",
        "vehicle_type":          "TRUST_REGISTRATION",
        "vehicle_class":         "TRUST_REGISTRATION",
    }

    def detect_color_conflict(
        self,
        capture_record: Optional[Dict[str, Any]],
        registration_record: Optional[Dict[str, Any]],
    ) -> Optional[ConflictRecord]:
        """
        Detect color mismatch between capture (detected) and registration (registered).
        This is a classic data conflict in Information Integration.
        """
        if not capture_record or not registration_record:
            return None

        detected = capture_record.get("detected_color") or ""
        detected = detected.upper().strip()
        
        registered = registration_record.get("registered_color") or ""
        registered = registered.upper().strip()

        if not detected or not registered:
            return None

        # Normalize color names for comparison
        color_aliases = {
            "WHITE": ["WHITE", "PEARL WHITE", "OFF WHITE"],
            "SILVER": ["SILVER", "GREY", "GRAY", "METALLIC SILVER"],
            "BLACK": ["BLACK", "MATTE BLACK"],
            "RED": ["RED", "MAROON"],
            "BLUE": ["BLUE", "NAVY BLUE", "DARK BLUE"],
        }

        def resolve_color(color: str) -> str:
            for canonical, aliases in color_aliases.items():
                if color in aliases:
                    return canonical
            return color

        canonical_detected = resolve_color(detected)
        canonical_registered = resolve_color(registered)

        if canonical_detected != canonical_registered:
            return ConflictRecord(
                attribute="color",
                source1="capture",
                value1=detected,
                source2="registration",
                value2=registered,
                conflict_type="VALUE_CONFLICT",
                resolved_value=registered,  # Trust registration as authoritative
                resolution_strategy="TRUST_REGISTRATION",
            )
        return None

    def detect_status_conflicts(
        self,
        insurance_record: Optional[Dict[str, Any]],
        theft_record: Optional[Dict[str, Any]],
        registration_record: Optional[Dict[str, Any]],
    ) -> List[ConflictRecord]:
        """Detect conflicting statuses across sources."""
        conflicts = []

        # Check: Insurance says active but theft says stolen
        if insurance_record and theft_record:
            ins_status = insurance_record.get("insurance_status", "")
            case_type = theft_record.get("case_type", "")
            case_status = theft_record.get("case_status", "")
            if ins_status == "ACTIVE" and case_type == "STOLEN" and case_status == "OPEN":
                conflicts.append(ConflictRecord(
                    attribute="vehicle_active_status",
                    source1="insurance",
                    value1="INSURED_ACTIVE",
                    source2="theft",
                    value2="STOLEN_OPEN",
                    conflict_type="SEMANTIC_CONFLICT",
                    resolved_value="SUSPICIOUS",
                    resolution_strategy="TRUST_THEFT_DB",
                ))

        # Check: Registration active but theft says scrapped
        if registration_record and theft_record:
            reg_status = registration_record.get("registration_status", "")
            case_type = theft_record.get("case_type", "")
            if reg_status == "ACTIVE" and case_type in ("SCRAPPED", "SHREDDED"):
                conflicts.append(ConflictRecord(
                    attribute="vehicle_physical_status",
                    source1="registration",
                    value1="REGISTRATION_ACTIVE",
                    source2="theft",
                    value2=case_type,
                    conflict_type="SEMANTIC_CONFLICT",
                    resolved_value=case_type,
                    resolution_strategy="TRUST_THEFT_DB",
                ))

        return conflicts

    def resolve_all_conflicts(
        self,
        capture_record: Optional[Dict[str, Any]],
        insurance_record: Optional[Dict[str, Any]],
        registration_record: Optional[Dict[str, Any]],
        theft_record: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run all conflict detection and return a summary.
        Returns:
            - conflicts: list of ConflictRecord.to_dict()
            - has_conflicts: bool
            - conflict_count: int
        """
        all_conflicts: List[ConflictRecord] = []

        # Color conflict check
        color_conflict = self.detect_color_conflict(capture_record, registration_record)
        if color_conflict:
            all_conflicts.append(color_conflict)

        # Status conflict checks
        status_conflicts = self.detect_status_conflicts(
            insurance_record, theft_record, registration_record
        )
        all_conflicts.extend(status_conflicts)

        return {
            "conflicts": [c.to_dict() for c in all_conflicts],
            "has_conflicts": len(all_conflicts) > 0,
            "conflict_count": len(all_conflicts),
        }

    def handle_missing_data(
        self,
        source_name: str,
        record: Optional[Dict[str, Any]],
        required_fields: List[str],
    ) -> Dict[str, Any]:
        """
        Handle missing data from a source.
        Returns a report of which fields are missing.
        """
        if record is None:
            return {
                "source": source_name,
                "status": "NO_RECORD_FOUND",
                "missing_fields": required_fields,
            }

        missing = [f for f in required_fields if not record.get(f)]
        return {
            "source": source_name,
            "status": "PARTIAL_DATA" if missing else "COMPLETE",
            "missing_fields": missing,
        }
