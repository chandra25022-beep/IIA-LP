"""
Schema Matcher — Multi-Signal Schema Matching

This module implements the schema matching algorithms from IIA-3 lecture notes.

From IIA-3 slides:
  "Given two input schemas, compute a mapping between schema elements
   that passes user validation."

  Similarity Functions (IIA-3, "Similarity Functions" slide):
    - Lexical (Linguistic)-based: Edit distance, Jaccard, cosine (token-level), synonym expansion
    - Structural-based: Uses schema tree/graph (context, neighbours)
    - Instance-based: Distribution similarity -- "Attributes match if they have
      similar instances or value distributions"
    - Hybrid Multi-signal: sim(a,b) = alpha*simlex(a,b) + beta*simsem(a,b) + gamma*siminst(a,b)

  Extended Multi-Signal Model (IIA-3, "Multi-signal matching model" slide):
    Score = wN*N + wI*I + wS*S + wC*C + wO*O
    where:
      N = name/description similarity (lexical)
      I = instance/value similarity   (instance-based)
      S = structural similarity       (context: neighbours, table)
      C = constraint/type compatibility
      O = ontology/synonym compatibility

  Schema Matching vs Mapping (IIA-3 slide):
    "Matching discovers correspondences; mapping operationalizes them into
     executable integration logic."

Reference: IIA-3 slides -- Schema Matching, Similarity Functions, Multi-signal model
"""
from typing import Any, Dict, List, Optional, Set
import re
import sqlite3


# =============================================================================
# Tokenization & Normalization
# =============================================================================

def normalize_name(name: str) -> List[str]:
    """
    Tokenize and normalize an attribute name.
    camelCase -> ['camel', 'case']
    snake_case -> ['snake', 'case']
    ALL_CAPS   -> ['all', 'caps']

    IIA-3: "Tokenization of names" (Linguistic/Lexical Matching slide)
    """
    parts = re.split(r'[_\-\s]+', name)
    tokens = []
    for part in parts:
        sub = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', part)
        tokens.extend(sub.lower().split())
    return tokens


# =============================================================================
# 1. LINGUISTIC (LEXICAL) SIMILARITY
#    IIA-3: "Lexical (Linguistic)-based: Edit distance, Jaccard, cosine"
# =============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Levenshtein edit distance -- IIA-3: 'Edit distance'"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c1 != c2)))
        prev_row = curr_row
    return prev_row[-1]


def lexical_similarity(name1: str, name2: str) -> float:
    """Normalized edit distance similarity. Returns 0.0-1.0."""
    max_len = max(len(name1), len(name2), 1)
    return 1.0 - levenshtein_distance(name1.lower(), name2.lower()) / max_len


def jaccard_token_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Token-level Jaccard similarity.
    J(A,B) = |A intersect B| / |A union B|
    IIA-3: 'Token set similarity = average (best matching token similarity)'
    """
    set1, set2 = set(tokens1), set(tokens2)
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def bigram_set(text: str) -> Set[str]:
    """Character bigrams for cosine-style matching."""
    text = text.lower()
    return set(text[i:i+2] for i in range(len(text) - 1))


def cosine_similarity_bigrams(name1: str, name2: str) -> float:
    """
    Cosine similarity on character bigrams.
    IIA-3: 'cosine (token-level)'
    """
    bg1, bg2 = bigram_set(name1), bigram_set(name2)
    if not bg1 or not bg2:
        return 0.0
    intersection = len(bg1 & bg2)
    return intersection / (len(bg1) ** 0.5 * len(bg2) ** 0.5)


# =============================================================================
# 2. SYNONYM / ONTOLOGY EXPANSION
#    IIA-3: "Synonyms, Acronyms, Thesaurus"
#    "Code = Id = Num = No", "Zip = PIN = Postal"
# =============================================================================

SYNONYM_GROUPS: List[Set[str]] = [
    # Vehicle identifier group -- all these tokens mean "the identifier"
    {"plate", "registration", "reg", "id", "identifier", "ref", "number", "no", "num", "vehicle"},
    # Name group
    {"name", "title", "full", "label"},
    # Date/Time group
    {"date", "time", "timestamp", "when", "at"},
    # Status/state group
    {"status", "state", "condition", "type", "class"},
    # Location group
    {"location", "address", "place", "city", "area", "zone"},
    # Insurance group
    {"policy", "insurance", "insurer", "coverage"},
    # Owner/person group
    {"owner", "holder", "customer", "client", "person", "driver"},
    # Report/record group
    {"report", "case", "record", "log", "entry"},
    # Expiry group
    {"expiry", "expiration", "valid", "until", "end"},
]


def _synonym_group(token: str) -> Optional[int]:
    """Return group index if token belongs to a synonym group, else None."""
    for i, group in enumerate(SYNONYM_GROUPS):
        if token.lower() in group:
            return i
    return None


def ontology_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Synonym/ontology expansion similarity.
    IIA-3: 'Expansion of acronyms', 'Thesaurus: acronyms, synonyms, stop words and categories'

    Returns fraction of token pairs that belong to the same synonym group.
    """
    if not tokens1 or not tokens2:
        return 0.0
    match_count = 0
    for t1 in tokens1:
        for t2 in tokens2:
            g1, g2 = _synonym_group(t1), _synonym_group(t2)
            if g1 is not None and g1 == g2:
                match_count += 1
                break
    return match_count / max(len(tokens1), len(tokens2))


# =============================================================================
# 3. INSTANCE-BASED SIMILARITY
#    IIA-3: "Instance-based: Distribution similarity (e.g., KL divergence)"
#    "Attributes match if they have similar instances or value distributions"
# =============================================================================

def instance_overlap_similarity(values1: List[str], values2: List[str]) -> float:
    """
    Instance-based matching via value overlap (Jaccard on value sets).

    IIA-3 "Inputs to Matching Technique":
      "Data instances -- Attributes match if they have similar instances
       or value distributions"

    IIA-3 "Similarity Functions":
      "Instance-based: Distribution similarity (e.g., KL divergence)"

    Implementation: We use Jaccard overlap on sampled value sets as a
    lightweight proxy for distribution similarity.

    Example in our project:
      'plate_number' has values: {'UP32AB1234', 'MH02EF9012', ...}
      'registration_id' has values: {'UP32AB1234', 'MH02EF9012', ...}
      Overlap = 1.0 -> these are clearly the same concept.
    """
    if not values1 or not values2:
        return 0.0
    norm1 = {str(v).strip().upper() for v in values1 if v}
    norm2 = {str(v).strip().upper() for v in values2 if v}
    if not norm1 or not norm2:
        return 0.0
    intersection = len(norm1 & norm2)
    union = len(norm1 | norm2)
    return intersection / union if union > 0 else 0.0


def sample_column_values(db_path: str, table: str, column: str, limit: int = 50) -> List[str]:
    """Sample actual data values from a source column for instance-based matching."""
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
        cursor = conn.execute(
            f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL LIMIT ?",
            (limit,)
        )
        values = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        return values
    except Exception:
        return []


# =============================================================================
# 4. STRUCTURAL SIMILARITY
#    IIA-3: "Structural-based: Uses schema tree/graph"
#    Structure Matching slide: "Atomic elements are similar if linguistically
#    similar AND their contexts (i.e., ancestors) are similar"
# =============================================================================

def structural_context_similarity(
    attr1: str,
    neighbours1: List[str],
    attr2: str,
    neighbours2: List[str],
) -> float:
    """
    Structural similarity: compare attribute context (neighbouring columns).

    IIA-3 "Structure Matching" (Tree Match Algorithm):
      "Atomic elements are similar if:
         - Linguistically and data-type similar
         - Their contexts (i.e., ancestors) are similar"
      "Compound elements are similar if elements in their subtrees are similar"

    We define 'context' as the set of co-occurring columns in the same table.
    High neighbour overlap is evidence that two attributes play the same role.
    """
    if not neighbours1 or not neighbours2:
        return 0.0
    n1_tokens = set(t for n in neighbours1 for t in normalize_name(n))
    n2_tokens = set(t for n in neighbours2 for t in normalize_name(n))
    intersection = len(n1_tokens & n2_tokens)
    union = len(n1_tokens | n2_tokens)
    return intersection / union if union > 0 else 0.0


def constraint_compatibility(type1: str, type2: str, pk1: bool, pk2: bool) -> float:
    """
    Constraint/type compatibility signal.

    IIA-3 "Multi-signal matching model":
      C = constraint/type compatibility
    IIA-3 "Evidence beyond names":
      "Data types and constraints" + "Keys and foreign keys"

    Attributes with compatible data types and matching key roles
    (both PKs, or both FKs) are more likely to be semantic matches.
    """
    score = 0.0
    t1, t2 = (type1 or "").upper(), (type2 or "").upper()
    if t1 == t2:
        score += 0.6
    elif ("TEXT" in t1 and "TEXT" in t2) or ("INT" in t1 and "INT" in t2) or ("REAL" in t1 and "REAL" in t2):
        score += 0.3
    if pk1 == pk2:
        score += 0.4
    return min(score, 1.0)


# =============================================================================
# 5. MULTI-SIGNAL HYBRID MODEL
#    IIA-3 "Multi-signal matching model" slide:
#      Score = wN*N + wI*I + wS*S + wC*C + wO*O
#
#    IIA-3 "Schema-based hybrid matching algorithm" slide:
#      Wsim = w * Lsim + (1-w) * Ssim   (simpler 2-signal version)
#
#    Our implementation extends to the full 5-signal model.
# =============================================================================

def compute_attribute_similarity(name1: str, name2: str) -> float:
    """
    Fast 3-component hybrid (no instance data required).

    IIA-3 hybrid formula: sim(a,b) = alpha*simlex + beta*simjaccard + gamma*simcosine
    Weights: alpha=0.4, beta=0.3, gamma=0.3
    """
    tokens1 = normalize_name(name1)
    tokens2 = normalize_name(name2)
    joined1 = ' '.join(tokens1)
    joined2 = ' '.join(tokens2)

    L_sim = lexical_similarity(joined1, joined2)
    J_sim = jaccard_token_similarity(tokens1, tokens2)
    C_sim = cosine_similarity_bigrams(joined1, joined2)

    return round(0.4 * L_sim + 0.3 * J_sim + 0.3 * C_sim, 4)


def compute_multisignal_similarity(
    name1: str,
    name2: str,
    instance_values1: Optional[List[str]] = None,
    instance_values2: Optional[List[str]] = None,
    neighbours1: Optional[List[str]] = None,
    neighbours2: Optional[List[str]] = None,
    type1: str = "TEXT",
    type2: str = "TEXT",
    pk1: bool = False,
    pk2: bool = False,
) -> Dict[str, Any]:
    """
    Full multi-signal matching: Score = wN*N + wI*I + wS*S + wC*C + wO*O

    IIA-3 "Multi-signal matching model" slide:
      N = name/description similarity  (wN = 0.35)
      I = instance/value similarity    (wI = 0.25)
      S = structural similarity        (wS = 0.20)
      C = constraint/type compat.      (wC = 0.10)
      O = ontology/synonym             (wO = 0.10)

    Returns a detailed breakdown: each signal's value, weight, and contribution
    to the final score -- making the matching decision fully explainable.
    """
    tokens1 = normalize_name(name1)
    tokens2 = normalize_name(name2)
    joined1 = ' '.join(tokens1)
    joined2 = ' '.join(tokens2)

    # N: Linguistic (edit distance + Jaccard + cosine bigrams)
    N = round(
        0.4 * lexical_similarity(joined1, joined2)
        + 0.3 * jaccard_token_similarity(tokens1, tokens2)
        + 0.3 * cosine_similarity_bigrams(joined1, joined2),
        4
    )
    # I: Instance-based value overlap
    I = round(instance_overlap_similarity(instance_values1 or [], instance_values2 or []), 4)
    # S: Structural/context (co-occurring neighbours)
    S = round(structural_context_similarity(name1, neighbours1 or [], name2, neighbours2 or []), 4)
    # C: Constraint/type compatibility
    C = round(constraint_compatibility(type1, type2, pk1, pk2), 4)
    # O: Ontology/synonym expansion
    O = round(ontology_similarity(tokens1, tokens2), 4)

    # Weighted combination
    score = round(0.35 * N + 0.25 * I + 0.20 * S + 0.10 * C + 0.10 * O, 4)

    return {
        "name1": name1,
        "name2": name2,
        "score": score,
        "signals": {
            "N_linguistic":   {"value": N, "weight": 0.35, "contribution": round(0.35 * N, 4)},
            "I_instance":     {"value": I, "weight": 0.25, "contribution": round(0.25 * I, 4)},
            "S_structural":   {"value": S, "weight": 0.20, "contribution": round(0.20 * S, 4)},
            "C_constraint":   {"value": C, "weight": 0.10, "contribution": round(0.10 * C, 4)},
            "O_ontology":     {"value": O, "weight": 0.10, "contribution": round(0.10 * O, 4)},
        },
        "formula": "Score = 0.35*N + 0.25*I + 0.20*S + 0.10*C + 0.10*O",
        "match_type": _classify_match(score),
    }


def _classify_match(sim: float) -> str:
    """IIA-3: threshold theta -> accept/reject. Classify match quality."""
    if sim >= 0.9:
        return "EXACT"
    elif sim >= 0.75:
        return "HIGH"
    elif sim >= 0.55:
        return "MEDIUM"
    elif sim >= 0.35:
        return "LOW"
    else:
        return "NO_MATCH"


# =============================================================================
# SchemaMatcher Class
# =============================================================================

class SchemaMatcher:
    """
    Schema Matcher for heterogeneous source integration.

    Implements the full IIA-3 matching pipeline:
      1. Linguistic matching (edit distance + Jaccard + cosine)
      2. Instance-based matching (value distribution overlap)
      3. Structural matching (column context/neighbours)
      4. Constraint compatibility (data types, keys)
      5. Ontology/synonym expansion
      6. Multi-signal weighted combination: Score = wN*N + wI*I + wS*S + wC*C + wO*O

    IIA-3: "A strong matcher uses names + structure + instances + constraints + context."

    Schema matching vs mapping distinction (IIA-3):
      - Matching: discovers correspondences (this module)
      - Mapping:  operationalizes them via GAV (schema_mapper.py)
    """

    # Match threshold theta -- IIA-3: "Match if sim(a,b) >= theta"
    THRESHOLD = 0.35

    def __init__(self):
        pass

    def match_schemas(
        self,
        schema1_attrs: List[str],
        schema2_attrs: List[str],
        source1_name: str = "source1",
        source2_name: str = "source2",
        instance_data1: Optional[Dict[str, List[str]]] = None,
        instance_data2: Optional[Dict[str, List[str]]] = None,
        column_types1: Optional[Dict[str, Dict]] = None,
        column_types2: Optional[Dict[str, Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pairwise schema matching between two source schemas.
        Returns all correspondences above threshold theta.

        IIA-3: Output = M = {(ai, bj, sim(ai,bj)) | ai in Sigma1, bj in Sigma2}
        """
        correspondences = []
        for attr1 in schema1_attrs:
            for attr2 in schema2_attrs:
                inst1 = (instance_data1 or {}).get(attr1, [])
                inst2 = (instance_data2 or {}).get(attr2, [])
                col1 = (column_types1 or {}).get(attr1, {})
                col2 = (column_types2 or {}).get(attr2, {})

                result = compute_multisignal_similarity(
                    attr1, attr2,
                    instance_values1=inst1,
                    instance_values2=inst2,
                    neighbours1=[a for a in schema1_attrs if a != attr1],
                    neighbours2=[a for a in schema2_attrs if a != attr2],
                    type1=col1.get("type", "TEXT"),
                    type2=col2.get("type", "TEXT"),
                    pk1=col1.get("pk", False),
                    pk2=col2.get("pk", False),
                )

                if result["score"] >= self.THRESHOLD:
                    correspondences.append({
                        "source1": source1_name,
                        "attr1": attr1,
                        "source2": source2_name,
                        "attr2": attr2,
                        "similarity": result["score"],
                        "match_type": result["match_type"],
                        "signals": result["signals"],
                        "formula": result["formula"],
                    })

        correspondences.sort(key=lambda x: x["similarity"], reverse=True)
        return correspondences

    def match_all_sources(self, source_schemas: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Pairwise schema matching across all sources (for Integration View page)."""
        sources = list(source_schemas.keys())
        all_correspondences = []
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                s1, s2 = sources[i], sources[j]
                pairs = self.match_schemas(source_schemas[s1], source_schemas[s2], s1, s2)
                all_correspondences.extend(pairs)
        return all_correspondences

    def find_key_correspondences(
        self,
        source_schemas: Dict[str, List[str]],
        instance_data: Optional[Dict[str, Dict[str, List[str]]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Multi-signal matching for the vehicle identifier across all 5 sources.

        Demonstrates the core IIA schema heterogeneity problem:
          capture.plate_number <-> insurance.registration_id <-> registration.vehicle_reg_no
          <-> theft.vehicle_identifier <-> ministry.vehicle_ref

        With real instance data (I signal), these score much higher than pure
        linguistic matching because they share the same concrete plate values.

        IIA-3: "Attributes match if they have similar instances or value distributions"
        """
        key_attrs = {
            "capture":      "plate_number",
            "insurance":    "registration_id",
            "registration": "vehicle_reg_no",
            "theft":        "vehicle_identifier",
            "ministry":     "vehicle_ref",
        }
        all_columns = {
            "capture":      ["capture_id", "plate_number", "detected_vehicle_type", "detected_color", "capture_timestamp", "capture_location"],
            "insurance":    ["policy_id", "registration_id", "insurer_name", "policy_number", "policy_expiry_date", "insurance_status"],
            "registration": ["reg_serial", "vehicle_reg_no", "owner_name", "manufacturer", "model_name", "registered_color", "registration_status"],
            "theft":        ["case_id", "vehicle_identifier", "case_type", "case_status", "fir_number", "police_station"],
            "ministry":     ["report_id", "vehicle_ref", "report_type", "report_date", "severity", "report_status"],
        }

        results = []
        sources = list(key_attrs.keys())
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                s1, s2 = sources[i], sources[j]
                a1, a2 = key_attrs[s1], key_attrs[s2]

                inst1 = (instance_data or {}).get(s1, {}).get(a1, [])
                inst2 = (instance_data or {}).get(s2, {}).get(a2, [])

                result = compute_multisignal_similarity(
                    a1, a2,
                    instance_values1=inst1,
                    instance_values2=inst2,
                    neighbours1=[c for c in all_columns.get(s1, []) if c != a1],
                    neighbours2=[c for c in all_columns.get(s2, []) if c != a2],
                )

                results.append({
                    "source1": s1,
                    "attr1": a1,
                    "source2": s2,
                    "attr2": a2,
                    "similarity": result["score"],
                    "match_type": result["match_type"],
                    "signals": result["signals"],
                    "underlying_concept": "registration_number",
                    "note": (
                        f"Instance-I={result['signals']['I_instance']['value']:.2f} "
                        f"(shared vehicle plate values boost score). "
                        f"Linguistic-N={result['signals']['N_linguistic']['value']:.2f}. "
                        "Same vehicle identifier, 5 different names -- the core schema heterogeneity."
                    ),
                })
        return results
