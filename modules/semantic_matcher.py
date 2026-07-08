"""
=========================================================
UrbanRoof AI DDR Generator

semantic_matcher.py

Creates semantic embeddings for observations and
matches Inspection ↔ Thermal findings.

Uses

Sentence Transformers
+
FAISS

=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

from modules.knowledge_base import KnowledgeBase


class SemanticMatcher:

    """
    Wrapper around SentenceTransformer + FAISS
    """

    def __init__(

        self,

        model_name="all-MiniLM-L6-v2"

    ):

        print("\nLoading embedding model...")

        self.model = SentenceTransformer(model_name)

        print("Model Loaded.\n")

        self.dimension = 384

        self.index = faiss.IndexFlatIP(self.dimension)

        self.embedding_lookup = []



    # --------------------------------------------------

    def normalize(

        self,

        embeddings

    ):

        faiss.normalize_L2(embeddings)

        return embeddings



    # --------------------------------------------------

    def embed_text(

        self,

        text

    ):

        embedding = self.model.encode(

            text,

            convert_to_numpy=True,

            normalize_embeddings=True

        )

        return embedding.astype(np.float32)



    # --------------------------------------------------

    def embed_observation(

        self,

        observation

    ):

        """
        Generate embedding using
        issue + description + evidence
        """

        text = f"""

        Area:
        {observation.area}

        Issue:
        {observation.issue}

        Description:
        {observation.description}

        Evidence:
        {observation.source_evidence}

        """

        return self.embed_text(text)
    
    # --------------------------------------------------
    # Batch Embedding
    # --------------------------------------------------

    def create_embeddings(self, observations):
        """
        Create embeddings for multiple observations.
        """

        if len(observations) == 0:
            return np.empty((0, self.dimension), dtype=np.float32)

        texts = []

        for obs in observations:

            text = f"""
            Area: {obs.area}

            Issue: {obs.issue}

            Description: {obs.description}

            Evidence: {obs.source_evidence}
            """

            texts.append(text)

        print(f"\nGenerating embeddings for {len(texts)} observations...")

        embeddings = self.model.encode(

            texts,

            convert_to_numpy=True,

            normalize_embeddings=True,

            show_progress_bar=True

        )

        embeddings = embeddings.astype(np.float32)

        return embeddings
    
        # --------------------------------------------------
    # Save Embeddings
    # --------------------------------------------------

    def save_embeddings(
        self,
        embeddings,
        output_file
    ):
        """
        Save embeddings as NumPy array.
        """

        np.save(output_file, embeddings)

        print(f"Embeddings saved to {output_file}")

        # --------------------------------------------------
    # Load Embeddings
    # --------------------------------------------------

    def load_embeddings(
        self,
        input_file
    ):

        embeddings = np.load(input_file)

        return embeddings
    
        # --------------------------------------------------
    # Assign Embedding IDs
    # --------------------------------------------------

    def assign_embedding_ids(
        self,
        observations
    ):

        for idx, obs in enumerate(observations):

            obs.embedding_id = idx

        # --------------------------------------------------
    # Build FAISS Index
    # --------------------------------------------------

    def build_index(
        self,
        embeddings
    ):

        index = faiss.IndexFlatIP(

            embeddings.shape[1]

        )

        index.add(embeddings)

        return index
    
    