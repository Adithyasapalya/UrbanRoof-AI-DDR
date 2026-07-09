import fitz

pdf = "data/inspection.pdf"

doc = fitz.open(pdf)

print(
    "Pages:",
    len(doc)
)

total = 0

for page_no, page in enumerate(doc, start=1):

    images = page.get_images(full=True)

    print(
        f"\nPage {page_no}: {len(images)} images"
    )

    for idx, img in enumerate(images):

        xref = img[0]

        info = doc.extract_image(xref)

        width = info["width"]
        height = info["height"]

        print(
            f"  Image {idx}: "
            f"{width}x{height} "
            f"{info['ext']}"
        )

        total += 1


print(
    "\nTotal embedded images:",
    total
)