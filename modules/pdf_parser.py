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
✔ Extract text blocks
✔ Detect headings
✔ Detect property areas
✔ Extract observations
✔ Extract images
✔ Generate JSON

Author : Adithya Sapalya
===========================================================
"""


from __future__ import annotations


import json
import logging

from dataclasses import dataclass, asdict

from pathlib import Path

from typing import List


import fitz


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
# DATA MODELS
# ==========================================================


@dataclass
class TextSpan:


    text: str

    font: str

    size: float

    flags: int

    bbox: list




@dataclass
class TextBlock:


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
# PDF PARSER
# ==========================================================


class PDFParser:


    def __init__(self, pdf_path):


        self.pdf_path = Path(pdf_path)


        if not self.pdf_path.exists():

            raise FileNotFoundError(
                f"{self.pdf_path} not found"
            )


        logger.info(
            f"Opening {self.pdf_path.name}"
        )


        self.doc = fitz.open(
            self.pdf_path
        )


        self.total_pages = len(
            self.doc
        )


        self.output = {

            "metadata": {},

            "pages": []

        }



    # ======================================================
    # Metadata
    # ======================================================


    def extract_metadata(self):


        meta = self.doc.metadata


        return {


            "file_name":
                self.pdf_path.name,


            "title":
                meta.get("title",""),


            "author":
                meta.get("author",""),


            "creator":
                meta.get("creator",""),


            "page_count":
                self.total_pages

        }



    # ======================================================
    # Heading Detection
    # ======================================================


    def is_heading(self, span):


        text = span.get(
            "text",
            ""
        ).strip()


        if len(text) < 3:

            return False


        size = span.get(
            "size",
            0
        )


        flags = span.get(
            "flags",
            0
        )


        bold = bool(
            flags & 16
        )


        upper_ratio = (
            sum(c.isupper() for c in text)
            /
            max(len(text),1)
        )


        if size >= 14:

            return True


        if bold and size >= 11:

            return True


        if upper_ratio > 0.7:

            return True


        return False
        # ======================================================
    # Extract Text Blocks
    # ======================================================

    def extract_text_blocks(self, page):

        page_dict = page.get_text("dict")

        blocks = []

        headings = []

        block_index = 0

        for block in page_dict["blocks"]:

            if block["type"] != 0:
                continue

            spans = []

            texts = []

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

                    texts.append(text)

            if not spans:
                continue

            merged_text = " ".join(texts)

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

            blocks.append(

                TextBlock(

                    block_no=block_index,

                    text=merged_text,

                    bbox=list(block["bbox"]),

                    spans=spans,

                    is_heading=heading

                )

            )

            block_index += 1

        return blocks, headings


    # ======================================================
    # Extract Images
    # ======================================================

    def extract_images(self, page):

        images = []

        for img in page.get_images(full=True):

            xref = img[0]

            try:

                pix = fitz.Pixmap(self.doc, xref)

                images.append(

                    ImageInfo(

                        xref=xref,

                        width=pix.width,

                        height=pix.height,

                        ext="png",

                        bbox=[]

                    )

                )

            except Exception:

                pass

        return images


    # ======================================================
    # Parse One Page
    # ======================================================

    def parse_page(self, page_number):

        logger.info(f"Parsing Page {page_number + 1}")

        page = self.doc.load_page(page_number)

        blocks, headings = self.extract_text_blocks(page)

        images = self.extract_images(page)

        return PageData(

            page_number=page_number + 1,

            width=page.rect.width,

            height=page.rect.height,

            headings=headings,

            blocks=blocks,

            images=images

        )


    # ======================================================
    # Detect Sections
    # ======================================================

    def detect_sections(self, page_data):

        PROPERTY_AREAS = [

            "Kitchen",

            "Hall",

            "Living Room",

            "Dining",

            "Master Bedroom",

            "Bedroom",

            "Bathroom",

            "Balcony",

            "Terrace",

            "Parking",

            "Utility",

            "Roof",

            "Ceiling",

            "Floor"

        ]

        detected = []

        for block in page_data.blocks:

            text = block.text.lower()

            for room in PROPERTY_AREAS:

                if room.lower() in text and room not in detected:

                    detected.append(room)

        if not detected:

            detected.append("General")

        return detected


    # ======================================================
    # Extract Observations
    # ======================================================

    def extract_observations(self, page_data):

        keywords = [

            "damp",

            "dampness",

            "crack",

            "cracks",

            "leak",

            "leakage",

            "moisture",

            "fungus",

            "paint",

            "tile",

            "corrosion",

            "rust",

            "thermal anomaly",

            "efflorescence"

        ]

        observations = []

        area = self.detect_sections(page_data)[0]

        for block in page_data.blocks:

            lower = block.text.lower()

            for keyword in keywords:

                if keyword in lower:

                    observations.append({

                        "area": area,

                        "issue": keyword.title(),

                        "description": block.text,

                        "text": block.text,

                        "page": page_data.page_number,

                        "bbox": block.bbox,

                        "keyword": keyword,

                        "confidence": 1.0,

                        "image_refs": []

                    })

                    break

        return observations
        # ======================================================
    # Layout Confidence
    # ======================================================

    def calculate_layout_confidence(self, page_data):

        score = 0

        score += len(page_data.headings) * 5
        score += len(page_data.blocks)
        score += len(page_data.images) * 2

        return min(score, 100)


    # ======================================================
    # Convert Page to Dictionary
    # ======================================================

    def page_to_dict(self, page_data):

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

        logger.info("Starting document parsing...")

        self.output["metadata"] = self.extract_metadata()

        pages = []

        for page_number in range(self.total_pages):

            page_data = self.parse_page(page_number)

            pages.append(

                self.page_to_dict(page_data)

            )

        self.output["pages"] = pages

        EXTRACTED_DIR.mkdir(

            parents=True,

            exist_ok=True

        )

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