import fitz  # pymupdf
from app.services.tree_builder import RawBlock


def extract_blocks(pdf_path: str) -> list[RawBlock]:
    doc = fitz.open(pdf_path)
    blocks: list[RawBlock] = []
    order_index = 0

    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    is_bold = bool(span["flags"] & 2**4)
                    blocks.append(RawBlock(
                        text=text,
                        size=round(span["size"], 1),
                        bold=is_bold,
                        order_index=order_index,
                    ))
                    order_index += 1

    doc.close()
    return blocks