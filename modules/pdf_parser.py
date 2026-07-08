"""
===========================================================
UrbanRoof AI DDR Generator
Module : pdf_parser.py

Purpose
-------
Layout-aware PDF parser for inspection and thermal reports.

Features
--------
✔ Extract metadata
✔ Extract page text
✔ Preserve reading order
✔ Extract text blocks
✔ Extract font information
✔ Extract coordinates
✔ Detect headings
✔ Extract images
✔ Generate structured JSON

Author : Adithya Sapalya
===========================================================
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF

from config import EXTRACTED_DIR


# ==========================================================
# LOGGER
# ==========================================================

logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s | %(message)s"

)

logger = logging.getLogger(__name__)


# ==========================================================
# DATA CLASSES
# ==========================================================

@dataclass
class TextSpan:
    """
    Smallest text unit.
    """

    text: str

    font: str

    size: float

    flags: int

    bbox: list


@dataclass
class TextBlock:
    """
    Group of spans.
    """

    block_no: int

    text: str

    bbox: list

    spans: List[TextSpan]

    is_heading: bool = False


@dataclass
class ImageInfo:

    xref: int

    width: int

    height: int

    ext: str

    bbox: list


@dataclass
class PageData:

    page_number: int

    width: float

    height: float

    headings: List[str]

    blocks: List[TextBlock]

    images: List[ImageInfo]


# ==========================================================
# MAIN PARSER
# ==========================================================

class PDFParser:

    """
    Layout-aware parser.
    """

    def __init__(self, pdf_path):

        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():

            raise FileNotFoundError(

                f"{self.pdf_path} not found."

            )

        logger.info(

            f"Opening {self.pdf_path.name}"

        )

        self.doc = fitz.open(self.pdf_path)

        self.total_pages = len(self.doc)

        self.output = {

            "metadata": {},

            "pages": []

        }


    # ======================================================

    def extract_metadata(self):

        """
        Extract PDF metadata.
        """

        meta = self.doc.metadata

        return {

            "file_name": self.pdf_path.name,

            "title": meta.get("title", ""),

            "author": meta.get("author", ""),

            "creator": meta.get("creator", ""),

            "producer": meta.get("producer", ""),

            "subject": meta.get("subject", ""),

            "keywords": meta.get("keywords", ""),

            "page_count": self.total_pages

        }
    # ======================================================
    # Heading Detection
    # ======================================================

    def is_heading(self, span: dict) -> bool:
        """
        Determine whether a text span is likely to be a heading.
        """

        text = span.get("text", "").strip()

        if len(text) < 3:
            return False

        size = span.get("size", 0)
        flags = span.get("flags", 0)

        # Bit 16 generally indicates bold in many PDFs
        is_bold = bool(flags & 16)

        upper_ratio = sum(c.isupper() for c in text) / max(len(text), 1)

        # Heuristics
        if size >= 14:
            return True

        if is_bold and size >= 11:
            return True

        if upper_ratio > 0.7 and len(text) < 60:
            return True

        return False


    # ======================================================
    # Text Block Extraction
    # ======================================================

    def extract_text_blocks(self, page: fitz.Page):
        """
        Extract layout-aware text blocks.
        """

        page_dict = page.get_text("dict")

        blocks = []
        headings = []

        block_index = 0

        for block in page_dict["blocks"]:

            if block["type"] != 0:
                continue

            spans = []
            block_text = []

            for line in block.get("lines", []):

                for span in line.get("spans", []):

                    text = span.get("text", "").strip()

                    if not text:
                        continue

                    span_obj = TextSpan(
                        text=text,
                        font=span.get("font", ""),
                        size=span.get("size", 0),
                        flags=span.get("flags", 0),
                        bbox=list(span.get("bbox"))
                    )

                    spans.append(span_obj)

                    block_text.append(text)

            if not spans:
                continue

            merged_text = " ".join(block_text).strip()

            heading = any(
                self.is_heading({
                    "text": s.text,
                    "size": s.size,
                    "flags": s.flags
                })
                for s in spans
            )

            if heading:
                headings.append(merged_text)

            block_obj = TextBlock(
                block_no=block_index,
                text=merged_text,
                bbox=list(block["bbox"]),
                spans=spans,
                is_heading=heading
            )

            blocks.append(block_obj)

            block_index += 1

        return blocks, headings


    # ======================================================
    # Image Extraction (Metadata only)
    # ======================================================

    def extract_images(self, page: fitz.Page):
        """
        Extract image metadata from a page.
        """

        images = []

        image_list = page.get_images(full=True)

        for img in image_list:

            xref = img[0]

            try:
                pix = fitz.Pixmap(self.doc, xref)

                info = ImageInfo(
                    xref=xref,
                    width=pix.width,
                    height=pix.height,
                    ext="png",
                    bbox=[]
                )

                images.append(info)

                pix = None

            except Exception as e:

                logger.warning(
                    f"Image extraction failed (xref={xref}): {e}"
                )

        return images


    # ======================================================
    # Parse One Page
    # ======================================================

    def parse_page(self, page_number: int):
        """
        Parse a single page.
        """

        logger.info(f"Parsing Page {page_number + 1}")

        page = self.doc.load_page(page_number)

        blocks, headings = self.extract_text_blocks(page)

        images = self.extract_images(page)

        page_data = PageData(
            page_number=page_number + 1,
            width=page.rect.width,
            height=page.rect.height,
            headings=headings,
            blocks=blocks,
            images=images
        )

        return page_data
    
    # ======================================================
    # Detect Property Areas / Sections
    # ======================================================

    def detect_sections(self, page_data: PageData):
        """
        Detect property areas like Kitchen, Hall, Bedroom etc.
        """

        PROPERTY_AREAS = [
            "Kitchen",
            "Hall",
            "Living Room",
            "Dining",
            "Master Bedroom",
            "Bedroom",
            "Common Bedroom",
            "Bathroom",
            "Common Bathroom",
            "Toilet",
            "WC",
            "Balcony",
            "Terrace",
            "Parking",
            "Passage",
            "Utility",
            "External Wall",
            "Roof",
            "Ceiling",
            "Floor"
        ]

        detected = []

        for block in page_data.blocks:

            text = block.text.lower()

            for room in PROPERTY_AREAS:

                if room.lower() in text:

                    if room not in detected:
                        detected.append(room)

        if not detected:
            detected.append("General")

        return detected


    # ======================================================
    # Extract Possible Observations
    # ======================================================

def extract_observations(self, page_data: PageData):
    """
    Extract likely inspection observations.
    Returns a richer structure compatible with the Knowledge Base.
    """

    KEYWORDS = [

        "damp",
        "dampness",
        "seepage",
        "leak",
        "leakage",
        "crack",
        "cracks",
        "moisture",
        "fungus",
        "paint",
        "tile",
        "hollow",
        "corrosion",
        "rust",
        "spalling",
        "efflorescence",
        "water ingress",
        "water penetration",
        "thermal anomaly"

    ]

    observations = []

    current_section = "General"

    sections = self.detect_sections(page_data)

    if sections:
        current_section = sections[0]

    for block in page_data.blocks:

        lower = block.text.lower()

        for keyword in KEYWORDS:

            if keyword in lower:

                observations.append({

                    "area": current_section,

                    "issue": keyword.title(),

                    "description": block.text,

                    "text": block.text,

                    "keyword": keyword,

                    "page": page_data.page_number,

                    "bbox": block.bbox,

                    "confidence": 1.0,

                    "is_heading": block.is_heading,

                    "image_refs": []

                })

                break

    return observations


    # ======================================================
    # Layout Confidence Score
    # ======================================================

def calculate_layout_confidence(self, page_data: PageData):
        """
        Simple confidence score based on document richness.
        """

        score = 0

        score += len(page_data.headings) * 5

        score += len(page_data.blocks)

        score += len(page_data.images) * 2

        return min(score, 100)


    # ======================================================
    # Convert Page Object to Dictionary
    # ======================================================

def page_to_dict(self, page_data: PageData):
        """
        Convert dataclasses into JSON serializable dictionary.
        """

        return {

            "page_number": page_data.page_number,

            "width": page_data.width,

            "height": page_data.height,

            "headings": page_data.headings,

            "sections": self.detect_sections(page_data),

            "layout_confidence": self.calculate_layout_confidence(page_data),

            "observations": self.extract_observations(page_data),

            "blocks": [

                {

                    "block_no": block.block_no,

                    "text": block.text,

                    "bbox": block.bbox,

                    "is_heading": block.is_heading,

                    "spans": [

                        asdict(span)

                        for span in block.spans

                    ]

                }

                for block in page_data.blocks

            ],

            "images": [

                asdict(img)

                for img in page_data.images

            ]

        }


    # ======================================================
    # Parse Complete PDF
    # ======================================================

def parse_pdf(self):
    """
    Parse the complete document.
    """

    logger.info("Starting document parsing...")

    self.output["metadata"] = self.extract_metadata()

    pages = []

    for page_number in range(self.total_pages):

        page_data = self.parse_page(page_number)

        pages.append(

            self.page_to_dict(page_data)

        )

    self.output["pages"] = pages

    output_file = EXTRACTED_DIR / f"{self.pdf_path.stem}.json"

    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            self.output,

            f,

            indent=4,

            ensure_ascii=False

        )

    logger.info(f"Saved parsed JSON -> {output_file}")

    logger.info("Document parsing completed.")

    return self.output
