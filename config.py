import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY=os.getenv("REMOVED_SECRET")

GEMINI_MODEL="gemini-2.5-pro"
REPORT_OUTPUT = OUTPUT_DIR / "DDR_Report.docx"