"""
Schema Mapper — Global-As-View (GAV) Schema Mapping

This module implements the GAV schema mapping approach taught in IIA-3.

In GAV: The global schema is defined in terms of source schemas.
Each global attribute is expressed as a view over one or more source attributes.

The central heterogeneity problem (required by project spec):
  5 databases use DIFFERENT attribute names for the SAME underlying value:

  Global Schema            → Source Schema Mapping
  ─────────────────────────────────────────────────
  registration_number      ← capture.plate_number
  registration_number      ← insurance.registration_id
  registration_number      ← registration.vehicle_reg_no
  registration_number      ← theft.vehicle_identifier
  registration_number      ← ministry.vehicle_ref

Reference: IIA-3 slides, GAV vs LAV discussion
Reference: CLIO schema mapping paper (IIA-2)
"""
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# GAV MAPPING TABLE
# Maps global attribute names to their local counterparts in each source.
# This is the "correspondence" set from the CLIO paper (IIA-2).
# ─────────────────────────────────────────────────────────────────────────────
GAV_MAPPING: Dict[str, Dict[str, str]] = {
    # The primary integration key — same value, different names in each source
    "registration_number": {
        "capture":      "plate_number",
        "insurance":    "registration_id",
        "registration": "vehicle_reg_no",
        "theft":        "vehicle_identifier",
        "ministry":     "vehicle_ref",
    },
    # Secondary attribute mappings
    "vehicle_type": {
        "capture":      "detected_vehicle_type",
        "registration": "vehicle_class",
    },
    "color": {
        "capture":      "detected_color",
        "registration": "registered_color",
    },
    "status": {
        "insurance":    "insurance_status",
        "registration": "registration_status",
        "theft":        "case_status",
        "ministry":     "report_status",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# REVERSE MAPPING
# Given a source name and local attribute, find the global attribute name.
# ─────────────────────────────────────────────────────────────────────────────
def build_reverse_mapping() -> Dict[str, Dict[str, str]]:
    """Build source_name → local_attr → global_attr reverse lookup."""
    reverse: Dict[str, Dict[str, str]] = {}
    for global_attr, source_map in GAV_MAPPING.items():
        for source_name, local_attr in source_map.items():
            if source_name not in reverse:
                reverse[source_name] = {}
            reverse[source_name][local_attr] = global_attr
    return reverse

REVERSE_MAPPING = build_reverse_mapping()


class SchemaMapper:
    """
    Implements GAV (Global-As-View) schema mapping.

    The role of the SchemaMapper is to:
    1. Translate global attribute names to local source attribute names.
    2. Translate local source attribute names back to global attribute names.
    3. Generate sub-queries for each source using their local attribute names.

    This is what separates proper Information Integration from a simple join.
    """

    def get_local_key(self, source_name: str, global_attr: str = "registration_number") -> Optional[str]:
        """
        Given a source and a global attribute name, return the local attribute name.

        Example:
            get_local_key("insurance", "registration_number")
            → "registration_id"

            get_local_key("capture", "registration_number")
            → "plate_number"
        """
        return GAV_MAPPING.get(global_attr, {}).get(source_name)

    def get_global_attr(self, source_name: str, local_attr: str) -> Optional[str]:
        """
        Given a source and its local attribute, return the global attribute.

        Example:
            get_global_attr("insurance", "registration_id")
            → "registration_number"
        """
        return REVERSE_MAPPING.get(source_name, {}).get(local_attr)

    def translate_record_to_global(self, source_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a source record's attribute names to global schema names
        where a mapping exists.

        Unmapped attributes are kept under their original names prefixed
        with the source name to avoid collisions.
        """
        translated = {}
        source_reverse = REVERSE_MAPPING.get(source_name, {})
        for local_attr, value in record.items():
            if local_attr in source_reverse:
                global_attr = source_reverse[local_attr]
                translated[global_attr] = value
            else:
                # Keep original, namespaced by source to avoid collision
                translated[f"{source_name}.{local_attr}"] = value
        return translated

    def get_all_source_keys(self, global_attr: str = "registration_number") -> Dict[str, str]:
        """
        Return all source-to-local-key mappings for a global attribute.
        Used for displaying the schema mapping in the Integration View page.
        """
        return GAV_MAPPING.get(global_attr, {})

    def get_full_mapping_table(self) -> List[Dict[str, Any]]:
        """
        Return the complete GAV mapping as a list for the UI.
        Each entry shows global_attr → source → local_attr.
        """
        rows = []
        for global_attr, source_map in GAV_MAPPING.items():
            for source_name, local_attr in source_map.items():
                rows.append({
                    "global_attribute": global_attr,
                    "source": source_name,
                    "local_attribute": local_attr,
                    "mapping_type": "GAV",
                })
        return rows

    def generate_sub_query_params(self, source_name: str, registration_number: str) -> Dict[str, Any]:
        """
        Generate the query parameters for a specific source, translating
        the global registration_number to the source's local key.

        Returns dict with:
            - local_key: the attribute name in this source
            - value: the value to search for
        """
        local_key = self.get_local_key(source_name, "registration_number")
        if not local_key:
            return {}
        return {
            "local_key": local_key,
            "value": registration_number,
            "source": source_name,
        }
