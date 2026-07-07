from modules.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

kb.add_observation(
    source="inspection",
    area="Kitchen",
    page=5,
    issue="Wall Dampness",
    description="Observed dampness near sink.",
    bbox=[20, 30, 200, 80]
)

kb.add_observation(
    source="thermal",
    area="Kitchen",
    page=8,
    issue="Cold Spot",
    description="Thermal anomaly detected.",
    bbox=[15, 25, 180, 75]
)

kb.add_observation(
    source="inspection",
    area="Bathroom",
    page=12,
    issue="Leakage",
    description="Leakage observed below wash basin.",
    bbox=[30, 50, 220, 90]
)

kb.summary()

kb.save("output/knowledge_base.json")