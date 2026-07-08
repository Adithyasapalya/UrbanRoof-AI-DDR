"""
==========================================================
UrbanRoof AI DDR Generator

DOCX Report Generator
==========================================================
"""

from pathlib import Path

from docx import Document
from docx.shared import Inches

from modules.knowledge_base import KnowledgeBase


class ReportGenerator:

    def __init__(self):

        self.document = Document()

    # --------------------------------------------------------

    def heading(self, text, level=1):

        self.document.add_heading(text, level=level)

    # --------------------------------------------------------

    def paragraph(self, text):

        self.document.add_paragraph(str(text))

    # --------------------------------------------------------

    def image(self, image_path):

        image_path = Path(image_path)

        if image_path.exists():

            self.document.add_picture(

                str(image_path),

                width=Inches(5.5)

            )

    # --------------------------------------------------------

    def build(self, kb: KnowledgeBase):

        self.heading(

            "DETAILED DEFECT REPORT",

            0

        )

        self.paragraph(

            "Automatically generated using UrbanRoof AI Pipeline."

        )

        self.heading(

            "Executive Summary",

            1

        )

        self.paragraph(

            f"Inspection Findings : {len(kb.inspection_observations)}"

        )

        self.paragraph(

            f"Thermal Findings : {len(kb.thermal_observations)}"

        )

        self.heading(

            "Matched Observations",

            1

        )

        thermal_lookup = {

            obs.id: obs

            for obs in kb.thermal_observations

        }

        for obs in kb.inspection_observations:

            self.heading(

                obs.area,

                2

            )

            self.paragraph(

                f"Issue : {obs.issue}"

            )

            self.paragraph(

                f"Description : {obs.description}"

            )

            self.paragraph(

                f"Severity : {obs.severity}"

            )

            self.paragraph(

                f"Root Cause : {obs.root_cause}"

            )

            self.paragraph(

                f"Recommendation : {obs.recommendation}"

            )

            self.paragraph(

                f"Similarity : {round(obs.similarity_score or 0,3)}"
            )

            thermal = thermal_lookup.get(

                obs.matched_observation_id

            )

            if thermal:

                self.paragraph(

                    f"Thermal Issue : {thermal.issue}"

                )

            for image in obs.image_refs:

                self.image(image)

            self.document.add_page_break()

    # --------------------------------------------------------

    def save(self, output_path):

        self.document.save(output_path)

        print(f"Report saved -> {output_path}")