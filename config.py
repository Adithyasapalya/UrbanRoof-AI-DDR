from pathlib import Path

# ----------------------------------
# Project Paths
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "output"

IMAGE_DIR = BASE_DIR / "images"

EMBEDDING_DIR = BASE_DIR / "embeddings"

EXTRACTED_DIR = BASE_DIR / "extracted"

TEMPLATE_DIR = BASE_DIR / "templates"

MODULE_DIR = BASE_DIR / "modules"

# ----------------------------------

for folder in [

    DATA_DIR,

    OUTPUT_DIR,

    IMAGE_DIR,

    EMBEDDING_DIR,

    EXTRACTED_DIR,

]:

    folder.mkdir(exist_ok=True)

# ----------------------------------

GEMINI_MODEL = "gemini-2.5-pro"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ==========================================================
# Pipeline Versions
# ==========================================================

PIPELINE_VERSION = "1.0.0"

PARSER_VERSION = "2.0"

KNOWLEDGE_BASE_VERSION = "2.0"

SEMANTIC_MATCHER_VERSION = "1.0"

REPORT_GENERATOR_VERSION = "1.0"

# ==========================================================
# Matching Configuration
# ==========================================================

TOP_K = 3

AUTO_MATCH_THRESHOLD = 0.90

REVIEW_THRESHOLD = 0.70

IGNORE_THRESHOLD = 0.55

# Hybrid Matching Weights
KEYWORD_WEIGHT = 0.40

SEMANTIC_WEIGHT = 0.60

# ==========================================================
# Output Files
# ==========================================================

INSPECTION_EMBEDDINGS = EMBEDDING_DIR / "inspection_embeddings.npy"

THERMAL_EMBEDDINGS = EMBEDDING_DIR / "thermal_embeddings.npy"

INSPECTION_INDEX = EMBEDDING_DIR / "inspection.index"

THERMAL_INDEX = EMBEDDING_DIR / "thermal.index"

MATCHES_FILE = OUTPUT_DIR / "matches.json"

INDEX_METADATA = OUTPUT_DIR / "index_metadata.json"

KNOWLEDGE_BASE_FILE = OUTPUT_DIR / "knowledge_base.json"
