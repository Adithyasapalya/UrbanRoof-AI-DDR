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
✔ Extract and save images
✔ Associate images with observations
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

    path: str = ""

    center_x: float = 0.0

    center_y: float = 0.0





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


    def __init__(
            self,
            pdf_path,
            report_type="inspection"
    ):


        self.pdf_path = Path(
            pdf_path
        )


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



        self.report_type = report_type



        self.output = {


            "metadata": {},


            "pages": []


        }




        # ==================================================
        # Image folders
        # ==================================================


        self.image_root = Path(
            "output/images"
        )



        self.inspection_image_dir = (

            self.image_root
            /
            "inspection"

        )



        self.thermal_image_dir = (

            self.image_root
            /
            "thermal"

        )



        self.inspection_image_dir.mkdir(

            parents=True,

            exist_ok=True

        )



        self.thermal_image_dir.mkdir(

            parents=True,

            exist_ok=True

        )



        logger.info(

            f"Report type: {self.report_type}"

        )
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

    def extract_images(

            self,

            page,

            page_number

    ):

        """
        Extract every image from a page and save it.

        Images are stored under:

            output/images/inspection/

            output/images/thermal/

        """

        images = []

        if self.report_type.lower() == "thermal":

            save_dir = self.thermal_image_dir

        else:

            save_dir = self.inspection_image_dir

        image_list = page.get_images(full=True)

        for image_index, img in enumerate(image_list):

            xref = img[0]

            try:

                pix = fitz.Pixmap(

                    self.doc,

                    xref

                )

                if pix.alpha:

                    pix = fitz.Pixmap(

                        fitz.csRGB,

                        pix

                    )

                filename = (

                    f"page_{page_number}_"

                    f"image_{image_index}.png"

                )

                image_path = save_dir / filename

                pix.save(

                    image_path

                )

                pix = None

                image_rects = page.get_image_rects(xref)

                if image_rects:

                    rect = image_rects[0]

                    bbox = [

                        rect.x0,

                        rect.y0,

                        rect.x1,

                        rect.y1

                    ]

                    center_x = (rect.x0 + rect.x1) / 2

                    center_y = (rect.y0 + rect.y1) / 2

                else:

                    bbox = []

                    center_x = 0

                    center_y = 0

                image_info = ImageInfo(

                    xref=xref,

                    width=img[2],

                    height=img[3],

                    ext="png",

                    bbox=bbox,

                    path=str(image_path),

                    center_x=center_x,

                    center_y=center_y

                )

                images.append(

                    image_info

                )

                logger.info(

                    f"Saved image: {image_path}"

                )

            except Exception as e:

                logger.warning(

                    f"Failed extracting image {xref}: {e}"

                )

        return images


    # ======================================================
    # Parse One Page
    # ======================================================

    def parse_page(

            self,

            page_number

    ):

        logger.info(

            f"Parsing Page {page_number + 1}"

        )


        page = self.doc.load_page(

            page_number

        )


        blocks, headings = self.extract_text_blocks(

            page

        )


        images = self.extract_images(

            page,

            page_number + 1

        )


        return PageData(

            page_number=page_number + 1,

            width=page.rect.width,

            height=page.rect.height,

            headings=headings,

            blocks=blocks,

            images=images

        )
        # ======================================================
    # Extract Observations
    # ======================================================

    def extract_observations(
            self,
            page_data
    ):
        """
        Extract observations from page text and associate
        page images with each observation.
        """

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

        area = self.detect_sections(
            page_data
        )[0]



        # --------------------------------------------------
        # Images on this page
        # --------------------------------------------------

        page_images = [

            image.path

            for image in page_data.images

        ]


        for block in page_data.blocks:

            lower = block.text.lower()

            for keyword in keywords:

                if keyword in lower:

                    observations.append(

                        {

                            "area": area,

                            "issue": keyword.title(),

                            "description": block.text,

                            "text": block.text,

                            "page": page_data.page_number,

                            "bbox": block.bbox,

                            "keyword": keyword,

                            "confidence": 1.0,

                            # Images attached automatically
                            "image_refs": page_images

                        }

                    )

                    break


        return observations



    # ======================================================
    # Convert Page to Dictionary
    # ======================================================

    def page_to_dict(
            self,
            page_data
    ):

        return {

            "page_number":
                page_data.page_number,

            "width":
                page_data.width,

            "height":
                page_data.height,

            "headings":
                page_data.headings,

            "sections":
                self.detect_sections(
                    page_data
                ),

            "layout_confidence":
                self.calculate_layout_confidence(
                    page_data
                ),

            "observations":
                self.extract_observations(
                    page_data
                ),

            "blocks":[

                {

                    "block_no":
                        block.block_no,

                    "text":
                        block.text,

                    "bbox":
                        block.bbox,

                    "is_heading":
                        block.is_heading,

                    "spans":[

                        asdict(span)

                        for span in block.spans

                    ]

                }

                for block in page_data.blocks

            ],

            "images":[

                {

                    "xref":
                        image.xref,

                    "width":
                        image.width,

                    "height":
                        image.height,

                    "ext":
                        image.ext,

                    "bbox":
                        image.bbox,

                    "path":
                        image.path

                }

                for image in page_data.images

            ]

        }



    # ======================================================
    # Metadata and layout helpers
    # ======================================================

    def extract_metadata(self):

        metadata = self.doc.metadata or {}

        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "pages": self.total_pages,
            "file_name": self.pdf_path.name,
            "report_type": self.report_type,
        }

    def is_heading(self, span):

        text = (span.get("text", "") or "").strip()

        if not text:
            return False

        size = span.get("size", 0) or 0
        flags = span.get("flags", 0) or 0

        if len(text.split()) <= 6 and (size >= 14 or text.isupper() or text.istitle()):
            return True

        if flags & 2**4:
            return True

        return False

    def detect_sections(self, page_data):

        headings = [heading for heading in page_data.headings if heading.strip()]

        if headings:
            return [headings[0]]

        return ["Unknown"]

    def calculate_layout_confidence(self, page_data):

        if not page_data.blocks:
            return 0.0

        return 0.85

    # ======================================================
    # Parse Complete PDF
    # ======================================================

    def parse_pdf(self):

            logger.info(
                "Starting document parsing..."
            )

            self.output["metadata"] = (
                self.extract_metadata()
            )

            pages = []

            for page_number in range(
                self.total_pages
            ):

                page_data = self.parse_page(
                    page_number
                )

                pages.append(

                    self.page_to_dict(
                        page_data
                    )

                )


            self.output["pages"] = pages


            EXTRACTED_DIR.mkdir(

                parents=True,

                exist_ok=True

            )


            output_file = (

                EXTRACTED_DIR
                /
                f"{self.pdf_path.stem}.json"

            )


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


            logger.info(

                f"Saved parsed JSON -> {output_file}"

            )

            logger.info(

                "Document parsing completed."

            )

            return self.output