from modules.knowledge_base import KnowledgeBase


kb = KnowledgeBase()



inspection = kb.add_observation(

    source="inspection",

    area="Kitchen",

    page=5,

    issue="Wall Dampness",

    description="Dampness observed near sink",

    source_evidence="Visible damp patches near kitchen sink area",

    bbox=[20,30,200,80]

)



thermal = kb.add_observation(

    source="thermal",

    area="Kitchen",

    page=8,

    issue="Moisture Anomaly",

    description="Cold region detected",

    source_evidence="Blue thermal region indicates moisture",

    bbox=[15,25,180,75]

)



kb.link_observations(

    inspection.id,

    thermal.id,

    0.91

)



kb.summary()


print(
    inspection
)