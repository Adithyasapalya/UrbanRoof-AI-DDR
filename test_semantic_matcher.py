from modules.semantic_matcher import SemanticMatcher
from modules.knowledge_base import KnowledgeBase, Observation

kb = KnowledgeBase()

kb.inspection_observations = [

    Observation(

        id=0,

        source="inspection",

        area="Kitchen",

        page=1,

        issue="Wall Dampness",

        description="Water stain near sink",

        source_evidence="Visible damp patch"

    )

]

kb.thermal_observations = [

    Observation(

        id=1,

        source="thermal",

        area="Kitchen",

        page=2,

        issue="Cold Patch",

        description="Thermal anomaly near sink",

        source_evidence="Blue thermal region"

    )

]

matcher = SemanticMatcher()

kb = matcher.run(kb)

print()

print("========== MATCHES ==========")

for obs in kb.inspection_observations:

    print(obs)