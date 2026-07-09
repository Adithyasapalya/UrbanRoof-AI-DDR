from __future__ import annotations

from curses import pair_number
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
    
    def detect_page_section(
    self,
    blocks,
    current_section
):
        """
        Detect which report section this page belongs to.
        """

        page_text = "\n".join(
            block.text.upper()
            for block in blocks
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

        if "LEGAL DISCLAIMER" in page_text:
            return "DISCLAIMER"

        return current_section
    
    def extract_analysis_observations(self,page_data: PageData):
        observations = []

        used_image = set()
        

        """
        Will be implemented next.
        """

        return []

    def extract_images(self, page, page_number: int):
        seen = set()
        images = []
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            if xref in seen:
                continue
            seen.add(xref)
            try:
                image_data = self.document.extract_image(xref)
            except Exception as e:
                logger.warning(f"Failed extracting image {xref}: {e}")
                continue

            width = image_data.get("width", 0)
            height = image_data.get("height", 0)

# ----------------------------------------
# Ignore UrbanRoof template graphics
# ----------------------------------------

            # Header banner
            # Ignore logos/icons
            if width < 400 or height < 300:
                continue

            ratio = width / height

# Ignore long header banners
            if ratio > 5:
                continue
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
            logger.info(
            f"Keeping image | Page {page_number} | "
            f"{width}x{height}"
            )

        return images


    def find_nearest_image(self, block, images):
        """
        Returns the closest image below the IMAGE caption.
        """

        if not images:
            return None

        bx0, by0, bx1, by1 = block.bbox

        best = None
        best_score = float("inf")

        for image in images:

            if not image.bbox:
                continue

            ix0, iy0, ix1, iy1 = image.bbox

        # Prefer images below the caption
            if iy0 < by0 - 20:
                continue

            dx = abs(ix0 - bx0)
            dy = abs(iy0 - by1)

            score = dx + dy

            if score < best_score:
                best_score = score
                best = image

        return best
    
    def find_best_evidence_image(
        self,
        text_block: TextBlock,
        images: List[ImageInfo]
    ):

        candidates = []

        for image in images:

            if not image.bbox:
                continue


            area = (
                image.width *
                image.height
            )


            if image.width < 500:
                continue

            if image.height < 300:
                continue


            block_y = text_block.bbox[1]

            image_y = image.bbox[1]


            distance = abs(
                image_y - block_y
            )


            candidates.append(
                (
                    distance,
                    image
                )
            )


        if not candidates:
            return None


        candidates.sort(
            key=lambda x: x[0]
        )


        return candidates[0][1]


    def extract_observations(self, page_data: PageData):
        """
        Extract observations from UrbanRoof inspection reports.
        """

        observations = []

        current_area = "Unknown"

        used_images = set()

        for block in page_data.blocks:

            text = block.text.strip()

            if not text:
                continue

            # ----------------------------------------
            # Detect Area Heading
            # ----------------------------------------

            if re.match(r"^\d+(\.\d+)+", text):

                current_area = re.sub(
                    r"^\d+(\.\d+)+\s*",
                    "",
                    text
                ).title()

                continue

            # ----------------------------------------
            # IMAGE xx:
            # ----------------------------------------

            if text.upper().startswith("IMAGE"):

                description_lines = [text]

                start = page_data.blocks.index(block)

                for nxt in page_data.blocks[start + 1:]:

                    t = nxt.text.strip()

                    if not t:
                        continue

                    if re.match(r"^\d+(\.\d+)+", t):
                        break

                    if t.upper().startswith("IMAGE"):
                        break

                    description_lines.append(t)

                description = " ".join(description_lines)

                # ----------------------------------------
                # Match nearest image
                # ----------------------------------------

                matched = self.find_nearest_image(
                    block,
                    page_data.images
                )
                image_path = None
                if matched:
                    image_path = matched.path
                if matched and matched.path in used_images:
                    matched = None

                if matched:
                    used_images.add(matched.path)

                image_path = matched.path if matched else None

                observations.append(
                    {
                        "page": page_data.page_number,
                        "area": current_area,
                        "text": description,
                        "description": description,
                        "issue": description,
                        "severity": None,
                        "bbox": block.bbox,
                        "heading": False,
                        "image": image_path,
                        "images": [image_path] if image_path else [],
                        "recommendation": "",
                        "root_cause": "",
                        "confidence": 1.0,
                    }
                )

        logger.info(
            f"Page {page_data.page_number}: extracted {len(observations)} observations"
        )

        return observations

    def parse_pdf(self):
        """
        Main parsing pipeline.
        """

        self.pages = []

        all_observations = []

        current_section = None

        for page_index in range(len(self.document)):

            page = self.document[page_index]

            logger.info(f"Processing page {page_index + 1}")

            blocks = self.extract_text_blocks(page)

            images = self.extract_images(page, page_index + 1)

            current_section = self.detect_page_section(
                blocks,
                current_section
            )

            page_data = PageData(
                page_number=page_index + 1,
                width=page.rect.width,
                height=page.rect.height,
                headings=[],
                blocks=blocks,
                images=images
            )

            observations = []

            if current_section == "ANALYSIS":

                observations = self.extract_observations(page_data)

                # -------------------------------
                # Assign severity
                # -------------------------------

            for obs in observations:

                txt = obs["description"].lower()

                if any(x in txt for x in [
                        "crack",
                        "structural",
                        "collapse"
                    ]):
                        obs["severity"] = "High"

                elif any(x in txt for x in [
                        "leak",
                        "water",
                        "seepage"
                    ]):
                        obs["severity"] = "High"

                elif any(x in txt for x in [
                        "moisture",
                        "thermal",
                        "vegetation",
                        "hollow"
                    ]):
                        obs["severity"] = "Medium"

                else:
                        obs["severity"] = "Low"

            page_dict = {
                        "page_number": page_index + 1,
                        "section": current_section,
                        "width": page.rect.width,
                        "height": page.rect.height,
                        "blocks": [
                            asdict(b)
                            for b in blocks
                        ],
                "images": [
                            asdict(i)
                            for i in images
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
    
    def parse(self):
        return self.parse_pdf()
    
    def save_json(self, data: dict, output_name: str = "parsed_output.json"):
        output_path = self.output_dir / output_name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"JSON saved: {output_path}")
        return output_path