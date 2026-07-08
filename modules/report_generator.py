"""
==========================================================
UrbanRoof AI DDR Generator

Professional Report Generator

Generates:

• Executive Summary
• Property Issue Summary
• Area-wise Observations
• Severity Assessment
• Recommended Actions
• Additional Notes
• Missing Information
• Building Health Score

Author : Adithya Sapalya
==========================================================
"""

from __future__ import annotations

import os
import tempfile
from collections import defaultdict

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE

from modules.knowledge_base import KnowledgeBase


class ReportGenerator:

    def __init__(self):

        self.document = Document()

        self.document.core_properties.author = "Adithya Sapalya"

        self.document.core_properties.title = "UrbanRoof AI DDR Report"

        self.document.core_properties.subject = "Defect Diagnostic Report"

        self._create_styles()

    # -----------------------------------------------------

    def _create_styles(self):

        styles = self.document.styles

        if "HeadingBlue" not in styles:

            style = styles.add_style(

                "HeadingBlue",

                WD_STYLE_TYPE.PARAGRAPH

            )

            style.font.name = "Calibri"

            style.font.size = Pt(16)

            style.font.bold = True

        if "BodyTextCustom" not in styles:

            style = styles.add_style(

                "BodyTextCustom",

                WD_STYLE_TYPE.PARAGRAPH

            )

            style.font.name = "Calibri"

            style.font.size = Pt(11)

    # -----------------------------------------------------

    def title_page(self):

        title = self.document.add_heading(

            "UrbanRoof AI\nDamage Diagnostic Report",

            level=0

        )

        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p = self.document.add_paragraph()

        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p.add_run(
            "Generated using Artificial Intelligence\n"
        ).bold = True

        p.add_run(
            "Inspection + Thermal Report Analysis"
        )

        self.document.add_page_break()

    # -----------------------------------------------------

    def executive_summary(

        self,

        llm_report

    ):

        self.document.add_heading(

            "1. Executive Summary",

            level=1

        )

        summary = llm_report.get(

            "executive_summary",

            {}

        )

        self.document.add_paragraph(

            summary.get(

                "executive_summary",

                "Not Available"

            )

        )

        self.document.add_paragraph()

        self.document.add_paragraph(

            "Overall Condition : "

            + summary.get(

                "overall_condition",

                "Unknown"

            )

        )

        actions = summary.get(

            "priority_actions",

            []

        )

        if actions:

            self.document.add_heading(

                "Priority Actions",

                level=2

            )

            for action in actions:

                self.document.add_paragraph(

                    action,

                    style="List Bullet"

                )

    # -----------------------------------------------------

    def property_issue_summary(

        self,

        kb: KnowledgeBase

    ):

        self.document.add_heading(

            "2. Property Issue Summary",

            level=1

        )

        issue_count = defaultdict(int)

        severity_count = defaultdict(int)

        for obs in kb.get_all_observations():

            issue_count[obs.issue] += 1

            severity_count[obs.severity] += 1

        table = self.document.add_table(

            rows=1,

            cols=2

        )

        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "Issue"

        hdr[1].text = "Occurrences"

        for issue, count in sorted(issue_count.items()):

            row = table.add_row().cells

            row[0].text = issue

            row[1].text = str(count)
    # -----------------------------------------------------
    # Area-wise Observations
    # -----------------------------------------------------

    def area_wise_observations(self, kb: KnowledgeBase):

        self.document.add_heading(
            "3. Area-wise Observations",
            level=1
        )

        grouped = defaultdict(list)

        for obs in kb.get_all_observations():
            grouped[obs.area].append(obs)

        for area in sorted(grouped.keys()):

            self.document.add_heading(area, level=2)

            observations = grouped[area]

            for index, obs in enumerate(observations, start=1):

                self.document.add_heading(
                    f"Observation {index}",
                    level=3
                )

                table = self.document.add_table(
                    rows=8,
                    cols=2
                )

                table.style = "Table Grid"

                table.cell(0,0).text = "Issue"
                table.cell(0,1).text = obs.issue

                table.cell(1,0).text = "Description"
                table.cell(1,1).text = obs.description

                table.cell(2,0).text = "Severity"
                table.cell(2,1).text = obs.severity

                table.cell(3,0).text = "Root Cause"
                table.cell(3,1).text = (
                    obs.root_cause
                    if obs.root_cause
                    else "Not Available"
                )

                table.cell(4,0).text = "Recommendation"
                table.cell(4,1).text = (
                    obs.recommendation
                    if obs.recommendation
                    else "Not Available"
                )

                table.cell(5,0).text = "Similarity Score"

                table.cell(5,1).text = (
                    f"{obs.similarity_score:.2f}"
                    if obs.similarity_score
                    else "Not Matched"
                )

                table.cell(6,0).text = "Matched Observation"

                table.cell(6,1).text = (
                    str(obs.matched_observation_id)
                    if obs.matched_observation_id is not None
                    else "Not Available"
                )

                table.cell(7,0).text = "Evidence"

                table.cell(7,1).text = (
                    obs.source_evidence
                    if obs.source_evidence
                    else "Not Available"
                )

                # ------------------------------------------
                # Images
                # ------------------------------------------

                self.document.add_paragraph(
                    "Inspection / Thermal Images",
                    style="Heading 4"
                )

                if obs.image_refs:

                    inserted = False

                    for image in obs.image_refs:

                        try:

                            self.document.add_picture(
                                image,
                                width=Inches(4.5)
                            )

                            inserted = True

                        except Exception:

                            pass

                    if not inserted:

                        self.document.add_paragraph(
                            "Image Not Available"
                        )

                else:

                    self.document.add_paragraph(
                        "Image Not Available"
                    )

                self.document.add_paragraph()

            self.document.add_page_break()
    
        # -----------------------------------------------------
    # Severity Assessment
    # -----------------------------------------------------

    def severity_assessment(self, llm_report):

        self.document.add_heading(
            "4. Severity Assessment",
            level=1
        )

        stats = llm_report.get(
            "severity_statistics",
            {}
        )

        table = self.document.add_table(
            rows=1,
            cols=2
        )

        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "Severity"

        hdr[1].text = "Count"

        for severity in [

            "Critical",

            "High",

            "Medium",

            "Low",

            "Unknown"

        ]:

            row = table.add_row().cells

            row[0].text = severity

            row[1].text = str(

                stats.get(

                    severity,

                    0

                )

            )

        self.document.add_paragraph()

        self.document.add_paragraph(

            "Severity is determined using both semantic matching "
            "between inspection and thermal observations together "
            "with AI reasoning over the extracted evidence."

        )

    # -----------------------------------------------------
    # Recommended Actions
    # -----------------------------------------------------

    def recommended_actions(

        self,

        kb: KnowledgeBase

    ):

        self.document.add_heading(

            "5. Recommended Actions",

            level=1

        )

        immediate = []

        planned = []

        monitor = []

        for obs in kb.get_all_observations():

            recommendation = (

                obs.recommendation

                if obs.recommendation

                else "No recommendation available."

            )

            severity = obs.severity.lower()

            if severity in [

                "critical",

                "high"

            ]:

                immediate.append(recommendation)

            elif severity == "medium":

                planned.append(recommendation)

            else:

                monitor.append(recommendation)

        self.document.add_heading(

            "Immediate Action",

            level=2

        )

        if immediate:

            for action in sorted(set(immediate)):

                self.document.add_paragraph(

                    action,

                    style="List Bullet"

                )

        else:

            self.document.add_paragraph(

                "No immediate actions."

            )

        self.document.add_heading(

            "Planned Maintenance",

            level=2

        )

        if planned:

            for action in sorted(set(planned)):

                self.document.add_paragraph(

                    action,

                    style="List Bullet"

                )

        else:

            self.document.add_paragraph(

                "No planned actions."

            )

        self.document.add_heading(

            "Monitoring",

            level=2

        )

        if monitor:

            for action in sorted(set(monitor)):

                self.document.add_paragraph(

                    action,

                    style="List Bullet"

                )

        else:

            self.document.add_paragraph(

                "No monitoring recommendations."

            )

    # -----------------------------------------------------
    # Additional Notes
    # -----------------------------------------------------

    def additional_notes(

        self,

        kb: KnowledgeBase

    ):

        self.document.add_heading(

            "6. Additional Notes",

            level=1

        )

        self.document.add_paragraph(

            "• Inspection observations have been matched against "
            "thermal observations using semantic similarity."

        )

        self.document.add_paragraph(

            "• AI-generated recommendations should be verified "
            "by a qualified structural engineer."

        )

        self.document.add_paragraph(

            "• Multiple observations within the same property "
            "area may indicate a common underlying defect."

        )

        self.document.add_paragraph(

            f"• Total observations analysed : {len(kb.get_all_observations())}"

        )

    # -----------------------------------------------------
    # Missing Information
    # -----------------------------------------------------

    def missing_information(

        self,

        kb: KnowledgeBase

    ):

        self.document.add_heading(

            "7. Missing or Unclear Information",

            level=1

        )

        missing = False

        for obs in kb.get_all_observations():

            if not obs.image_refs:

                self.document.add_paragraph(

                    f"{obs.area} - Image Not Available",

                    style="List Bullet"

                )

                missing = True

            if obs.root_cause == "":

                self.document.add_paragraph(

                    f"{obs.area} - Root Cause Not Available",

                    style="List Bullet"

                )

                missing = True

            if obs.recommendation == "":

                self.document.add_paragraph(

                    f"{obs.area} - Recommendation Not Available",

                    style="List Bullet"

                )

                missing = True

        if not missing:

            self.document.add_paragraph(

                "No missing information detected."

            )

    # -----------------------------------------------------
    # Building Health Score
    # -----------------------------------------------------

    def building_health(

        self,

        llm_report

    ):

        self.document.add_heading(

            "8. Building Health Score",

            level=1

        )

        score = llm_report.get(

            "health_score",

            0

        )

        p = self.document.add_paragraph()

        p.add_run(

            "Overall Building Health Score : "

        ).bold = True

        p.add_run(

            f"{score}/100"

        )

        if score >= 80:

            status = "Excellent"

        elif score >= 60:

            status = "Good"

        elif score >= 40:

            status = "Fair"

        else:

            status = "Poor"

        self.document.add_paragraph(

            f"Overall Building Condition : {status}"

        )

        # -----------------------------------------------------
    # Appendix
    # -----------------------------------------------------

    def appendix(self, kb: KnowledgeBase):

        self.document.add_heading(
            "9. Appendix",
            level=1
        )

        self.document.add_paragraph(
            "Complete list of extracted observations."
        )

        table = self.document.add_table(
            rows=1,
            cols=5
        )

        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "ID"
        hdr[1].text = "Area"
        hdr[2].text = "Issue"
        hdr[3].text = "Severity"
        hdr[4].text = "Matched"

        for obs in kb.get_all_observations():

            row = table.add_row().cells

            row[0].text = str(obs.id)

            row[1].text = obs.area

            row[2].text = obs.issue

            row[3].text = obs.severity

            row[4].text = (
                str(obs.matched_observation_id)
                if obs.matched_observation_id is not None
                else "-"
            )

    # -----------------------------------------------------
    # Generate Complete Report
    # -----------------------------------------------------

    def generate_report(
        self,
        kb: KnowledgeBase,
        llm_report
    ):

        print("\nGenerating DDR Report...")

        self.title_page()

        self.executive_summary(
            llm_report
        )

        self.property_issue_summary(
            kb
        )

        self.area_wise_observations(
            kb
        )

        self.severity_assessment(
            llm_report
        )

        self.recommended_actions(
            kb
        )

        self.additional_notes(
            kb
        )

        self.missing_information(
            kb
        )

        self.building_health(
            llm_report
        )

        self.appendix(
            kb
        )

        print("Report Generated Successfully.")

        return self.document

    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    def save(
        self,
        output_file
    ):

        output_path = os.path.abspath(output_file)
        output_dir = os.path.dirname(output_path) or "."

        os.makedirs(output_dir, exist_ok=True)

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                pass

        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=output_dir,
            suffix=".docx"
        ) as tmp_file:
            temp_path = tmp_file.name

        try:
            self.document.save(temp_path)
            os.replace(temp_path, output_path)
        finally:
            if os.path.exists(temp_path) and not os.path.exists(output_path):
                os.remove(temp_path)

        print(f"Report saved -> {output_path}")

    # -----------------------------------------------------
    # Public Entry Point
    # -----------------------------------------------------

    def run(
        self,
        kb: KnowledgeBase,
        llm_report,
        output_file
    ):

        self.generate_report(
            kb,
            llm_report
        )

        self.save(output_file)

        return self.document