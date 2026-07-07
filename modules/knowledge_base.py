"""
===========================================================
knowledge_base.py

UrbanRoof AI DDR Generator

Central Knowledge Base

This module stores all structured observations extracted
from Inspection and Thermal reports.

Pipeline

PDF Parser
        ↓
Knowledge Base
        ↓
Semantic Matcher
        ↓
Gemini
        ↓
DDR Generator

Author: Adithya Sapalya
===========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict
import json


# ============================================================
# Observation Dataclass
# ============================================================

@dataclass
class Observation:
    """
    Represents one inspection or thermal finding.
    """

    id: int
    source: str
    area: str
    page: int
    issue: str
    description: str
    bbox: list

    image_refs: List[str] = field(default_factory=list)

    confidence: float = 1.0

    embedding_id: int = -1

    severity: str = "Unknown"

    root_cause: str = ""

    recommendation: str = ""


# ============================================================
# Property Area
# ============================================================

@dataclass
class PropertyArea:

    name: str

    observations: List[Observation] = field(default_factory=list)

    thermal_observations: List[Observation] = field(default_factory=list)


# ============================================================
# Knowledge Base
# ============================================================

class KnowledgeBase:

    """
    Central storage for all observations.
    """

    def __init__(self):

        self.areas: Dict[str, PropertyArea] = {}

        self.total_observations = 0

    # --------------------------------------------------------

    def add_area(self, area: str):

        if area not in self.areas:

            self.areas[area] = PropertyArea(name=area)

    # --------------------------------------------------------

    def add_observation(
        self,
        source,
        area,
        page,
        issue,
        description,
        bbox,
        image_refs=None
    ):

        self.add_area(area)

        obs = Observation(

            id=self.total_observations,

            source=source,

            area=area,

            page=page,

            issue=issue,

            description=description,

            bbox=bbox,

            image_refs=image_refs or []

        )

        self.total_observations += 1

        if source.lower() == "inspection":

            self.areas[area].observations.append(obs)

        else:

            self.areas[area].thermal_observations.append(obs)

        return obs

    # --------------------------------------------------------

    def get_area(self, area):

        return self.areas.get(area)

    # --------------------------------------------------------

    def get_area_names(self):

        return list(self.areas.keys())

    # --------------------------------------------------------

    def get_all_observations(self):

        observations = []

        for area in self.areas.values():

            observations.extend(area.observations)

            observations.extend(area.thermal_observations)

        return observations

    # --------------------------------------------------------

    def total(self):

        return self.total_observations

    # --------------------------------------------------------

    def summary(self):

        print("\n" + "=" * 60)
        print("UrbanRoof Knowledge Base Summary")
        print("=" * 60)

        print(f"\nAreas Detected       : {len(self.areas)}")
        print(f"Total Observations   : {self.total_observations}")

        print("\nArea-wise Summary")
        print("-" * 60)

        for area in self.areas.values():

            print(
                f"{area.name:25}"
                f"Inspection : {len(area.observations):3}"
                f"   Thermal : {len(area.thermal_observations):3}"
            )

        print("=" * 60)

    # --------------------------------------------------------

    def save(self, output_path):

        data = {

            "areas": {}

        }

        for area_name, area in self.areas.items():

            data["areas"][area_name] = {

                "inspection": [

                    asdict(obs)

                    for obs in area.observations

                ],

                "thermal": [

                    asdict(obs)

                    for obs in area.thermal_observations

                ]

            }

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(f"\nKnowledge Base saved successfully.")
        print(output_path)

    # --------------------------------------------------------

    def load(self, input_path):

        with open(
            input_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        self.areas = {}
        self.total_observations = 0

        for area_name, area_data in data["areas"].items():

            self.add_area(area_name)

            for obs in area_data["inspection"]:

                observation = Observation(**obs)

                self.areas[area_name].observations.append(
                    observation
                )

                self.total_observations += 1

            for obs in area_data["thermal"]:

                observation = Observation(**obs)

                self.areas[area_name].thermal_observations.append(
                    observation
                )

                self.total_observations += 1

        print("Knowledge Base loaded successfully.")
        