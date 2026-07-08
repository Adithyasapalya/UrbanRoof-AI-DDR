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
    source="thermal",
    area="Kitchen",
    page=2,
    issue="Moisture",
    description="Cold spot behind sink",
    source_evidence="Thermal anomaly",
    bbox=[20,30,40,50]
)

engine = EmbeddingEngine()

inspection = kb.get_inspection_observations()

engine.assign_embedding_ids(inspection)

embeddings = engine.create_embeddings(
    inspection
)

print(embeddings.shape)