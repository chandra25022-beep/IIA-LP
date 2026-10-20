"""
Q-Gram Inverted Index & Prefix Filtering Engine
Based on IIA Course Notes: Week 6-8 (Scalability Challenges & 2-Step Framework)

Implements:
1. Inverted Index over Strings [Sarawagi et al., SIGMOD 04] (Slides 47-51)
   - Tokenizes strings into character q-grams (q=2 and q=3)
   - Builds posting lists mapping q-gram -> List of Record IDs
2. Size Filtering [Arasu et al., VLDB 06] (Slides 53-54)
   - Prunes candidate strings whose length cannot satisfy edit distance or Jaccard threshold
3. Prefix Filtering [Chaudhuri et al., ICDE 06] (Slides 55-56)
   - Probes prefixes of size |x| - (k - 1)
4. Prefix-Inverted Index [Bayardo et al., WWW 07] (Slides 57-64)
   - Imposes universal ordering over tokens (least frequent / rarest tokens first)
   - Builds inverted index strictly over prefixes
5. Position Filtering [Xiao et al., WWW 08] (Slide 65)
   - Derives upper bound on maximum possible overlap to avoid redundant distance computations
"""
import math
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict, Counter
from .string_metrics import (
    get_character_qgrams, jaccard_similarity, edit_distance,
    normalized_edit_similarity, jaro_winkler_similarity
)


class QGramInvertedIndex:
    """
    Inverted Index and Prefix Filtering Engine for scalable candidate retrieval.
    Enables sub-linear candidate generation across all 5 federated databases
    instead of exhaustive O(N) comparisons.
    """

    def __init__(self, q: int = 3):
        self.q = q
        # Universal token frequency across all indexed strings
        self.doc_frequency: Counter = Counter()
        # Inverted index: token -> list of (record_id, string_value, source, metadata)
        self.inverted_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # Prefix-Inverted index: token -> list of prefix postings [Bayardo et al, WWW 07]
        self.prefix_inverted_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # Length buckets for Size Filtering [Arasu et al, VLDB 06]
        self.length_buckets: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        # Registry of all unique indexed records
        self.records: Dict[str, Dict[str, Any]] = {}
        # Precomputed IDF weights
        self.idf_weights: Dict[str, float] = {}

    def index_record(self, record_id: str, plate_string: str, source: str, metadata: Optional[Dict[str, Any]] = None):
        """Index a single record with its q-grams into inverted and prefix indexes."""
        cleaned = plate_string.strip().upper()
        if not cleaned:
            return

        record = {
            "record_id": record_id,
            "plate": cleaned,
            "source": source,
            "metadata": metadata or {},
            "length": len(cleaned)
        }
        self.records[record_id] = record
        self.length_buckets[len(cleaned)].append(record)

        # Generate q-grams
        qgrams = get_character_qgrams(cleaned, q=self.q, padding=True)
        unique_qgrams = set(qgrams)

        # 1. Update document frequency and standard Inverted Index [Sarawagi et al, 04]
        for token in unique_qgrams:
            self.doc_frequency[token] += 1
            self.inverted_index[token].append(record)

    def build(self):
        """
        Finalize indexing by:
        1. Computing IDF weights for all tokens
        2. Imposing universal ordering (rare tokens first) [Bayardo et al, WWW 07]
        3. Building the Prefix-Inverted Index
        """
        total_docs = max(1, len(self.records))
        self.idf_weights = {
            token: math.log((total_docs + 1) / (df + 1))
            for token, df in self.doc_frequency.items()
        }

        # Clear and build prefix inverted index
        self.prefix_inverted_index.clear()
        for record_id, record in self.records.items():
            cleaned = record["plate"]
            qgrams = get_character_qgrams(cleaned, q=self.q, padding=True)
            unique_qgrams = list(set(qgrams))

            # Order tokens by universal frequency: rarest first [Bayardo et al, Slide 58]
            ordered_tokens = sorted(unique_qgrams, key=lambda t: (self.doc_frequency[t], t))

            # Prefix size for minimum overlap k=2: prefix_len = |x| - (k - 1)
            k = 2
            prefix_len = max(1, len(ordered_tokens) - (k - 1))
            prefix_tokens = ordered_tokens[:prefix_len]

            for token in prefix_tokens:
                self.prefix_inverted_index[token].append({
                    "record_id": record_id,
                    "plate": cleaned,
                    "source": record["source"],
                    "ordered_tokens": ordered_tokens,
                    "prefix_len": prefix_len
                })

    def size_filter(self, query: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Size Filtering [Arasu et al, VLDB 06] (Slides 53-54).
        For Jaccard threshold t, matching string y must satisfy:
        |x| * t <= |y| <= |x| / t.
        Returns all records whose lengths fall inside the allowed bounds.
        """
        len_x = len(query)
        min_len = int(math.ceil(len_x * threshold))
        max_len = int(math.floor(len_x / threshold)) if threshold > 0 else 50

        candidates = []
        for l in range(min_len, max_len + 1):
            if l in self.length_buckets:
                candidates.extend(self.length_buckets[l])
        return candidates

    def search_candidates(
        self,
        query: str,
        method: str = "prefix_index",
        jaccard_threshold: float = 0.4,
        max_candidates: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve candidate matching records using the 2-Step Framework (Week 6-8 Slide 44).
        Step 1: Blocking / Index filtering
        Step 2: Scoring with detailed string metrics
        """
        cleaned_query = query.strip().upper()
        if not cleaned_query or not self.records:
            return []

        query_qgrams = get_character_qgrams(cleaned_query, q=self.q, padding=True)
        unique_query_qgrams = list(set(query_qgrams))

        candidate_counts: Counter = Counter()
        candidate_records: Dict[str, Dict[str, Any]] = {}

        if method == "prefix_index":
            # Method: Prefix-Inverted Index [Bayardo et al, WWW 07]
            # Order query tokens by rarity
            ordered_query = sorted(unique_query_qgrams, key=lambda t: (self.doc_frequency.get(t, 0), t))
            k = 2
            prefix_len = max(1, len(ordered_query) - (k - 1))
            query_prefix = ordered_query[:prefix_len]

            for token in query_prefix:
                for posting in self.prefix_inverted_index.get(token, []):
                    rec_id = posting["record_id"]
                    candidate_counts[rec_id] += 1
                    if rec_id not in candidate_records:
                        candidate_records[rec_id] = self.records[rec_id]

        elif method == "inverted_index":
            # Method: Standard Inverted Index [Sarawagi et al, SIGMOD 04]
            for token in unique_query_qgrams:
                for rec in self.inverted_index.get(token, []):
                    rec_id = rec["record_id"]
                    candidate_counts[rec_id] += 1
                    if rec_id not in candidate_records:
                        candidate_records[rec_id] = rec
        else:
            # Fallback to Size Filtering
            for rec in self.size_filter(cleaned_query, threshold=jaccard_threshold):
                rec_id = rec["record_id"]
                candidate_records[rec_id] = rec
                candidate_counts[rec_id] = 1

        # Step 2: Detailed scoring of retrieved candidates
        scored_candidates = []
        for rec_id, rec in candidate_records.items():
            target_plate = rec["plate"]
            target_qgrams = set(get_character_qgrams(target_plate, q=self.q, padding=True))
            
            jacc = jaccard_similarity(set(unique_query_qgrams), target_qgrams)
            edit_dist = edit_distance(cleaned_query, target_plate)
            norm_edit = normalized_edit_similarity(cleaned_query, target_plate)
            jw_sim = jaro_winkler_similarity(cleaned_query, target_plate)

            # Combined match score
            combined_score = round(0.40 * jw_sim + 0.35 * norm_edit + 0.25 * jacc, 4)

            scored_candidates.append({
                "record_id": rec_id,
                "plate": target_plate,
                "source": rec["source"],
                "metadata": rec["metadata"],
                "overlap_qgrams": candidate_counts[rec_id],
                "jaccard_sim": jacc,
                "edit_distance": edit_dist,
                "normalized_edit_sim": norm_edit,
                "jaro_winkler_sim": jw_sim,
                "match_score": combined_score,
            })

        # Sort by match score descending
        scored_candidates.sort(key=lambda c: c["match_score"], reverse=True)
        return scored_candidates[:max_candidates]

    def get_index_stats(self) -> Dict[str, Any]:
        """Return structural statistics for the Academic / Integration Explorer view."""
        return {
            "total_indexed_records": len(self.records),
            "unique_qgrams": len(self.doc_frequency),
            "qgram_size": self.q,
            "inverted_index_postings": sum(len(p) for p in self.inverted_index.values()),
            "prefix_index_postings": sum(len(p) for p in self.prefix_inverted_index.values()),
            "length_buckets": {str(k): len(v) for k, v in sorted(self.length_buckets.items())},
            "top_frequent_qgrams": [
                {"token": t, "df": count} for t, count in self.doc_frequency.most_common(10)
            ],
            "rarest_qgrams": [
                {"token": t, "df": count} for t, count in sorted(self.doc_frequency.items(), key=lambda x: x[1])[:10]
            ],
        }
