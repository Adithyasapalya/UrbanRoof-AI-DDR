"""
==========================================================
UrbanRoof AI DDR Generator

Observation Merger Test

Tests inspection + thermal observation merging.

Author : Adithya Sapalya
==========================================================
"""


from modules.observation_merger import ObservationMerger
from modules.knowledge_base import Observation



# ==========================================================
# Sample Inspection Data
# ==========================================================

inspection_observation = Observation(

    id="INS-001",

    area="North Roof Section",

    issue="Water Leakage",

    description=
        "Visible moisture damage near roof panel",

    severity="High",

    page=1,

    source="Inspection Report",

    source_evidence=[
        "Visible water stain",
        "Damaged roof membrane"
    ],

    bbox=[
        100,
        120,
        300,
        250
    ]

)



# ==========================================================
# Sample Thermal Data
# ==========================================================

thermal_observation = Observation(

    id="THR-001",

    area="North Roof Section",

    issue="Thermal Hotspot",

    description=
        "Temperature anomaly indicating possible moisture accumulation",

    severity="Medium",

    page=2,

    source="Thermal Report",

    source_evidence=[
        "High temperature variation detected"
    ],

    bbox=[
        110,
        130,
        310,
        260
    ]

)



# ==========================================================
# Run Test
# ==========================================================

def test_merging():

    merger = ObservationMerger()


    result = merger.merge_inspection_and_thermal(
        [
            inspection_observation
        ],
        [
            thermal_observation
        ]
    )


    print(
        "\nNumber of merged observations:",
        len(result)
    )


    for obs in result:

        print("\n----------------")

        print(
            "Area:",
            obs.area
        )

        print(
            "Issue:",
            obs.issue
        )

        print(
            "Severity:",
            obs.severity
        )

        print(
            "source:",
            obs.source
        )

        print(
            "Similarity:",
            obs.similarity_score
        )



    # Debug before assertion

    print("\n========== DEBUG ==========")

    for item in result:

        print(
            "Issue:",
            item.issue,
            "| source:",
            item.source,
            "| Similarity:",
            item.similarity_score
        )

    print("==========================")



    merged = result[0]


    print(
        "\n========== DDR MERGED OUTPUT =========="
    )


    print(
        "Area:",
        merged.area
    )


    print(
        "Issue:",
        merged.issue
    )


    print(
        "Severity:",
        merged.severity
    )


    print(
        "source:",
        merged.source
    )


    print(
        "Evidence:",
        merged.evidence
    )


    print(
        "Similarity:",
        merged.similarity_score
    )


    print(
        "Images:",
        merged.image_refs
    )


    print(
        "======================================"
    )



    # ======================================================
    # Validation checks
    # ======================================================

    assert len(result) == 1


    assert (
        merged.area
        ==
        "North Roof Section"
    )


    assert (
        merged.severity
        ==
        "High"
    )


    assert (
        len(merged.source)
        ==
        2
    )


    assert (
        "Inspection Report"
        in
        merged.source
    )


    assert (
        "Thermal Report"
        in
        merged.source
    )



if __name__ == "__main__":

    test_merging()