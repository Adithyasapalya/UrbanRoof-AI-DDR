"""
==========================================================
UrbanRoof AI DDR Generator

Central Configuration

Author: Adithya Sapalya
==========================================================
"""

from pathlib import Path
import os

from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()

# ==========================================================
# Base Directory
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# Project Folders
# ==========================================================

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "output"

IMAGE_DIR = BASE_DIR / "images"

EXTRACTED_DIR = BASE_DIR / "extracted"

EMBEDDING_DIR = BASE_DIR / "embeddings"

LOG_DIR = BASE_DIR / "logs"

TEMPLATE_DIR = BASE_DIR / "templates"

# ==========================================================
# Create folders automatically
# ==========================================================

for folder in [

    OUTPUT_DIR,

    IMAGE_DIR,

    EXTRACTED_DIR,

    EMBEDDING_DIR,

    LOG_DIR,

    TEMPLATE_DIR

]:

    folder.mkdir(

        parents=True,

        exist_ok=True

    )

# ==========================================================
# Input PDFs
# ==========================================================

INSPECTION_PDF = DATA_DIR / "inspection.pdf"

THERMAL_PDF = DATA_DIR / "thermal.pdf"

SAMPLE_REPORT_PDF = DATA_DIR / "sample_report.pdf"

# ==========================================================
# JSON Outputs
# ==========================================================

INSPECTION_JSON = EXTRACTED_DIR / "inspection.json"

THERMAL_JSON = EXTRACTED_DIR / "thermal.json"

KNOWLEDGE_BASE_JSON = OUTPUT_DIR / "knowledge_base.json"

MATCHES_FILE = OUTPUT_DIR / "matches.json"

# ==========================================================
# Embeddings
# ==========================================================

INSPECTION_EMBEDDINGS = OUTPUT_DIR / "inspection_embeddings.npy"

THERMAL_EMBEDDINGS = OUTPUT_DIR / "thermal_embeddings.npy"

# ==========================================================
# FAISS Index
# ==========================================================

INSPECTION_INDEX = OUTPUT_DIR / "inspection.index"

THERMAL_INDEX = OUTPUT_DIR / "thermal.index"

INDEX_METADATA = OUTPUT_DIR / "index_metadata.json"

# ==========================================================
# Final Report
# ==========================================================

REPORT_OUTPUT = OUTPUT_DIR / "DDR_Report.docx"

# ==========================================================
# AI Models
# ==========================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

GEMINI_MODEL = "gemini-2.5-pro"

# ==========================================================
# Gemini API
# ==========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================================
# Semantic Matching
# ==========================================================

TOP_K = 3

AUTO_MATCH_THRESHOLD = 0.85

REVIEW_THRESHOLD = 0.70

IGNORE_THRESHOLD = 0.50

SEMANTIC_WEIGHT = 0.75

KEYWORD_WEIGHT = 0.25

# ==========================================================
# Versions
# ==========================================================

PIPELINE_VERSION = "1.0"

PARSER_VERSION = "1.0"

KNOWLEDGE_BASE_VERSION = "1.0"

SEMANTIC_MATCHER_VERSION = "1.0"