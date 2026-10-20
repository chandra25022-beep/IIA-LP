"""
Data Integration Under Uncertainty Engine
Based on IIA Course Notes:
- Week 2 Slide 24: Straight-Through Processing (STP) & Uncertainty Routing
- Week 6-8 Slides 68-87: Modern ML/DL Matching, Feature Vector, Calibration & Decision Routing

Features:
1. Multi-Signal Feature Vector Extraction phi(r_i, r_j) [Slide 71]
2. OCR Confusion Likelihood Modeling (P(ocr_error | char_pair))
3. Probability Calibration [Slide 81] converting raw scores to P(Match | Evidence)
4. Three-Tier Uncertainty Decision Policy:
   - AUTO_MERGE (p >= 0.85): Straight-through high-confidence integration
   - UNCERTAIN_REVIEW (0.50 <= p < 0.85): Ambiguous/partial evidence, ranked candidate hypotheses
   - REJECT (p < 0.50): Independent novel/untracked entity
5. Probabilistic Conflict Resolution & Truth Discovery
   - Estimates P(Attribute = V | Source_Evidence) using source reliability weights & sensor confidences
"""
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from ..indexing.string_metrics import (
    edit_distance, normalized_edit_similarity,
    jaro_winkler_similarity, jaccard_similarity,
    soundex_similarity, get_character_qgrams
)


# Common OCR misrecognition transition probabilities for license plates
# P(read_char | true_char)
OCR_TRANSITION_PROBS: Dict[Tuple[str, str], float] = {
    ("0", "O"): 0.85, ("O", "0"): 0.85,
    ("0", "D"): 0.65, ("D", "0"): 0.65,
    ("0", "Q"): 0.60, ("Q", "0"): 0.60,
    ("1", "I"): 0.90, ("I", "1"): 0.90,
    ("1", "L"): 0.70, ("L", "1"): 0.70,
    ("8", "B"): 0.85, ("B", "8"): 0.85,
    ("5", "S"): 0.85, ("S", "5"): 0.85,
    ("2", "Z"): 0.80, ("Z", "2"): 0.80,
    ("6", "G"): 0.75, ("G", "6"): 0.75,
    ("4", "A"): 0.70, ("A", "4"): 0.70,
    ("H", "A"): 0.60, ("A", "H"): 0.60,
    ("C", "G"): 0.55, ("G", "C"): 0.55,
}

# Base reliability weights per source organization (IIA Truth Discovery)
SOURCE_RELIABILITY_WEIGHTS: Dict[str, float] = {
    "registration": 0.95,   # Official Government RTO registry — authoritative for identity & chassis
    "insurance":    0.90,   # National Insurance Registry — authoritative for policy dates & status
    "theft":        0.92,   # Police Crime Records Bureau — authoritative for criminal FIRs & stolen state
    "capture":      0.82,   # Roadside ANPR Camera — real-time sensor observation subject to weather/lighting
    "ministry":     0.88,   # Ministry of Transportation — authoritative for national alerts
}


class UncertaintyEngine:
    """
    Core engine for reasoning under uncertainty during Information Integration.
    """

    def __init__(self):
        # Operational decision thresholds (Week 6-8 Slide 81)
        self.tau_auto = 0.85     # High confidence auto-merge
        self.tau_review = 0.50   # Review / candidate presentation band

    def compute_ocr_confusion_likelihood(self, s1: str, s2: str) -> float:
        """
        Calculates probability that differences between s1 and s2 are standard OCR scanner errors.
        Returns a score in [0, 1].
        """
        if s1 == s2:
            return 1.0
        if len(s1) != len(s2):
            # Length mismatch - penalize slightly
            len_diff = abs(len(s1) - len(s2))
            base = max(0.0, 1.0 - (len_diff * 0.3))
            return base

        diff_count = 0
        prob_sum = 0.0

        for c1, c2 in zip(s1, s2):
            if c1 != c2:
                diff_count += 1
                trans_prob = OCR_TRANSITION_PROBS.get((c1, c2), OCR_TRANSITION_PROBS.get((c2, c1), 0.10))
                prob_sum += trans_prob

        if diff_count == 0:
            return 1.0
        # Average probability across mutated characters
        avg_trans_prob = prob_sum / diff_count
        # Penalize if too many characters mutated
        mutation_penalty = max(0.0, 1.0 - (diff_count - 1) * 0.25)
        return round(avg_trans_prob * mutation_penalty, 4)

    def extract_feature_vector(
        self,
        query_plate: str,
        target_plate: str,
        sensor_confidence: float = 0.90,
        query_metadata: Optional[Dict[str, Any]] = None,
        target_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Extract multi-signal feature vector phi(r_i, r_j) [Week 6-8 Slide 71].
        Combines linguistic, phonetic, OCR confusion, sensor confidence, and semantic attributes.
        """
        s1 = query_plate.upper().strip()
        s2 = target_plate.upper().strip()

        # 1. Linguistic similarities
        jw = jaro_winkler_similarity(s1, s2)
        norm_edit = normalized_edit_similarity(s1, s2)
        q1 = set(get_character_qgrams(s1, q=3))
        q2 = set(get_character_qgrams(s2, q=3))
        jacc_q = jaccard_similarity(q1, q2)

        # 2. Phonetic agreement
        phonetic = soundex_similarity(s1, s2)

        # 3. Domain OCR confusion probability
        ocr_lik = self.compute_ocr_confusion_likelihood(s1, s2)

        # 4. Attribute agreement (if metadata provided)
        attr_sim = 1.0
        if query_metadata and target_metadata:
            matches = 0
            total_attrs = 0
            for key in ["vehicle_type", "color", "make"]:
                v1 = query_metadata.get(key)
                v2 = target_metadata.get(key)
                if v1 and v2:
                    total_attrs += 1
                    if str(v1).upper() == str(v2).upper():
                        matches += 1
            if total_attrs > 0:
                attr_sim = matches / total_attrs

        return {
            "jaro_winkler": jw,
            "normalized_edit": norm_edit,
            "jaccard_qgrams": jacc_q,
            "soundex_phonetic": phonetic,
            "ocr_confusion_prob": ocr_lik,
            "sensor_confidence": sensor_confidence,
            "attribute_agreement": attr_sim,
        }

    def calibrate_probability(self, features: Dict[str, float]) -> float:
        """
        Calibrates raw feature vector into a posterior match probability P(Match | Evidence)
        using logistic sigmoid calibration with domain-learned feature weights.
        Reference: Week 6-8 Slide 81.
        """
        # Learned weights reflecting signal importance
        w = {
            "jaro_winkler": 2.2,
            "normalized_edit": 2.0,
            "jaccard_qgrams": 1.5,
            "ocr_confusion_prob": 1.8,
            "soundex_phonetic": 0.8,
            "sensor_confidence": 1.0,
            "attribute_agreement": 1.2,
        }
        bias = -4.5  # Prior favoring non-match on completely distinct strings

        logit = bias + sum(features.get(k, 0.0) * weight for k, weight in w.items())
        # Sigmoid function
        prob = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, logit))))
        return round(prob, 4)

    def evaluate_match_under_uncertainty(
        self,
        query_plate: str,
        candidate_plates: List[Dict[str, Any]],
        sensor_confidence: float = 0.90,
        query_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Performs full uncertainty evaluation and decision routing on retrieved candidates.
        Categorizes into:
        - AUTO_MERGE (p >= 0.85)
        - UNCERTAIN_REVIEW (0.50 <= p < 0.85)
        - REJECT (p < 0.50)
        """
        scored_candidates = []

        for cand in candidate_plates:
            target_plate = cand["plate"]
            target_meta = cand.get("metadata", {})
            features = self.extract_feature_vector(
                query_plate, target_plate,
                sensor_confidence=sensor_confidence,
                query_metadata=query_metadata,
                target_metadata=target_meta
            )
            prob_match = self.calibrate_probability(features)

            # Determine candidate status
            if prob_match >= self.tau_auto:
                tier = "AUTO_MERGE"
                tier_description = "High confidence match — automated straight-through integration."
            elif prob_match >= self.tau_review:
                tier = "UNCERTAIN_REVIEW"
                tier_description = "Ambiguous / Partial match — candidate routed to human reviewer or ranked queue."
            else:
                tier = "REJECT"
                tier_description = "Low probability match — treated as distinct candidate."

            scored_candidates.append({
                "plate": target_plate,
                "source": cand.get("source", "unknown"),
                "record_id": cand.get("record_id", target_plate),
                "match_probability": prob_match,
                "decision_tier": tier,
                "tier_description": tier_description,
                "features": features,
                "raw_candidate": cand
            })

        # Sort by match probability descending
        scored_candidates.sort(key=lambda x: x["match_probability"], reverse=True)

        best_candidate = scored_candidates[0] if scored_candidates else None
        overall_decision = "NO_CANDIDATES"
        if best_candidate:
            overall_decision = best_candidate["decision_tier"]

        return {
            "query_plate": query_plate,
            "overall_decision": overall_decision,
            "best_match": best_candidate,
            "candidate_hypotheses": scored_candidates[:5],
            "total_candidates_evaluated": len(scored_candidates),
            "thresholds": {
                "auto_merge_threshold": self.tau_auto,
                "review_threshold": self.tau_review
            }
        }

    def resolve_conflicts_probabilistically(
        self,
        attribute_name: str,
        source_values: Dict[str, Any],
        camera_confidence: float = 0.90
    ) -> Dict[str, Any]:
        """
        Probabilistic Truth Discovery when independent sources disagree.
        Example: Traffic Camera reports 'WHITE' (conf=0.96), RTO Registration reports 'SILVER'.
        Calculates source evidence posterior distribution: P(True_Value = v | Sources).
        """
        if not source_values:
            return {"resolved_value": None, "probabilities": {}, "has_conflict": False}

        unique_values = set(v for v in source_values.values() if v is not None)
        if len(unique_values) <= 1:
            val = next(iter(unique_values)) if unique_values else None
            return {
                "resolved_value": val,
                "probabilities": {str(val): 1.0} if val else {},
                "has_conflict": False,
                "explanation": "All sources agree unanimously."
            }

        # Multi-source conflict: compute evidence weights
        scores: Dict[str, float] = defaultdict(float)

        for source_name, val in source_values.items():
            if val is None:
                continue
            base_rel = SOURCE_RELIABILITY_WEIGHTS.get(source_name, 0.70)
            if source_name == "capture":
                effective_weight = base_rel * camera_confidence
            else:
                effective_weight = base_rel
            scores[str(val)] += effective_weight

        # Normalize to probability distribution
        total_score = sum(scores.values())
        prob_dist = {
            val: round(score / total_score, 4)
            for val, score in scores.items()
        }

        # Value with maximum a posteriori (MAP) probability
        best_val = max(prob_dist.items(), key=lambda x: x[1])[0]

        return {
            "resolved_value": best_val,
            "probabilities": prob_dist,
            "has_conflict": True,
            "confidence": prob_dist[best_val],
            "competing_sources": {src: str(val) for src, val in source_values.items() if val is not None},
            "explanation": f"Source conflict resolved probabilistically via Truth Discovery. MAP choice: '{best_val}' with P={prob_dist[best_val]:.2f}."
        }
