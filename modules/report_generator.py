"""
==========================================================
UrbanRoof AI DDR Generator

Report Generator

Creates:
- Executive Summary
- Observation Tables
- Recommendations
- Final DDR Report (.docx)

Author: Adithya Sapalya
==========================================================
"""

from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from modules.knowledge_base import KnowledgeBase


class ReportGenerator:

    def __init__(self):

        self.document = Document()

        self.document.styles["Normal"].font.name = "Calibri"
        self.document.styles["Normal"].font.size = Pt(11)

    # -----------------------------------------------------

    def add_title(self):

        heading = self.document.add_heading(
            "Defect Diagnostic Report",
            level=0
        )

        heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        self.document.add_paragraph(
            "UrbanRoof AI DDR Generator"
        )

        self.document.add_page_break()

    # -----------------------------------------------------

    def executive_summary(
        self,
        report
    ):

        self.document.add_heading(
            "Executive Summary",
            level=1
        )

        summary = report["executive_summary"]

        self.document.add_paragraph(
            f"Overall Condition : {summary['overall_condition']}"
        )

        self.document.add_paragraph(
            summary["executive_summary"]
        )

        self.document.add_heading(
            "Priority Actions",
            level=2
        )

        for action in summary["priority_actions"]:

            self.document.add_paragraph(
                action,
                style="List Bullet"
            )
    # -----------------------------------------------------

    def observations_section(

        self,

        kb: KnowledgeBase

    ):

        self.document.add_heading(

            "Inspection Findings",

            level=1

        )

        table = self.document.add_table(

            rows=1,

            cols=6

        )

        table.style = "Table Grid"

        header = table.rows[0].cells

        header[0].text = "Area"

        header[1].text = "Issue"

        header[2].text = "Severity"

        header[3].text = "Root Cause"

        header[4].text = "Recommendation"

        header[5].text = "Match"

        for obs in kb.get_all_observations():

            row = table.add_row().cells

            row[0].text = obs.area

            row[1].text = obs.issue

            row[2].text = obs.severity

            row[3].text = obs.root_cause

            row[4].text = obs.recommendation

            if obs.matched_observation_id is None:

                row[5].text = "-"

            else:

                row[5].text = (

                    f"#{obs.matched_observation_id} "

                    f"({obs.similarity_score:.2f})"

                )

    # -----------------------------------------------------

    def severity_summary(

        self,

        report

    ):

        self.document.add_heading(

            "Severity Summary",

            level=1

        )

        stats = report["severity_statistics"]

        table = self.document.add_table(

            rows=1,

            cols=2

        )

        table.style = "Table Grid"

        header = table.rows[0].cells

        header[0].text = "Severity"

        header[1].text = "Count"

        for severity, count in stats.items():

            row = table.add_row().cells

            row[0].text = severity

            row[1].text = str(count)

        self.document.add_paragraph()

        self.document.add_paragraph(

            f"Overall Building Health Score : {report['health_score']}/100"

        )
    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    def save(

        self,

        output_path

    ):

        output_path = Path(output_path)

        output_path.parent.mkdir(

            parents=True,

            exist_ok=True

        )

        self.document.save(

            output_path

        )

        print(

            f"Report saved -> {output_path}"

        )

    # -----------------------------------------------------
    # Full Pipeline
    # -----------------------------------------------------

    def run(

        self,

        kb: KnowledgeBase,

        report,

        output_path

    ):

        print()

        print("=" * 60)

        print("GENERATING DDR REPORT")

        print("=" * 60)

        self.add_title()

        self.executive_summary(

            report

        )

        self.observations_section(

            kb

        )

        self.severity_summary(

            report

        )

        self.save(

            output_path

        )

        print()

        print("=" * 60)

        print("DDR REPORT GENERATED SUCCESSFULLY")

        print("=" * 60)

        print()

        return output_path