"""
String Matching & Similarity Measures Engine
Based on IIA Course Notes: Week 6-8 (Data & Text String Matching)

Implements:
1. Sequence-based Measures:
   - Levenshtein / Edit Distance (Dynamic Programming) [Slides 16-19]
   - Jaro Similarity [Slides 20-21]
   - Jaro-Winkler Similarity (Prefix-weighting) [Slide 22]
2. Set-based Measures:
   - Overlap Coefficient [Slide 25]
   - Jaccard Similarity (character q-grams & word tokens) [Slide 26]
   - TF-IDF Cosine Similarity with IDF weights [Slides 27-31]
3. Pattern & Substring Measures:
   - Ratcliff-Obershelp Similarity (Longest common subsegment) [Slides 33-34]
4. Phonetic Measures:
   - Soundex Phonetic Encoding & Distance [Slides 36-37]
"""
import math
import re
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# 1. SEQUENCE-BASED SIMILARITY MEASURES
# ─────────────────────────────────────────────────────────────────────────────

def edit_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein Edit Distance using Dynamic Programming (O(m*n)).
    Reference: Week 6-8 Slides 16-19.
    Operations allowed: Insert, Delete, Substitute (cost 1 each).
    """
    m, n = len(s1), len(s2)
    # DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )
    return dp[m][n]


def normalized_edit_similarity(s1: str, s2: str) -> float:
    """Normalized edit similarity in range [0, 1]."""
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = edit_distance(s1, s2)
    return round(1.0 - (dist / max_len), 4)


def jaro_similarity(s1: str, s2: str) -> float:
    """
    Compute Jaro Similarity score in range [0, 1].
    Reference: Week 6-8 Slides 20-21.
    Formula: sim_j = (1/3) * (m/|s1| + m/|s2| + (m - t)/m)
    where m = matching characters within window floor(max(|s1|, |s2|) / 2) - 1,
    and t = number of transpositions / 2.
    """
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    t = transpositions / 2.0
    jaro = (matches / len1 + matches / len2 + (matches - t) / matches) / 3.0
    return round(jaro, 4)


def jaro_winkler_similarity(s1: str, s2: str, prefix_scale: float = 0.1, max_prefix: int = 4) -> float:
    """
    Compute Jaro-Winkler Similarity score in range [0, 1].
    Reference: Week 6-8 Slide 22.
    Formula: sim_jw = sim_j + l * p * (1 - sim_j)
    where l is length of common prefix up to max_prefix (usually 4),
    and p is scaling factor (standard 0.1).
    """
    j_sim = jaro_similarity(s1, s2)
    # Common prefix length up to max_prefix
    prefix_len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            prefix_len += 1
            if prefix_len == max_prefix:
                break
        else:
            break

    jw_sim = j_sim + prefix_len * prefix_scale * (1.0 - j_sim)
    return round(min(1.0, max(0.0, jw_sim)), 4)


# ─────────────────────────────────────────────────────────────────────────────
# 2. SET-BASED SIMILARITY MEASURES
# ─────────────────────────────────────────────────────────────────────────────

def get_character_qgrams(s: str, q: int = 3, padding: bool = True) -> List[str]:
    """
    Generate character-level q-grams from a string.
    Reference: Week 6-8 Slides 45-46.
    Example: 'UP32' with q=2 and padding -> ['#U', 'UP', 'P3', '32', '2$']
    """
    if padding:
        padded = f"{'#' * (q - 1)}{s}{'$' * (q - 1)}"
    else:
        padded = s
    if len(padded) < q:
        return [padded]
    return [padded[i:i + q] for i in range(len(padded) - q + 1)]


def overlap_coefficient(set1: Set[str], set2: Set[str]) -> float:
    """
    Compute Overlap Coefficient: |set1 ∩ set2| / min(|set1|, |set2|).
    Reference: Week 6-8 Slide 25.
    """
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    min_size = min(len(set1), len(set2))
    if min_size == 0:
        return 0.0
    return round(intersection / min_size, 4)


def jaccard_similarity(tokens1: Set[str], tokens2: Set[str]) -> float:
    """
    Compute Jaccard Similarity: |tokens1 ∩ tokens2| / |tokens1 ∪ tokens2|.
    Reference: Week 6-8 Slide 26.
    """
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    if union == 0:
        return 0.0
    return round(intersection / union, 4)


def tfidf_similarity(s1: str, s2: str, idf_weights: Optional[Dict[str, float]] = None, q: int = 3) -> float:
    """
    Compute TF-IDF Cosine Similarity over q-grams.
    Reference: Week 6-8 Slides 27-31.
    """
    q1 = get_character_qgrams(s1, q=q)
    q2 = get_character_qgrams(s2, q=q)
    c1 = Counter(q1)
    c2 = Counter(q2)
    all_tokens = set(c1.keys()).union(set(c2.keys()))

    if not all_tokens:
        return 1.0

    # Default unit IDF if no weights provided
    dot_product = 0.0
    norm1 = 0.0
    norm2 = 0.0

    for token in all_tokens:
        idf = idf_weights.get(token, 1.0) if idf_weights else 1.0
        w1 = c1.get(token, 0) * idf
        w2 = c2.get(token, 0) * idf
        dot_product += w1 * w2
        norm1 += w1 * w1
        norm2 += w2 * w2

    if norm1 == 0 or norm2 == 0:
        return 0.0
    cosine = dot_product / (math.sqrt(norm1) * math.sqrt(norm2))
    return round(cosine, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 3. RATCLIFF-OBERSHELP SIMILARITY
# ─────────────────────────────────────────────────────────────────────────────

def ratcliff_obershelp_similarity(s1: str, s2: str) -> float:
    """
    Compute Ratcliff-Obershelp similarity based on longest common subsegments.
    Reference: Week 6-8 Slides 33-34.
    Formula: 2 * M / (|s1| + |s2|), where M is total matched characters in common subsegments.
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    def find_lcs(a: str, b: str) -> Tuple[int, int, int]:
        """Find longest common contiguous substring: returns (start_a, start_b, length)."""
        best_len, best_i, best_j = 0, 0, 0
        len_a, len_b = len(a), len(b)
        dp = [[0] * (len_b + 1) for _ in range(len_a + 1)]
        for i in range(1, len_a + 1):
            for j in range(1, len_b + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    if dp[i][j] > best_len:
                        best_len = dp[i][j]
                        best_i = i - best_len
                        best_j = j - best_len
        return best_i, best_j, best_len

    def count_matches(a: str, b: str) -> int:
        if not a or not b:
            return 0
        i, j, length = find_lcs(a, b)
        if length == 0:
            return 0
        total = length
        # Recurse left
        total += count_matches(a[:i], b[:j])
        # Recurse right
        total += count_matches(a[i + length:], b[j + length:])
        return total

    matched_chars = count_matches(s1, s2)
    score = (2.0 * matched_chars) / (len(s1) + len(s2))
    return round(score, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 4. SOUNDEX PHONETIC MEASURE
# ─────────────────────────────────────────────────────────────────────────────

def soundex(s: str) -> str:
    """
    Compute Soundex phonetic code for a string.
    Reference: Week 6-8 Slides 36-37.
    Standard code: 1 letter + 3 digits (e.g., 'U132').
    """
    s = re.sub(r'[^A-Z]', '', s.upper())
    if not s:
        return "0000"

    first_char = s[0]
    # Mapping table
    mapping = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',
    }

    encoded = [first_char]
    prev_code = mapping.get(first_char, '')

    for char in s[1:]:
        code = mapping.get(char, '')
        if code and code != prev_code:
            encoded.append(code)
            prev_code = code
        elif not code:
            prev_code = ''  # vowels/W/H reset adjacent duplicates

    # Pad or truncate to 4 chars
    digits = ''.join(encoded[1:])
    digits = (digits + '000')[:3]
    return f"{first_char}{digits}"


def soundex_similarity(s1: str, s2: str) -> float:
    """Phonetic agreement between two strings using Soundex codes."""
    code1 = soundex(s1)
    code2 = soundex(s2)
    if code1 == code2:
        return 1.0
    # Match prefixes
    matches = sum(1 for c1, c2 in zip(code1, code2) if c1 == c2)
    return round(matches / 4.0, 4)


# ─────────────────────────────────────────────────────────────────────────────
# 5. ALL-IN-ONE SIMILARITY VECTOR
# ─────────────────────────────────────────────────────────────────────────────

def compute_all_metrics(s1: str, s2: str, idf_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Compute all Week 6-8 similarity metrics between two strings.
    Returns comprehensive metrics dictionary for explainability and feature vector generation.
    """
    qgrams1 = set(get_character_qgrams(s1, q=3))
    qgrams2 = set(get_character_qgrams(s2, q=3))

    edit_dist = edit_distance(s1, s2)
    norm_edit = normalized_edit_similarity(s1, s2)
    jaro = jaro_similarity(s1, s2)
    jaro_winkler = jaro_winkler_similarity(s1, s2)
    jaccard_q3 = jaccard_similarity(qgrams1, qgrams2)
    overlap = overlap_coefficient(qgrams1, qgrams2)
    tfidf = tfidf_similarity(s1, s2, idf_weights=idf_weights, q=3)
    ro = ratcliff_obershelp_similarity(s1, s2)
    phonetic = soundex_similarity(s1, s2)

    return {
        "edit_distance": float(edit_dist),
        "normalized_edit_sim": norm_edit,
        "jaro_sim": jaro,
        "jaro_winkler_sim": jaro_winkler,
        "jaccard_q3": jaccard_q3,
        "overlap_coeff": overlap,
        "tfidf_sim": tfidf,
        "ratcliff_obershelp_sim": ro,
        "soundex_sim": phonetic,
    }
