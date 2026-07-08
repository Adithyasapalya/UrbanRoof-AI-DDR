"""
=============================================================
semantic_matcher.py

UrbanRoof AI DDR Generator

Semantic Matching Engine

Pipeline

Knowledge Base
      ↓
Embedding Engine
      ↓
FAISS Index
      ↓
Hybrid Matcher
      ↓
Matched Observations

Author: Adithya Sapalya
=============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from collections import Counter

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

from modules.knowledge_base import (
    KnowledgeBase,
    Observation
)

# ============================================================
# Configuration
# ============================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

AUTO_MATCH_THRESHOLD = 0.90

REVIEW_THRESHOLD = 0.70

TOP_K = 3

# ============================================================
# Match Object
# ============================================================

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

# ============================================================
# Embedding Engine
# ============================================================

class EmbeddingEngine:
    """
    Responsible for:
    - Creating embeddings
    - Saving embeddings
    - Loading embeddings
    """

    def __init__(self, model_name=EMBEDDING_MODEL):

        print("\nLoading embedding model...")

        self.model = SentenceTransformer(model_name)

        self.dimension = self.model.get_sentence_embedding_dimension()

        print(f"Embedding model loaded ({self.dimension} dimensions).")

    # --------------------------------------------------------

    def observation_to_text(self, observation: Observation) -> str:
        """
        Convert an Observation into a rich text representation.
        """

        return f"""
Area:
{observation.area}

Issue:
{observation.issue}

Description:
{observation.description}

Evidence:
{observation.source_evidence}
"""

    # --------------------------------------------------------

    def create_embeddings(
        self,
        observations: List[Observation]
    ) -> np.ndarray:
        """
        Create embeddings for all observations.
        """

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
            f"\nGenerating embeddings for {len(texts)} observations..."
        )

        embeddings = self.model.encode(

            texts,

            convert_to_numpy=True,

            normalize_embeddings=True,

            show_progress_bar=True

        )

        return embeddings.astype(np.float32)

    # --------------------------------------------------------

    def assign_embedding_ids(
        self,
        observations: List[Observation]
    ):
        """
        Assign row numbers from the embedding matrix.
        """

        for idx, obs in enumerate(observations):

            obs.embedding_id = idx

    # --------------------------------------------------------

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        output_file: str
    ):

        np.save(output_file, embeddings)

        print(f"Saved embeddings → {output_file}")

    # --------------------------------------------------------

    def load_embeddings(
        self,
        input_file: str
    ) -> np.ndarray:

        embeddings = np.load(input_file)

        print(f"Loaded embeddings ← {input_file}")

        return embeddings
    
# ============================================================
# Semantic Matcher
# ============================================================

class SemanticMatcher:

    """
    Main orchestrator.
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()

        self.dimension = self.embedding_engine.dimension

        self.inspection_index = None

        self.thermal_index = None

        self.matches = []

    # --------------------------------------------------------
    # Create text representation
    # --------------------------------------------------------

    def observation_text(
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
"""
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

        words = [

            word.lower()

            for word in text.split()

            if len(word) > 2

        ]

        return [

            w

            for w in words

            if w not in stopwords

        ]
        # --------------------------------------------------------
    # Keyword Similarity
    # --------------------------------------------------------

    def keyword_score(

        self,

        obs1: Observation,

        obs2: Observation

    ):

        words1 = set(

            self.extract_keywords(

                self.observation_text(obs1)

            )

        )

        words2 = set(

            self.extract_keywords(

                self.observation_text(obs2)

            )

        )

        if len(words1) == 0:

            return 0.0

        overlap = words1.intersection(words2)

        return len(overlap) / len(words1)
    