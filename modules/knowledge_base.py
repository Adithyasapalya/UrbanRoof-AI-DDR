"""
===========================================================
UrbanRoof AI DDR Generator

Knowledge Base

Stores all observations extracted from
Inspection and Thermal reports.

Author: Adithya Sapalya
===========================================================
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


# ==========================================================
# Observation
# ==========================================================

@dataclass
class Observation:

    id: int

    source: str

    area: str

    page: int

    issue: str

    description: str

    source_evidence: str

    bbox: list

    image_refs: List[str] = field(default_factory=list)

    embedding=None

    embedding_id: int = -1

    confidence: float = 1.0

    matched_observation_id: Optional[int] = None

    similarity_score: float = 0.0

    severity: str = "Unknown"

    root_cause: str = ""

    recommendation: str = ""


# ==========================================================
# Area
# ==========================================================

@dataclass
class PropertyArea:

    name: str

    observations: List[Observation] = field(default_factory=list)


# ==========================================================
# Knowledge Base
# ==========================================================

class KnowledgeBase:

    def __init__(self):

        self.inspection_observations = []

        self.thermal_observations = []

        self.observations = []

        self.areas = {}

        self.counter = 0

    # =======================================================
    # Area
    # =======================================================

    def add_area(self, area):

        if area not in self.areas:

            self.areas[area] = PropertyArea(area)

    # =======================================================
    # Add Observation
    # =======================================================

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

        obs = Observation(

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

        self.counter += 1

        self.observations.append(obs)

        self.areas[area].observations.append(obs)

        if source.lower() == "inspection":

            self.inspection_observations.append(obs)

        else:

            self.thermal_observations.append(obs)

        return obs

    # =======================================================
    # Link Observations
    # =======================================================

    def link(

        self,

        inspection_id,

        thermal_id,

        similarity

    ):

        inspection = self.get_observation(

            inspection_id

        )

        thermal = self.get_observation(

            thermal_id

        )

        if inspection is None:

            return

        if thermal is None:

            return

        inspection.matched_observation_id = thermal.id

        thermal.matched_observation_id = inspection.id

        inspection.similarity_score = similarity

        thermal.similarity_score = similarity

    # =======================================================
    # Getters
    # =======================================================

    def get_observation(self, obs_id):

        for obs in self.observations:

            if obs.id == obs_id:

                return obs

        return None

    def get_all_observations(self):

        return self.observations

    def get_inspection_observations(self):

        return self.inspection_observations

    def get_thermal_observations(self):

        return self.thermal_observations

    def get_area_observations(self, area):

        if area not in self.areas:

            return []

        return self.areas[area].observations

    # =======================================================
    # Load Parsed PDF
    # =======================================================

    def load_pdf(

        self,

        parsed_pdf,

        source

    ):

        pages = parsed_pdf.get("pages", [])

        current_area = "General"

        for page in pages:

            page_no = page["page_number"]

            if page["sections"]:

                current_area = page["sections"][0]

            observations = page.get(

                "observations",

                []

            )

            for obs in observations:

                self.add_observation(

                    source=source,

                    area=current_area,

                    page=page_no,

                    issue=obs["keyword"],

                    description=obs["text"],

                    source_evidence=obs["text"],

                    bbox=obs["bbox"],

                    image_refs=[],

                    confidence=1.0

                )

    # =======================================================
    # Summary
    # =======================================================

    def summary(self):

        print("\n========== Knowledge Base ==========\n")

        print(

            "Inspection Findings :",

            len(self.inspection_observations)

        )

        print(

            "Thermal Findings :",

            len(self.thermal_observations)

        )

        print(

            "Total Findings :",

            len(self.observations)

        )

        print()

        for area in self.areas.values():

            print(

                area.name,

                "->",

                len(area.observations)

            )

    # =======================================================
    # Save
    # =======================================================

    def save(self, path):

        data = {

            "inspection": [

                asdict(obs)

                for obs in self.inspection_observations

            ],

            "thermal": [

                asdict(obs)

                for obs in self.thermal_observations

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

            f"Knowledge Base saved -> {path}"

        )