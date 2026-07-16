import sys
from app.db.base import SessionLocal, Base, engine
from app.services.pdf_extract import extract_blocks
from app.services.tree_builder import build_tree
from app.services.ingest import persist_tree

DOC_TITLE = "CardioTrack CT-200 Home Blood Pressure Monitor — Technical & User Manual"


def main(pdf_path: str, label: str):
    Base.metadata.create_all(bind=engine)  # creates tables if they don't exist
    blocks = extract_blocks(pdf_path)
    root = build_tree(blocks, DOC_TITLE)

    db = SessionLocal()
    try:
        doc_version = persist_tree(db, root, label=label, source_filename=pdf_path)
        print(f"Ingested '{label}' as DocumentVersion id={doc_version.id}")
    finally:
        db.close()


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "data/ct200_manual_v1.pdf"
    label = sys.argv[2] if len(sys.argv) > 2 else "v1"
    main(pdf_path, label)