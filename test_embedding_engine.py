from modules.semantic_matcher import EmbeddingEngine
from modules.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

kb.add_observation(
    source="inspection",
    area="Kitchen",
    page=1,
    issue="Wall Dampness",
    description="Damp wall behind sink",
    source_evidence="Visible damp patches",
    bbox=[10,20,30,40]
)

kb.add_observation(
    source="inspection",
    area="Bathroom",
    page=2,
    issue="Leakage",
    description="Leakage below basin",
    source_evidence="Water stains visible",
    bbox=[10,20,30,40]
)

engine = EmbeddingEngine()

observations = kb.get_all_observations()

engine.assign_embedding_ids(observations)

embeddings = engine.create_embeddings(observations)

print("Shape:", embeddings.shape)

print("First Embedding ID:", observations[0].embedding_id)

engine.save_embeddings(
    embeddings,
    "output/test_embeddings.npy"
)