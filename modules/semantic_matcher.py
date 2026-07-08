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
from pathlib import Path
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

        self.model = SentenceTransformer(EMBEDDING_MODEL)

        self.dimension = self.model.get_sentence_embedding_dimension()

        print(f"Embedding Dimension : {self.dimension}")

        self.matches = []
            # --------------------------------------------------------
    # Observation to Text
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

        inspection_embeddings,

        thermal_embeddings

    ):

        np.save(

            INSPECTION_EMBEDDINGS,

            inspection_embeddings

        )

        np.save(

            THERMAL_EMBEDDINGS,

            thermal_embeddings

        )

        print("Embeddings Saved.")
            # --------------------------------------------------------
    # Build FAISS Index
    # --------------------------------------------------------

    def build_index(

        self,

        embeddings

    ):

        index = faiss.IndexFlatIP(

            embeddings.shape[1]

        )

        index.add(

            embeddings

        )

        return index
    
        # --------------------------------------------------------
    # Keyword Extraction
    # --------------------------------------------------------

    def extract_keywords(self, text: str):

        stopwords = {
            "the", "a", "an", "of", "is", "are",
            "and", "to", "near", "on", "at",
            "in", "for", "with"
        }

        words = []

        for word in text.lower().split():

            word = "".join(
                c for c in word
                if c.isalnum()
            )

            if len(word) > 2 and word not in stopwords:

                words.append(word)

        return set(words)

    # --------------------------------------------------------
    # Keyword Similarity
    # --------------------------------------------------------

    def keyword_similarity(
        self,
        obs1: Observation,
        obs2: Observation
    ):

        words1 = self.extract_keywords(
            self.observation_to_text(obs1)
        )

        words2 = self.extract_keywords(
            self.observation_to_text(obs2)
        )

        if len(words1) == 0:

            return 0.0

        overlap = words1.intersection(words2)

        union = words1.union(words2)

        return len(overlap) / max(len(union), 1)

    # --------------------------------------------------------
    # Combined Score
    # --------------------------------------------------------

    def combined_score(

        self,

        semantic_score,

        keyword_score

    ):

        return (

            semantic_score * SEMANTIC_WEIGHT

            +

            keyword_score * KEYWORD_WEIGHT

        )

    # --------------------------------------------------------
    # Match Type
    # --------------------------------------------------------

    def classify_match(

        self,

        score

    ):

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

        inspection_observations,

        thermal_observations,

        inspection_embeddings,

        thermal_embeddings

    ):

        print("\nSearching for matches...")

        thermal_index = self.build_index(
            thermal_embeddings
        )

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

            best_score = -1

            for rank in range(TOP_K):

                thermal_idx = indices[
                    inspection_idx
                ][rank]

                if thermal_idx == -1:

                    continue

                if thermal_idx in used_thermal:

                    continue

                thermal = thermal_observations[
                    thermal_idx
                ]

                semantic_score = float(

                    distances[
                        inspection_idx
                    ][rank]

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

            thermal_idx, semantic_score, keyword_score, final_score = best_match

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

            matches.append(match)

        self.matches = matches

        print(
            f"Found {len(matches)} matches."
        )

        return matches
        # --------------------------------------------------------
    # Update Knowledge Base
    # --------------------------------------------------------

    def update_knowledge_base(

        self,

        kb: KnowledgeBase

    ):

        inspection_lookup = {

            obs.id: obs

            for obs in kb.inspection_observations

        }

        thermal_lookup = {

            obs.id: obs

            for obs in kb.thermal_observations

        }

        for match in self.matches:

            inspection = inspection_lookup[
                match.inspection_id
            ]

            thermal = thermal_lookup[
                match.thermal_id
            ]

            inspection.matched_observation_id = thermal.id
            inspection.similarity_score = match.final_score

            thermal.matched_observation_id = inspection.id
            thermal.similarity_score = match.final_score

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

                "keyword_score": round(match.keyword_score, 4),

                "semantic_score": round(match.semantic_score, 4),

                "final_score": round(match.final_score, 4),

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

        print(f"Saved {len(data)} matches -> {MATCHES_FILE}")

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

            "inspection_vectors": len(inspection_embeddings),

            "thermal_vectors": len(thermal_embeddings)

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

        print("Metadata saved.")
           # --------------------------------------------------------
    # Full Pipeline
    # --------------------------------------------------------

    def run(

        self,

        kb: KnowledgeBase

    ):

        print("\n===================================")
        print("Running Semantic Matching")
        print("===================================")

        inspection = kb.inspection_observations

        thermal = kb.thermal_observations

        print(f"\nInspection Findings : {len(inspection)}")

        print(f"Thermal Findings    : {len(thermal)}")

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

        print("\nSemantic Matching Completed Successfully")

        return kb
     
    # --------------------------------------------------------
    # Save Index
    # --------------------------------------------------------

    def save_index(

        self,

        inspection_index,

        thermal_index

    ):

        faiss.write_index(

            inspection_index,

            str(INSPECTION_INDEX)

        )

        faiss.write_index(

            thermal_index,

            str(THERMAL_INDEX)

        )

        print("Indexes Saved.")
