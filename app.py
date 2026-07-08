"""
==========================================================
UrbanRoof AI DDR Generator

Main Pipeline

Author: Adithya Sapalya
==========================================================
"""

from pathlib import Path

from modules.pdf_parser import PDFParser
from modules.knowledge_base import KnowledgeBase
from modules.semantic_matcher import SemanticMatcher
from modules.llm_reasoner import LLMReasoner
from modules.report_generator import ReportGenerator

from config import (
    DATA_DIR,
    REPORT_OUTPUT,
)

# ----------------------------------------------------------
# Input Files
# ----------------------------------------------------------

inspection_pdf = DATA_DIR / "inspection.pdf"
thermal_pdf = DATA_DIR / "thermal.pdf"

# ----------------------------------------------------------
# Parse PDFs
# ----------------------------------------------------------

print("\n==============================")
print("STEP 1 : Parsing PDFs")
print("==============================")

parser = PDFParser()

inspection_data = parser.parse_pdf(inspection_pdf)
thermal_data = parser.parse_pdf(thermal_pdf)

# ----------------------------------------------------------
# Build Knowledge Base
# ----------------------------------------------------------

print("\n==============================")
print("STEP 2 : Building Knowledge Base")
print("==============================")

kb = KnowledgeBase()

kb.load_inspection(inspection_data)
kb.load_thermal(thermal_data)

print(f"Inspection observations : {len(kb.inspection_observations)}")
print(f"Thermal observations    : {len(kb.thermal_observations)}")

# ----------------------------------------------------------
# Semantic Matching
# ----------------------------------------------------------

print("\n==============================")
print("STEP 3 : Semantic Matching")
print("==============================")

matcher = SemanticMatcher()

kb = matcher.run(kb)

# ----------------------------------------------------------
# Gemini Reasoning
# ----------------------------------------------------------

print("\n==============================")
print("STEP 4 : Gemini Reasoning")
print("==============================")

reasoner = LLMReasoner()

kb = reasoner.run(kb)

# ----------------------------------------------------------
# Report Generation
# ----------------------------------------------------------

print("\n==============================")
print("STEP 5 : Report Generation")
print("==============================")

report = ReportGenerator()

report.build(kb)

report.save(REPORT_OUTPUT)

print("\n=====================================")
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=====================================")

print(f"\nReport generated at:\n{REPORT_OUTPUT}")