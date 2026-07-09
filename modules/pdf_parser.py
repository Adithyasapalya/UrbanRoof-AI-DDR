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


@dataclass
class PageData:
    page_number: int
    width: float
    height: float
    headings: List[str]
    blocks: List[TextBlock]
    images: List[ImageInfo]


class PDFParser:
    """Layout-aware PDF parser wrapper."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        self.document = fitz.open(self.pdf_path)
        self.pages: List[PageData] = []

        # Output directory for extracted assets
        self.output_dir = EXTRACTED_DIR
        self.images_dir = self.output_dir / self.pdf_path.stem / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loaded PDF: {self.pdf_path.name}")

    def extract_text_blocks(self, page):
        blocks = []
        raw_blocks = page.get_text("dict")["blocks"]

        for block_no, block in enumerate(raw_blocks):
            if block.get("type") != 0:
                continue

            spans = []
            full_text = []

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    full_text.append(text)
                    spans.append(
                        TextSpan(
                            text=text,
                            font=span.get("font", ""),
                            size=span.get("size", 0.0),
                            flags=span.get("flags", 0),
                            bbox=list(span.get("bbox", [])),
                        )
                    )

            if not full_text:
                continue

            text = " ".join(full_text)

            avg_size = sum(s.size for s in spans) / len(spans)
            is_heading = avg_size >= 12 or any("bold" in s.font.lower() for s in spans)

            blocks.append(
                TextBlock(
                    block_no=block_no,
                    text=text,
                    bbox=list(block.get("bbox", [])),
                    spans=spans,
                    is_heading=is_heading,
                )
            )

        return blocks

    def extract_images(self, page, page_number: int):
        images = []
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                image_data = self.document.extract_image(xref)
            except Exception as e:
                logger.warning(f"Failed extracting image {xref}: {e}")
                continue

            width = image_data.get("width", 0)
            height = image_data.get("height", 0)
            ext = image_data.get("ext", "png")
            image_path = self.images_dir / f"page_{page_number}_image_{img_index}.{ext}"

            try:
                with open(image_path, "wb") as f:
                    f.write(image_data["image"])
            except Exception as e:
                logger.warning(f"Failed saving image {image_path}: {e}")
                continue

            bbox = []
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    # rects[0] is a Rect object; convert to [x0, y0, x1, y1]
                    r = rects[0]
                    bbox = [r.x0, r.y0, r.x1, r.y1]
            except Exception:
                pass

            images.append(ImageInfo(xref=xref, width=width, height=height, ext=ext, bbox=bbox, path=str(image_path)))

        return images

    def find_nearest_image(self, text_block: TextBlock, images: List[ImageInfo]):
        if not images:
            return None

        block_bbox = text_block.bbox
        if not block_bbox or len(block_bbox) != 4:
            return None

        block_x = (block_bbox[0] + block_bbox[2]) / 2
        block_y = (block_bbox[1] + block_bbox[3]) / 2

        nearest_image = None
        smallest_distance = float("inf")

        for image in images:
            if not image.bbox or len(image.bbox) < 4:
                continue
            img_x = (image.bbox[0] + image.bbox[2]) / 2
            img_y = (image.bbox[1] + image.bbox[3]) / 2
            distance = ((block_x - img_x) ** 2 + (block_y - img_y) ** 2) ** 0.5
            if distance < smallest_distance:
                smallest_distance = distance
                nearest_image = image

        return nearest_image

    def extract_observations(self, page_data: PageData):
        observations = []

        for block in page_data.blocks:
            text = block.text.strip()
            if not text:
                continue

            keywords = [
                "damage",
                "defect",
                "issue",
                "leak",
                "crack",
                "moisture",
                "thermal",
                "repair",
                "recommendation",
                "concern",
                "fault",
            ]

            is_observation = any(keyword in text.lower() for keyword in keywords)
            if not is_observation:
                continue

            matched_image = self.find_nearest_image(block, page_data.images)

            observation = {
                "page": page_data.page_number,

                # Required by DDR generator
                "text": text,

                # Keep description for compatibility
                "description": text,

                "bbox": block.bbox,

                "heading": block.is_heading,

                "image": (
                    matched_image.path
                    if matched_image
                    else None
                ),

                "keyword": None,

                "confidence": 1.0,
            }

            observations.append(observation)

        return observations

    def parse_pdf(self):
        """
        Execute complete PDF parsing pipeline.

        Returns
        -------
        dict
            Parsed PDF structure.
        """

        all_observations = []

        pages_out = []


        for page_number in range(len(self.document)):

            page = self.document[page_number]

            logger.info(
                f"Processing page {page_number + 1}"
            )


            blocks = self.extract_text_blocks(
                page
            )


            images = self.extract_images(
                page,
                page_number + 1
            )


            headings = [
                block.text
                for block in blocks
                if block.is_heading
            ]


            page_data = PageData(
                page_number=page_number + 1,
                width=page.rect.width,
                height=page.rect.height,
                headings=headings,
                blocks=blocks,
                images=images
            )


            observations = self.extract_observations(
                page_data
            )


            page_output = {
        "page_number": page_data.page_number,

        "width": page_data.width,

        "height": page_data.height,

        "headings": page_data.headings,

        # Compatibility with DDR generator
        "sections": page_data.headings,

        "blocks": [
            asdict(block)
            for block in page_data.blocks
        ],

        "images": [
            asdict(image)
            for image in page_data.images
        ],

        "observations": observations
    }


            pages_out.append(
                page_output
            )


            all_observations.extend(
                observations
            )


        result = {
            "pdf": self.pdf_path.name,
            "pages": pages_out,
            "observations": all_observations
        }


        return result
    
    def parse(self):
        return self.parse_pdf()
    
    def save_json(self, data: dict, output_name: str = "parsed_output.json"):
        output_path = self.output_dir / output_name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"JSON saved: {output_path}")
        return output_path