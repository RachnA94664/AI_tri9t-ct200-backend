import fitz
import pdfplumber
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")


def inspect_with_pymupdf(pdf_path: str):
    print("=" * 100)
    print("PYMUPDF INSPECTION")
    print("=" * 100)

    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc, start=1):

        print(f"\n\nPAGE {page_num}")
        print("-" * 80)

        print("\nRAW TEXT\n")
        print(page.get_text())

        print("\nTEXT BLOCKS\n")

        blocks = page.get_text("dict")["blocks"]

        for block in blocks:

            if "lines" not in block:
                continue

            print("-" * 40)

            for line in block["lines"]:

                for span in line["spans"]:

                    text = span["text"].strip()

                    if not text:
                        continue

                    print(
                        f"Size={span['size']:.1f}"
                        f" Font={span['font']}"
                        f" Flags={span['flags']}"
                        f" Text={text}"
                    )


def inspect_tables(pdf_path: str):
    print("\n")
    print("=" * 100)
    print("PDFPLUMBER TABLE INSPECTION")
    print("=" * 100)

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            tables = page.extract_tables()

            print(f"\nPAGE {page_number}")

            if not tables:
                print("No tables detected.")
                continue

            print(f"{len(tables)} table(s) detected.\n")

            for table_index, table in enumerate(tables, start=1):

                print(f"TABLE {table_index}")

                for row in table:
                    print(row)

                print()


if __name__ == "__main__":

    pdf_file = Path("data/ct200_manual_v1.pdf")

    inspect_with_pymupdf(pdf_file)

    inspect_tables(pdf_file)