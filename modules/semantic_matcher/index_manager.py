"""
=========================================================
Index Manager

Responsible for:
- Building FAISS indexes
- Saving indexes
- Loading indexes
- Saving metadata
- Validating metadata

=========================================================
"""

from datetime import datetime
import json
from pathlib import Path

import faiss
import numpy as np

from config import (
    EMBEDDING_MODEL,
    PIPELINE_VERSION,
    PARSER_VERSION,
    KNOWLEDGE_BASE_VERSION,
    SEMANTIC_MATCHER_VERSION,
)


class IndexManager:
    """
    Handles FAISS index operations.
    """

    def __init__(self):

        self.inspection_index = None
        self.thermal_index = None

    # --------------------------------------------------
    # Build Index
    # --------------------------------------------------

    def build_index(
        self,
        embeddings: np.ndarray
    ):

        if embeddings.size == 0:
            return None

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)

        index.add(embeddings)

        return index

    # --------------------------------------------------
    # Save Index
    # --------------------------------------------------

    def save_index(
        self,
        index,
        path: Path
    ):

        if index is None:
            print("No index to save.")
            return

        faiss.write_index(index, str(path))

        print(f"Saved index -> {path}")

    # --------------------------------------------------
    # Load Index
    # --------------------------------------------------

    def load_index(
        self,
        path: Path
    ):

        if not path.exists():
            raise FileNotFoundError(path)

        print(f"Loading index <- {path}")

        return faiss.read_index(str(path))

    # --------------------------------------------------
    # Search Index
    # --------------------------------------------------

    def search(
        self,
        index,
        query_embedding,
        top_k=3
    ):

        if index is None:
            raise ValueError("Index has not been built.")

        scores, ids = index.search(
            query_embedding.reshape(1, -1),
            top_k
        )

        return scores[0], ids[0]

    # --------------------------------------------------
    # Save Metadata
    # --------------------------------------------------

    def save_metadata(
        self,
        embedding_dimension,
        inspection_vectors,
        thermal_vectors,
        output_file: Path
    ):

        metadata = {

            "pipeline_version": PIPELINE_VERSION,

            "parser_version": PARSER_VERSION,

            "knowledge_base_version": KNOWLEDGE_BASE_VERSION,

            "semantic_matcher_version": SEMANTIC_MATCHER_VERSION,

            "embedding_model": EMBEDDING_MODEL,

            "embedding_dimension": embedding_dimension,

            "inspection_vectors": inspection_vectors,

            "thermal_vectors": thermal_vectors,

            "created_at": datetime.now().isoformat()

        }

        with open(output_file, "w", encoding="utf-8") as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        print(f"Saved metadata -> {output_file}")

    # --------------------------------------------------
    # Load Metadata
    # --------------------------------------------------

    def load_metadata(
        self,
        metadata_file: Path
    ):

        with open(metadata_file, "r", encoding="utf-8") as f:

            metadata = json.load(f)

        return metadata

    # --------------------------------------------------
    # Validate Metadata
    # --------------------------------------------------

    def validate_metadata(
        self,
        metadata
    ):

        if metadata["embedding_model"] != EMBEDDING_MODEL:

            raise ValueError(
                "Embedding model mismatch."
            )

        print("Embedding model validated.")

        return True