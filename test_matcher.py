from modules.knowledge_base import KnowledgeBase
from modules.semantic_matcher import SemanticMatcher

kb = KnowledgeBase()

kb.add_observation(
    source="inspection",
    area="Kitchen",
    page=1,
    issue="Wall Dampness",
    description="Moist wall near sink.",
    source_evidence="Visible dampness near sink.",
    bbox=[1,2,3,4]
)

kb.add_observation(
    source="thermal",
    area="Kitchen",
    page=2,
    issue="Moisture Anomaly",
    description="Cold spot detected behind sink wall.",
    source_evidence="Blue thermal region.",
    bbox=[1,2,3,4]
)

matcher = SemanticMatcher()

matcher.build_indexes(kb)

matches = matcher.match_observations(kb)

print(matches)

print(kb.get_observation(0))