from __future__ import annotations

import json
import logging
import re

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
# DATA CLASSES
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
    path: str
    image_number: int


@dataclass
class PageData:
    page_number: int
    width: float
    height: float
    blocks: List[TextBlock]
    images: List[ImageInfo]


# ==========================================================
# PDF PARSER
# ==========================================================

class PDFParser:

    def __init__(self, pdf_path: str):

        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        self.document = fitz.open(self.pdf_path)

        self.pages = []

        self.output_dir = EXTRACTED_DIR

        self.images_dir = (
            self.output_dir/
            self.pdf_path.stem/
            "images"
        )
        self.manual_image_dir = (
            self.output_dir/
            "inspection_photos"
        )

        logger.info(
            f"Loaded PDF : {self.pdf_path.name}"
        )

        # Folder containing manually renamed inspection images
        self.manual_image_dir = (
            self.output_dir /
            "inspection_photos"
        )


# ==========================================================
# TEXT EXTRACTION
# ==========================================================

    def extract_text_blocks(self, page):

        blocks = []

        raw_blocks = page.get_text("dict")["blocks"]

        for block_no, block in enumerate(raw_blocks):

            if block.get("type") != 0:
                continue

            spans = []
            text_parts = []

            for line in block.get("lines", []):

                for span in line.get("spans", []):

                    txt = span.get("text", "").strip()

                    if not txt:
                        continue

                    text_parts.append(txt)

                    spans.append(

                        TextSpan(

                            text=txt,

                            font=span.get("font", ""),

                            size=span.get("size", 0),

                            flags=span.get("flags", 0),

                            bbox=list(span.get("bbox", []))

                        )

                    )

            if not text_parts:
                continue

            full_text = " ".join(text_parts)

            avg_size = sum(
                s.size for s in spans
            ) / len(spans)

            is_heading = (

                avg_size >= 12

                or

                any(
                    "bold" in s.font.lower()
                    for s in spans
                )

            )

            blocks.append(

                TextBlock(

                    block_no=block_no,

                    text=full_text,

                    bbox=list(block["bbox"]),

                    spans=spans,

                    is_heading=is_heading

                )

            )

        return blocks


# ==========================================================
# REPORT SECTION DETECTION
# ==========================================================

    def detect_page_section(
        self,
        blocks,
        current_section
    ):

        page_text = "\n".join(
            b.text.upper()
            for b in blocks
        )

        if "SECTION 1" in page_text:
            return "INTRODUCTION"

        if "SECTION 2" in page_text:
            return "SITE"

        if "SECTION 3" in page_text:
            return "VISUAL"

        if "SECTION 4" in page_text:
            return "ANALYSIS"

        if "SECTION 5" in page_text:
            return "LIMITATION"

        if "DISCLAIMER" in page_text:
            return "DISCLAIMER"

        return current_section
# ==========================================================
# IMAGE LOADER
# ==========================================================

    def extract_images(
        self,
        page,
        page_number: int
    ):

        """
        Inspection Report:
            Uses manually prepared images from
            output/inspection_photos

        Thermal Report:
            Still extracts images from PDF.
        """

        # ------------------------------------------------------
        # INSPECTION REPORT
        # ------------------------------------------------------

        if "inspection" in self.pdf_path.stem.lower():

            return []

        # ------------------------------------------------------
        # THERMAL REPORT
        # ------------------------------------------------------

        images = []

        seen = set()

        for index, img in enumerate(page.get_images(full=True)):

            xref = img[0]

            if xref in seen:
                continue

            seen.add(xref)

            try:
                image = self.document.extract_image(xref)
            except Exception:
                continue

            width = image.get("width", 0)
            height = image.get("height", 0)

            if width < 120 or height < 120:
                continue

            ext = image.get("ext", "png")

            filename = (
                self.images_dir /
                f"page_{page_number}_image_{index}.{ext}"
            )

            with open(filename, "wb") as f:
                f.write(image["image"])

            images.append(

        ImageInfo(

            path=str(filename),

            image_number=index + 1

        )

    )

        return images
    # ==========================================================
    # OBSERVATION EXTRACTION
    # ==========================================================

    def extract_observations(
            self,
            page_data: PageData
        ):

            observations = []

            current_area = "General"

            blocks = page_data.blocks

            for index, block in enumerate(blocks):

                text = block.text.strip()

                if not text:
                    continue

                # --------------------------------------------------
                # AREA HEADING
                # Example:
                # 2.1 Terrace
                # 3.4 Roof Slab
                # --------------------------------------------------

                if re.match(
                    r"^\d+(?:\.\d+)+",
                    text
                ):

                    current_area = re.sub(
                        r"^\d+(?:\.\d+)+\s*",
                        "",
                        text
                    ).strip()

                    continue

                # --------------------------------------------------
                # Observation starts with IMAGE
                # --------------------------------------------------

                if not text.upper().startswith("IMAGE"):
                    continue

                # --------------------------------------------------
                # Collect description
                # --------------------------------------------------

                description_lines = [text]

                for nxt in blocks[index + 1:]:

                    nxt_text = nxt.text.strip()

                    if not nxt_text:
                        continue

                    if nxt_text.upper().startswith("IMAGE"):
                        break

                    if re.match(
                        r"^\d+(?:\.\d+)+",
                        nxt_text
                    ):
                        break

                    description_lines.append(nxt_text)

                description = " ".join(
                    description_lines
                ).strip()

                # --------------------------------------------------
                # IMAGE NUMBER
                # --------------------------------------------------

                image_number = None

                match = re.search(
                    r"IMAGE\s*(\d+)",
                    description,
                    re.IGNORECASE
                )

                if match:

                    image_number = int(
                        match.group(1)
                    )

                # --------------------------------------------------
                # MANUAL IMAGE LOADING
                # image_01.jpg
                # image_02.jpg
                # ...
                # --------------------------------------------------

                image_refs = []

                if image_number is not None:

                    filename = f"image_{image_number:02d}"

                    for ext in (
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".bmp"
                    ):

                        img_path = (
                            self.manual_image_dir /
                            f"{filename}{ext}"
                        )

                        if img_path.exists():

                            image_refs.append(
                                str(img_path)
                            )

                            logger.info(
                                f"Found manual image -> {img_path.name}"
                            )

                            break

                    if not image_refs:

                        logger.warning(
                            f"Manual image not found : {filename}"
                        )

                observations.append(

                    {

                        "page": page_data.page_number,

                        "area": current_area,

                        "text": description,

                        "description": description,

                        "issue": description,

                        "bbox": block.bbox,

                        "heading": False,

                        "severity": None,

                        "images": image_refs,

                        "image_number": image_number,

                        "recommendation": "",

                        "root_cause": "",

                        "confidence": 1.0

                    }

                )

                logger.info(

                    f"Page {page_data.page_number} | "

                    f"IMAGE {image_number} -> {image_refs}"

                )

            logger.info(

                f"Page {page_data.page_number}: "

                f"{len(observations)} observations"

            )

            return observations
    # ==========================================================
    # MAIN PARSER
    # ==========================================================

    def parse_pdf(self):

            self.pages = []

            all_observations = []

            current_section = None

            for page_index in range(len(self.document)):

                page = self.document[page_index]

                logger.info(
                    f"Processing page {page_index + 1}"
                )

                # --------------------------------------
                # TEXT EXTRACTION
                # --------------------------------------

                blocks = self.extract_text_blocks(page)

                current_section = self.detect_page_section(
                    blocks,
                    current_section
                )

                # --------------------------------------
                # IMAGES
                #
                # Inspection PDF:
                #     Uses manual images from
                #     extracted/inspection_photos
                #
                # Thermal PDF:
                #     Uses extracted images
                # --------------------------------------

                images = self.extract_images(
                    page,
                    page_index + 1
                )

                page_data = PageData(

                    page_number=page_index + 1,

                    width=page.rect.width,

                    height=page.rect.height,

                    blocks=blocks,

                    images=images

                )

                observations = []

                if current_section == "ANALYSIS":

                    observations = self.extract_observations(
                        page_data
                    )

                # --------------------------------------
                # SEVERITY
                # --------------------------------------

                for obs in observations:

                    txt = obs["description"].lower()

                    if any(

                        word in txt

                        for word in [

                            "collapse",
                            "unsafe",
                            "structural failure",
                            "major crack"

                        ]

                    ):

                        obs["severity"] = "Critical"

                    elif any(

                        word in txt

                        for word in [

                            "crack",
                            "water",
                            "leak",
                            "rust",
                            "corrosion",
                            "spalling"

                        ]

                    ):

                        obs["severity"] = "High"

                    elif any(

                        word in txt

                        for word in [

                            "thermal",
                            "moisture",
                            "vegetation",
                            "efflorescence",
                            "damp"

                        ]

                    ):

                        obs["severity"] = "Medium"

                    else:

                        obs["severity"] = "Low"

                page_dict = {

                    "page_number": page_index + 1,

                    "section": current_section,

                    "width": page.rect.width,

                    "height": page.rect.height,

                    "blocks": [

                        asdict(block)

                        for block in blocks

                    ],

                    "images": [

                        asdict(image)

                        for image in images

                    ],

                    "observations": observations

                }

                self.pages.append(page_dict)

                all_observations.extend(observations)

            return {

                "pdf": self.pdf_path.name,

                "pages": self.pages,

                "observations": all_observations

            }


    # ==========================================================
    # WRAPPER
    # ==========================================================

    def parse(self):

            return self.parse_pdf()


    # ==========================================================
    # SAVE JSON
    # ==========================================================

    def save_json(

            self,

            data,

            output_name="parsed_output.json"

        ):

            output_path = self.output_dir / output_name

            with open(

                output_path,

                "w",

                encoding="utf-8"

            ) as f:

                json.dump(

                    data,

                    f,

                    indent=4,

                    ensure_ascii=False

                )

            logger.info(
                f"JSON saved -> {output_path}"
            )

            return output_path