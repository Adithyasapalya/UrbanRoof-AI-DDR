"""
==========================================================
UrbanRoof AI DDR Generator

Semantic Matching Engine

Author: Adithya Sapalya
==========================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

from modules.knowledge_base import (
    KnowledgeBase,
    Observation
)

from config import (
    EMBEDDING_MODEL,
    INSPECTION_EMBEDDINGS,
    THERMAL_EMBEDDINGS,
    INSPECTION_INDEX,
    THERMAL_INDEX,
    MATCHES_FILE,
    INDEX_METADATA,
    TOP_K,
    AUTO_MATCH_THRESHOLD,
    REVIEW_THRESHOLD,
    KEYWORD_WEIGHT,
    SEMANTIC_WEIGHT,
)

# ==========================================================
# Match Object
# ==========================================================

@dataclass
class Match:

    inspection_id: int

    thermal_id: int

    area: str

    keyword_score: float

    semantic_score: float

    final_score: float

    match_type: str

    review_required: bool = False


# ==========================================================
# Semantic Matcher
# ==========================================================

class SemanticMatcher:

    def __init__(self):

        print("\nLoading SentenceTransformer...")

        self.model = SentenceTransformer(
            EMBEDDING_MODEL
        )

        self.dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        print(
            f"Embedding Dimension : {self.dimension}"
        )

        self.matches: List[Match] = []

    # --------------------------------------------------------
    # Observation -> Text
    # --------------------------------------------------------

    def observation_to_text(
        self,
        obs: Observation
    ) -> str:

        return f"""
Area:
{obs.area}

Issue:
{obs.issue}

Description:
{obs.description}

Evidence:
{obs.source_evidence}

Severity:
{obs.severity}

Recommendation:
{obs.recommendation}
"""

    # --------------------------------------------------------
    # Create Embeddings
    # --------------------------------------------------------

    def create_embeddings(
        self,
        observations: List[Observation]
    ) -> np.ndarray:

        if len(observations) == 0:

            return np.empty(
                (0, self.dimension),
                dtype=np.float32
            )

        texts = [

            self.observation_to_text(obs)

            for obs in observations

        ]

        print(
            f"\nGenerating {len(texts)} embeddings..."
        )

        embeddings = self.model.encode(

            texts,

            convert_to_numpy=True,

            normalize_embeddings=True,

            show_progress_bar=True

        )

        return embeddings.astype(np.float32)

    # --------------------------------------------------------
    # Save Embeddings
    # --------------------------------------------------------

    def save_embeddings(

        self,

        inspection_embeddings: np.ndarray,

        thermal_embeddings: np.ndarray

    ):

        np.save(

            str(INSPECTION_EMBEDDINGS),

            inspection_embeddings

        )

        np.save(

            str(THERMAL_EMBEDDINGS),

            thermal_embeddings

        )

        print("Inspection embeddings saved.")

        print("Thermal embeddings saved.")

    # --------------------------------------------------------
    # Load Embeddings
    # --------------------------------------------------------

    def load_embeddings(self):

        inspection = np.load(

            str(INSPECTION_EMBEDDINGS)

        )

        thermal = np.load(

            str(THERMAL_EMBEDDINGS)

        )

        return inspection, thermal

    # --------------------------------------------------------
    # Build FAISS Index
    # --------------------------------------------------------

    def build_index(

        self,

        embeddings: np.ndarray

    ):

        if len(embeddings) == 0:

            return None

        index = faiss.IndexFlatIP(

            embeddings.shape[1]

        )

        index.add(

            embeddings

        )

        return index

    # --------------------------------------------------------
    # Save Index
    # --------------------------------------------------------

    def save_index(

        self,

        inspection_index,

        thermal_index

    ):

        if inspection_index is not None:

            faiss.write_index(

                inspection_index,

                str(INSPECTION_INDEX)

            )

        if thermal_index is not None:

            faiss.write_index(

                thermal_index,

                str(THERMAL_INDEX)

            )

        print("FAISS indexes saved.")

    # --------------------------------------------------------
    # Keyword Extraction
    # --------------------------------------------------------

    def extract_keywords(

        self,

        text: str

    ):

        stopwords = {

            "the",
            "a",
            "an",
            "of",
            "is",
            "are",
            "and",
            "to",
            "near",
            "on",
            "at",
            "in",
            "for",
            "with"

        }

        words = []

        for word in text.lower().split():

            word = "".join(

                c

                for c in word

                if c.isalnum()

            )

            if (

                len(word) > 2

                and

                word not in stopwords

            ):

                words.append(word)

        return set(words)
    # --------------------------------------------------------
    # Keyword Similarity
    # --------------------------------------------------------

    def keyword_similarity(

        self,

        obs1: Observation,

        obs2: Observation

    ) -> float:

        words1 = self.extract_keywords(

            self.observation_to_text(obs1)

        )

        words2 = self.extract_keywords(

            self.observation_to_text(obs2)

        )

        if len(words1) == 0:

            return 0.0

        overlap = words1.intersection(

            words2

        )

        union = words1.union(

            words2

        )

        return len(overlap) / max(

            len(union),

            1

        )

    # --------------------------------------------------------
    # Combined Score
    # --------------------------------------------------------

    def combined_score(

        self,

        semantic_score: float,

        keyword_score: float

    ) -> float:

        return (

            semantic_score * SEMANTIC_WEIGHT

            +

            keyword_score * KEYWORD_WEIGHT

        )

    # --------------------------------------------------------
    # Match Classification
    # --------------------------------------------------------

    def classify_match(

        self,

        score: float

    ) -> str:

        if score >= AUTO_MATCH_THRESHOLD:

            return "AUTO"

        elif score >= REVIEW_THRESHOLD:

            return "REVIEW"

        else:

            return "IGNORE"

    # --------------------------------------------------------
    # Find Matches
    # --------------------------------------------------------

    def find_matches(

        self,

        inspection_observations: List[Observation],

        thermal_observations: List[Observation],

        inspection_embeddings: np.ndarray,

        thermal_embeddings: np.ndarray

    ) -> List[Match]:

        print("\nSearching for semantic matches...")

        if len(inspection_observations) == 0:

            print("No inspection observations found.")

            return []

        if len(thermal_observations) == 0:

            print("No thermal observations found.")

            return []

        thermal_index = self.build_index(

            thermal_embeddings

        )

        if thermal_index is None:

            return []

        distances, indices = thermal_index.search(

            inspection_embeddings,

            TOP_K

        )

        matches = []

        used_thermal = set()

        for inspection_idx in range(

            len(inspection_observations)

        ):

            inspection = inspection_observations[

                inspection_idx

            ]

            best_match = None

            best_score = -1.0

            for rank in range(TOP_K):

                thermal_idx = int(

                    indices[inspection_idx][rank]

                )

                if thermal_idx == -1:

                    continue

                if thermal_idx >= len(

                    thermal_observations

                ):

                    continue

                if thermal_idx in used_thermal:

                    continue

                thermal = thermal_observations[

                    thermal_idx

                ]

                semantic_score = float(

                    distances[inspection_idx][rank]

                )

                keyword_score = self.keyword_similarity(

                    inspection,

                    thermal

                )

                final_score = self.combined_score(

                    semantic_score,

                    keyword_score

                )

                if final_score > best_score:

                    best_score = final_score

                    best_match = (

                        thermal_idx,

                        semantic_score,

                        keyword_score,

                        final_score

                    )

            if best_match is None:

                continue

            (

                thermal_idx,

                semantic_score,

                keyword_score,

                final_score

            ) = best_match

            used_thermal.add(

                thermal_idx

            )

            match_type = self.classify_match(

                final_score

            )

            match = Match(

                inspection_id=inspection.id,

                thermal_id=thermal_observations[
                    thermal_idx
                ].id,

                area=inspection.area,

                keyword_score=keyword_score,

                semantic_score=semantic_score,

                final_score=final_score,

                match_type=match_type,

                review_required=(

                    match_type == "REVIEW"

                )

            )

            matches.append(

                match

            )

        self.matches = matches

        print(

            f"Found {len(matches)} semantic matches."

        )

        return matches
    # --------------------------------------------------------
    # Update Knowledge Base
    # --------------------------------------------------------

    def update_knowledge_base(

        self,

        kb: KnowledgeBase

    ) -> KnowledgeBase:

        for match in self.matches:

            kb.link_observations(

                inspection_id=match.inspection_id,

                thermal_id=match.thermal_id,

                similarity=match.final_score

            )

        print(

            f"Linked {len(self.matches)} observations."

        )

        return kb

    # --------------------------------------------------------
    # Save Matches
    # --------------------------------------------------------

    def save_matches(self):

        data = []

        for match in self.matches:

            data.append({

                "inspection_id": match.inspection_id,

                "thermal_id": match.thermal_id,

                "area": match.area,

                "keyword_score": round(

                    match.keyword_score,

                    4

                ),

                "semantic_score": round(

                    match.semantic_score,

                    4

                ),

                "final_score": round(

                    match.final_score,

                    4

                ),

                "match_type": match.match_type,

                "review_required": match.review_required

            })

        with open(

            MATCHES_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                data,

                f,

                indent=4

            )

        print(

            f"Saved {len(data)} matches."

        )

    # --------------------------------------------------------
    # Save Metadata
    # --------------------------------------------------------

    def save_metadata(

        self,

        inspection_embeddings,

        thermal_embeddings

    ):

        metadata = {

            "embedding_model": EMBEDDING_MODEL,

            "embedding_dimension": self.dimension,

            "inspection_vectors": len(

                inspection_embeddings

            ),

            "thermal_vectors": len(

                thermal_embeddings

            ),

            "top_k": TOP_K,

            "semantic_weight": SEMANTIC_WEIGHT,

            "keyword_weight": KEYWORD_WEIGHT,

            "auto_threshold": AUTO_MATCH_THRESHOLD,

            "review_threshold": REVIEW_THRESHOLD

        }

        with open(

            INDEX_METADATA,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                metadata,

                f,

                indent=4

            )

        print(

            "Metadata saved."

        )

    # --------------------------------------------------------
    # Full Pipeline
    # --------------------------------------------------------

    def run(

        self,

        kb: KnowledgeBase

    ) -> KnowledgeBase:

        print()

        print("=" * 60)

        print("SEMANTIC MATCHING")

        print("=" * 60)

        inspection = kb.get_inspection_observations()

        thermal = kb.get_thermal_observations()

        print(

            f"Inspection Findings : {len(inspection)}"

        )

        print(

            f"Thermal Findings    : {len(thermal)}"

        )

        if len(inspection) == 0:

            print(

                "No inspection observations."

            )

            return kb

        if len(thermal) == 0:

            print(

                "No thermal observations."

            )

            return kb

        inspection_embeddings = self.create_embeddings(

            inspection

        )

        thermal_embeddings = self.create_embeddings(

            thermal

        )

        self.save_embeddings(

            inspection_embeddings,

            thermal_embeddings

        )

        inspection_index = self.build_index(

            inspection_embeddings

        )

        thermal_index = self.build_index(

            thermal_embeddings

        )

        self.save_index(

            inspection_index,

            thermal_index

        )

        self.save_metadata(

            inspection_embeddings,

            thermal_embeddings

        )

        self.find_matches(

            inspection,

            thermal,

            inspection_embeddings,

            thermal_embeddings

        )

        kb = self.update_knowledge_base(

            kb

        )

        self.save_matches()

        print()

        print("=" * 60)

        print("Semantic Matching Completed")

        print("=" * 60)

        print()

        return kb