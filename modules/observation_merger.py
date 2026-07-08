"""
==========================================================
UrbanRoof AI DDR Generator

Observation Merger

Merges duplicate observations from inspection and thermal
reports into one consolidated observation.

Author : Adithya Sapalya
==========================================================
"""


from dataclasses import dataclass, field

from modules.knowledge_base import Observation



# ==========================================================
# Merged Observation
# ==========================================================

@dataclass
class MergedObservation:

    area: str

    issue: str

    description: str = ""

    evidence: list = field(default_factory=list)

    source: list = field(default_factory=list)

    severity: str = "Unknown"

    root_cause: str = ""

    recommendation: str = ""

    similarity_score: float = 0.0

    image_refs: list = field(default_factory=list)

    observations: list = field(default_factory=list)



# ==========================================================
# Merger
# ==========================================================

class ObservationMerger:


    def __init__(self):

        self.merged = []



    # ------------------------------------------------------

    def severity_rank(
            self,
            severity
    ):

        order = {

            "Critical": 5,

            "High": 4,

            "Medium": 3,

            "Low": 2,

            "Unknown": 1

        }

        return order.get(
            severity,
            1
        )



    # ------------------------------------------------------

    def normalize_text(
            self,
            text
    ):

        if not text:

            return ""

        return (
            text.lower()
            .strip()
            .replace("-", " ")
            .replace("_", " ")
        )



    # ------------------------------------------------------

    def calculate_similarity(
            self,
            obs1,
            obs2
    ):
        """
        Calculates similarity between observations.

        Handles different terminology:
        Inspection:
            Water Leakage

        Thermal:
            Thermal Hotspot
        """

        score = 0



        # Area matching

        if self.normalize_text(
            obs1.area
        ) == self.normalize_text(
            obs2.area
        ):

            score += 0.6



        issue1 = self.normalize_text(
            obs1.issue
        )

        issue2 = self.normalize_text(
            obs2.issue
        )



        defect_groups = [

            [
                "water",
                "leak",
                "leakage",
                "moisture",
                "thermal",
                "hotspot",
                "temperature",
                "anomaly"
            ],


            [
                "crack",
                "fracture",
                "damage"
            ],


            [
                "rust",
                "corrosion"
            ]

        ]



        for group in defect_groups:


            found1 = any(
                word in issue1
                for word in group
            )


            found2 = any(
                word in issue2
                for word in group
            )


            if found1 and found2:

                score += 0.4

                break



        return round(
            min(score, 1.0),
            2
        )



    # ------------------------------------------------------

    def merge_evidence(
            self,
            obs
    ):

        evidence = []


        if obs.description:

            evidence.append(
                obs.description
            )


        if obs.source_evidence:

            evidence.extend(
                obs.source_evidence
            )


        return evidence



    # ------------------------------------------------------

    def merge_two_observations(
            self,
            obs1,
            obs2
    ):

        severity = (

            obs1.severity

            if self.severity_rank(
                obs1.severity
            )
            >=
            self.severity_rank(
                obs2.severity
            )

            else obs2.severity

        )



        merged = MergedObservation(

            area=obs1.area,


            issue=obs1.issue,


            description=(

                obs1.description
                +
                " | "
                +
                obs2.description

            ),



            evidence=(

                self.merge_evidence(obs1)
                +
                self.merge_evidence(obs2)

            ),



            source=[

                obs1.source,

                obs2.source

            ],



            severity=severity,



            root_cause=(

                getattr(
                    obs1,
                    "root_cause",
                    ""
                )
                or
                getattr(
                    obs2,
                    "root_cause",
                    ""
                )

            ),



            recommendation=(

                getattr(
                    obs1,
                    "recommendation",
                    ""
                )
                or
                getattr(
                    obs2,
                    "recommendation",
                    ""
                )

            ),



            similarity_score=
                self.calculate_similarity(
                    obs1,
                    obs2
                ),



            image_refs=list(
                set(

                    getattr(
                        obs1,
                        "image_refs",
                        []

                    )
                    +
                    getattr(
                        obs2,
                        "image_refs",
                        []

                    )

                )
            ),



            observations=[

                obs1,

                obs2

            ]

        )


        return merged



    # ------------------------------------------------------

    def merge_observations(
            self,
            observations
    ):

        self.merged = []

        processed = set()



        for i, obs1 in enumerate(observations):


            if i in processed:

                continue



            matched_indexes = []

            best_similarity = 0



            for j, obs2 in enumerate(observations):


                if i == j or j in processed:

                    continue



                similarity = self.calculate_similarity(
                    obs1,
                    obs2
                )


                if similarity >= 0.6:


                    matched_indexes.append(j)


                    best_similarity = max(
                        best_similarity,
                        similarity
                    )



            # Merge duplicates

            if matched_indexes:


                merged_obs = obs1



                for index in matched_indexes:


                    merged_obs = self.merge_two_observations(

                        merged_obs,

                        observations[index]

                    )


                    processed.add(index)



                merged_obs.similarity_score = (
                    best_similarity
                )


                self.merged.append(
                    merged_obs
                )



            else:


                single = MergedObservation(

                    area=obs1.area,

                    issue=obs1.issue,

                    description=obs1.description,

                    evidence=self.merge_evidence(
                        obs1
                    ),

                    source=[
                        obs1.source
                    ],

                    severity=obs1.severity,

                    root_cause=getattr(
                        obs1,
                        "root_cause",
                        ""
                    ),

                    recommendation=getattr(
                        obs1,
                        "recommendation",
                        ""
                    ),

                    image_refs=getattr(
                        obs1,
                        "image_refs",
                        []
                    ),

                    similarity_score=1.0,

                    observations=[
                        obs1
                    ]

                )


                self.merged.append(
                    single
                )



            processed.add(i)



        return self.merged



    # ------------------------------------------------------

    def merge_inspection_and_thermal(
            self,
            inspection_data,
            thermal_data
    ):

        combined = []


        combined.extend(
            inspection_data
        )


        combined.extend(
            thermal_data
        )


        return self.merge_observations(
            combined
        )