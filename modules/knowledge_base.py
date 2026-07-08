"""
===========================================================
UrbanRoof AI DDR Generator

knowledge_base.py

Advanced Observation Knowledge Base

Supports:

- Inspection observations
- Thermal observations
- Semantic matching
- Observation linking
- Embedding storage
- Gemini-ready reasoning

===========================================================
"""


from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
import json



# ==========================================================
# Observation Object
# ==========================================================


@dataclass
class Observation:


    id: int


    # Source document
    source: str


    # Location
    area: str


    page: int


    # Problem information
    issue: str


    description: str



    # Exact extracted sentence
    # from PDF

    source_evidence: str



    # Location inside PDF

    bbox: list



    # Connected images

    image_refs: List[str] = field(
        default_factory=list
    )



    # AI information


    embedding: Optional[List[float]] = None


    embedding_id: int = -1



    confidence: float = 1.0



    # Matching information


    matched_observation_id: Optional[int] = None


    similarity_score: float = 0.0



    # Gemini output fields


    severity: str = "Unknown"


    root_cause: str = ""


    recommendation: str = ""



# ==========================================================
# Property Area
# ==========================================================


@dataclass
class PropertyArea:


    name: str


    observations: List[Observation] = field(
        default_factory=list
    )
# ==========================================================
# Knowledge Base
# ==========================================================


class KnowledgeBase:


    def __init__(self):


        self.observations = {}

        self.areas = {}


        self.counter = 0



    # ------------------------------------------------------

    def add_area(self, area):


        if area not in self.areas:

            self.areas[area] = PropertyArea(
                name=area
            )



    # ------------------------------------------------------

    def add_observation(

        self,

        source,

        area,

        page,

        issue,

        description,

        source_evidence,

        bbox,

        image_refs=None,

        confidence=1.0

    ):



        self.add_area(area)



        observation = Observation(

            id=self.counter,

            source=source,

            area=area,

            page=page,

            issue=issue,

            description=description,

            source_evidence=source_evidence,

            bbox=bbox,

            image_refs=image_refs or [],

            confidence=confidence

        )



        self.observations[
            self.counter
        ] = observation



        self.areas[area].observations.append(
            observation
        )



        self.counter += 1



        return observation



    # ------------------------------------------------------

    def link_observations(

        self,

        inspection_id,

        thermal_id,

        similarity

    ):


        inspection = self.observations.get(
            inspection_id
        )


        thermal = self.observations.get(
            thermal_id
        )



        if inspection and thermal:


            inspection.matched_observation_id = (
                thermal_id
            )


            thermal.matched_observation_id = (
                inspection_id
            )


            inspection.similarity_score = (
                similarity
            )


            thermal.similarity_score = (
                similarity
            )



    # ------------------------------------------------------

    def get_observation(self, obs_id):

        return self.observations.get(obs_id)



    # ------------------------------------------------------

    def get_all_observations(self):

        return list(
            self.observations.values()
        )



    # ------------------------------------------------------

    def get_area_observations(self, area):

        if area in self.areas:

            return self.areas[
                area
            ].observations


        return []



    # ------------------------------------------------------

    def summary(self):


        print("\n========== Knowledge Base ==========\n")


        print(
            "Total observations:",
            len(self.observations)
        )


        print(
            "Areas:",
            len(self.areas)
        )



        for area in self.areas.values():


            print(

                area.name,

                "->",

                len(area.observations),

                "findings"

            )



    # ------------------------------------------------------

    def save(self,path):


        data = {


            "observations":[

                asdict(obs)

                for obs in self.observations.values()

            ]

        }



        with open(

            path,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                data,

                f,

                indent=4

            )



        print(
            "Knowledge base saved:",
            path
        )
        # ------------------------------------------------------

    def get_observations_by_source(self, source):
        """
        Return all observations from a given source.
        """

        source = source.lower()

        return [
            obs
            for obs in self.observations.values()
            if obs.source.lower() == source
        ]
        # ------------------------------------------------------

    def get_inspection_observations(self):

        return self.get_observations_by_source(
            "inspection"
        )
        # ------------------------------------------------------

    def get_thermal_observations(self):

        return self.get_observations_by_source(
            "thermal"
        )
    