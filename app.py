"""
==========================================================
UrbanRoof AI DDR Generator

Main Application

Pipeline

Inspection PDF
        │
Thermal PDF
        │
PDF Parser
        │
Knowledge Base
        │
Semantic Matcher
        │
LLM Reasoner
        │
Report Generator
        │
DDR Report

Author: Adithya Sapalya
==========================================================
"""

from config import (
    DATA_DIR,
    KNOWLEDGE_BASE_JSON,
    OUTPUT_DIR,
    REPORT_OUTPUT
)

from modules.pdf_parser import PDFParser
from modules.knowledge_base import KnowledgeBase
from modules.semantic_matcher import SemanticMatcher
from modules.llm_reasoner import LLMReasoner
from modules.report_generator import ReportGenerator


def main():

    print("=" * 60)
    print("UrbanRoof AI DDR Generator")
    print("=" * 60)

    inspection_pdf = DATA_DIR / "inspection.pdf"
    thermal_pdf = DATA_DIR / "thermal.pdf"

    # --------------------------------------------------
    # Parse PDFs
    # --------------------------------------------------

    print("\nParsing Inspection PDF...")

    inspection_parser = PDFParser(inspection_pdf)
    inspection_data = inspection_parser.parse_pdf()

    print("\nParsing Thermal PDF...")

    thermal_parser = PDFParser(thermal_pdf)
    thermal_data = thermal_parser.parse_pdf()

    # --------------------------------------------------
    # Build Knowledge Base
    # --------------------------------------------------

    kb = KnowledgeBase()

    #
    # NOTE:
    # Replace these loops if your parser already has
    # a method like parser.build_knowledge_base(kb)
    #

    for page in inspection_data["pages"]:

        for obs in page["observations"]:
             kb.add_observation(

                source="inspection",

                area=page["sections"][0] if page["sections"] else "Unknown",

                page=page["page_number"],

                issue=obs["keyword"],

                description=obs["text"],

                source_evidence=obs["text"],

                bbox=obs["bbox"],

                image_refs=obs.get("image_refs", []),

                confidence=obs.get("confidence", 1.0)

        )

    for page in thermal_data["pages"]:

        for obs in page["observations"]:

            kb.add_observation(

                source="thermal",

                area=page["sections"][0] if page["sections"] else "Unknown",

                page=page["page_number"],

                issue=obs["keyword"],

                description=obs["text"],

                source_evidence=obs["text"],

                bbox=obs["bbox"],

                image_refs=obs.get("image_refs", []),

                confidence=obs.get("confidence", 1.0)
            )


    print("\nKnowledge Base Created")

    kb.summary()
    matcher = SemanticMatcher()
    kb = matcher.run(kb)
    reasoner = LLMReasoner()
    kb, report = reasoner.run(kb)
    kb.save(KNOWLEDGE_BASE_JSON)

    # --------------------------------------------------
    # Semantic Matching
    # --------------------------------------------------

    matcher = SemanticMatcher()

    kb = matcher.run(kb)

    # --------------------------------------------------
    # LLM Reasoning
    # --------------------------------------------------

    reasoner = LLMReasoner()

    kb, report = reasoner.run(kb)

    # --------------------------------------------------
    # Report Generation
    # --------------------------------------------------

    generator = ReportGenerator()

    generator.run(

        kb,

        report,

        REPORT_OUTPUT

    )

    print("\nDone.")

    print(f"\nReport saved at:\n{REPORT_OUTPUT}")


if __name__ == "__main__":

    main()