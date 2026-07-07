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