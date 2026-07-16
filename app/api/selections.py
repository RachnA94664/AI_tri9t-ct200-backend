from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.document import Node, DocumentVersion
from app.models.selection import Selection, SelectionItem
from app.schemas.selection import SelectionCreate, SelectionOut

router = APIRouter(prefix="/selections", tags=["selections"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=SelectionOut)
def create_selection(payload: SelectionCreate, db: Session = Depends(get_db)):
    if not payload.node_ids:
        raise HTTPException(status_code=400, detail="node_ids cannot be empty")

    selection = Selection(name=payload.name)
    db.add(selection)
    db.flush()

    for node_id in payload.node_ids:
        node = db.query(Node).filter(Node.id == node_id).first()
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        # PIN the node's CURRENT document_version_id at creation time —
        # this is what makes the selection survive later re-ingestion.
        item = SelectionItem(
            selection_id=selection.id,
            node_id=node.id,
            document_version_id=node.document_version_id,
        )
        db.add(item)

    db.commit()
    db.refresh(selection)
    return _to_selection_out(db, selection)


@router.get("/{selection_id}", response_model=SelectionOut)
def get_selection(selection_id: int, db: Session = Depends(get_db)):
    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if selection is None:
        raise HTTPException(status_code=404, detail="Selection not found")
    return _to_selection_out(db, selection)


def _to_selection_out(db: Session, selection: Selection) -> SelectionOut:
    items_out = []
    for item in selection.items:
        node = db.query(Node).filter(Node.id == item.node_id).first()
        items_out.append({
            "node_id": item.node_id,
            "document_version_id": item.document_version_id,
            "heading_text": node.heading_text if node else "(deleted node)",
            "heading_number": node.heading_number if node else None,
            "body_text": node.body_text if node else "",
        })
    return SelectionOut(id=selection.id, name=selection.name,
                         created_at=selection.created_at, items=items_out)