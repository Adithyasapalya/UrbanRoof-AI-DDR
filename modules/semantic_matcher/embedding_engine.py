"""
=========================================================
Embedding Engine

Responsible for:
- Creating embeddings
- Saving embeddings
- Loading embeddings
- Assigning embedding IDs
=========================================================
"""

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from config import (
    EMBEDDING_MODEL,
)

from modules.knowledge_base import Observation


class EmbeddingEngine:
    """
    Handles embedding generation and storage.
    """

    def __init__(self, model_name=EMBEDDING_MODEL):

        print("\nLoading embedding model...")

        self.model = SentenceTransformer(model_name)

        self.dimension = self.model.get_sentence_embedding_dimension()

        print(
            f"Embedding model loaded ({self.dimension} dimensions)."
        )

    # --------------------------------------------------

    def observation_to_text(
        self,
        observation: Observation
    ) -> str:
        """
        Convert an Observation into a text block
        for semantic embedding.
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

    # --------------------------------------------------

    def create_embeddings(
        self,
        observations: List[Observation]
    ) -> np.ndarray:
        """
        Generate embeddings for observations.
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

    # --------------------------------------------------

    def assign_embedding_ids(
        self,
        observations: List[Observation]
    ):
        """
        Assign row numbers from embedding matrix.
        """

        for idx, obs in enumerate(observations):

            obs.embedding_id = idx

    # --------------------------------------------------

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        output_file
    ):

        np.save(output_file, embeddings)

        print(
            f"Saved embeddings → {output_file}"
        )

    # --------------------------------------------------

    def load_embeddings(
        self,
        input_file
    ) -> np.ndarray:

        embeddings = np.load(input_file)

        print(
            f"Loaded embeddings ← {input_file}"
        )

        return embeddings