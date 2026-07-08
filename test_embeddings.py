from modules.knowledge_base import KnowledgeBase
from modules.semantic_matcher import SemanticMatcher

kb = KnowledgeBase()

kb.add_observation(
    source="inspection",
    area="Kitchen",
    page=1,
    issue="Wall Dampness",
    description="Damp patches found.",
    source_evidence="Visible damp patch near sink.",
    bbox=[10,20,30,40]
)

kb.add_observation(
    source="inspection",
    area="Bathroom",
    page=2,
    issue="Leakage",
    description="Leakage below basin.",
    source_evidence="Water stains below wash basin.",
    bbox=[10,20,30,40]
)

matcher = SemanticMatcher()

observations = kb.get_all_observations()

embeddings = matcher.create_embeddings(observations)

matcher.assign_embedding_ids(observations)

print("Embedding Shape:", embeddings.shape)

print("Embedding ID of first observation:", observations[0].embedding_id)

matcher.save_embeddings(
    embeddings,
    "output/inspection_embeddings.npy"
)