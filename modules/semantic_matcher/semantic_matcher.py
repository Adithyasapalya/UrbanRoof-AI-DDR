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
from datetime import datetime

import json
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

from modules.knowledge_base import (
    KnowledgeBase,
    Observation
)

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DIR,
    INSPECTION_EMBEDDINGS,
    THERMAL_EMBEDDINGS,
    INSPECTION_INDEX,
    THERMAL_INDEX,
    MATCHES_FILE,
    INDEX_METADATA,
    PIPELINE_VERSION,
    PARSER_VERSION,
    KNOWLEDGE_BASE_VERSION,
    SEMANTIC_MATCHER_VERSION,
    TOP_K,
    AUTO_MATCH_THRESHOLD,
    REVIEW_THRESHOLD,
    IGNORE_THRESHOLD,
    KEYWORD_WEIGHT,
    SEMANTIC_WEIGHT,
)

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
        output_file: Path
    ):

        np.save(output_file, embeddings)

        print(f"Saved embeddings → {output_file}")

    # --------------------------------------------------------

    def load_embeddings(
        self,
        input_file: Path
    ) -> np.ndarray:

        embeddings = np.load(input_file)

        print(f"Loaded embeddings ← {input_file}")

        return embeddings
    
# ============================================================
# Index Manager
# ============================================================

import json
from datetime import datetime


class IndexManager:
    """
    Responsible for:
    - Building FAISS indexes
    - Saving indexes
    - Loading indexes
    - Saving metadata
    """

    def __init__(self):

        self.inspection_index = None

        self.thermal_index = None
            
    # --------------------------------------------------------
    # Build Index
    # --------------------------------------------------------

    def build_index(
        self,
        embeddings: np.ndarray
    ):

        if len(embeddings) == 0:

            return None

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)

        index.add(embeddings)

        return index
    
    # --------------------------------------------------------
    # Save Index
    # --------------------------------------------------------

    def save_index(
        self,
        index,
        path: Path
    ):

        faiss.write_index(
            index,
            path
        )

        print(f"Saved index → {path}")
    # --------------------------------------------------------
    # Load Index
    # --------------------------------------------------------

    def load_index(
        self,
        path: Path
    ):

        print(f"Loading index ← {path}")

        return faiss.read_index(path)
        # --------------------------------------------------------
    # Save Metadata
    # --------------------------------------------------------

    def save_metadata(

        self,

        embedding_model,

        embedding_dimension,

        inspection_vectors,

        thermal_vectors,

        output_path

    ):

        metadata = {

    "pipeline_version": PIPELINE_VERSION,

    "parser_version": PARSER_VERSION,

    "knowledge_base_version": KNOWLEDGE_BASE_VERSION,

    "semantic_matcher_version": SEMANTIC_MATCHER_VERSION,

    "embedding_model": embedding_model,

    "embedding_dimension": embedding_dimension,

    "inspection_vectors": inspection_vectors,

    "thermal_vectors": thermal_vectors,

    "created_at": datetime.now().isoformat()

}

        with open(

            output_path,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                metadata,

                f,

                indent=4

            )

        print(

            f"Saved metadata → {output_path}"

        )
           # --------------------------------------------------------
    # Validate Metadata
    # --------------------------------------------------------

    def validate_metadata(

        self,

        metadata_path,

        embedding_model,

        embedding_dimension

    ):

        with open(

            metadata_path,

            "r",

            encoding="utf-8"

        ) as f:

            metadata = json.load(f)

        if metadata["embedding_model"] != embedding_model:

            raise ValueError(

                "Embedding model mismatch."

            )

        if metadata["embedding_dimension"] != embedding_dimension:

            raise ValueError(

                "Embedding dimension mismatch."

            )

        print("Metadata validated successfully.")

    
# ============================================================
# Semantic Matcher
# ============================================================

class SemanticMatcher:

    """
    Main orchestrator.
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()

        self.index_manager = IndexManager()

        self.dimension = self.embedding_engine.dimension

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
    