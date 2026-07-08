import numpy as np

from modules.semantic_matcher import IndexManager

from config import (
    INDEX_METADATA,
    INSPECTION_INDEX,
)

# ---------------------------------------
# Create Index Manager
# ---------------------------------------

manager = IndexManager()

# ---------------------------------------
# Create Dummy Embeddings
# ---------------------------------------

embeddings = np.random.rand(10, 384).astype(np.float32)

# Normalize embeddings (important for cosine similarity)
embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)

print(f"Embedding Shape: {embeddings.shape}")

# ---------------------------------------
# Build FAISS Index
# ---------------------------------------

index = manager.build_index(embeddings)

print(f"Vectors in Index: {index.ntotal}")

# ---------------------------------------
# Save Index
# ---------------------------------------

manager.save_index(
    index,
    INSPECTION_INDEX
)

# ---------------------------------------
# Save Metadata
# ---------------------------------------

manager.save_metadata(
    embedding_dimension=384,
    inspection_vectors=10,
    thermal_vectors=0,
    output_file=INDEX_METADATA
)

# ---------------------------------------
# Load Index
# ---------------------------------------

loaded_index = manager.load_index(
    INSPECTION_INDEX
)

print(f"Loaded Index Vectors: {loaded_index.ntotal}")

# ---------------------------------------
# Load Metadata
# ---------------------------------------

metadata = manager.load_metadata(
    INDEX_METADATA
)

print("\nMetadata")

for key, value in metadata.items():
    print(f"{key}: {value}")

# ---------------------------------------
# Validate Metadata
# ---------------------------------------

manager.validate_metadata(metadata)

print("\nAll tests passed successfully!")