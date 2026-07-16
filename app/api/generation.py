from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.selection import Selection
from app.models.document import Node
from app.services.llm_client import generate_test_cases
from app.services.generation_store import save_generation, get_existing_generation_for_selection

router = APIRouter(prefix="/generations", tags=["generation"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/selections/{selection_id}")
def generate_for_selection(
    selection_id: int,
    force: bool = Query(default=False, description="Regenerate even if a generation already exists"),
    db: Session = Depends(get_db),
):
    """
    Duplicate-submission policy: if a generation already exists for this
    selection and force=False (default), return the EXISTING generation
    rather than calling the LLM again. Rationale: the selection is pinned
    to specific node+version text, so re-submitting the same selection
    means re-deriving output from IDENTICAL source text — regenerating by
    default would burn API cost/time for no new information. force=True
    lets a user explicitly request a fresh generation (e.g. to get
    different phrasing, or after improving the prompt).
    """
    selection = db.query(Selection).filter(Selection.id == selection_id).first()
    if selection is None:
        raise HTTPException(status_code=404, detail="Selection not found")

    if not force:
        existing = get_existing_generation_for_selection(selection_id)
        if existing:
            return {"status": "existing_generation_returned", **existing}

    source_nodes = []
    text_parts = []
    for item in selection.items:
        node = db.query(Node).filter(Node.id == item.node_id).first()
        if node is None:
            continue
        source_nodes.append({"node_id": node.id, "content_hash": node.content_hash})
        text_parts.append(f"### {node.heading_number} {node.heading_text}\n{node.body_text}")

    if not text_parts:
        raise HTTPException(status_code=400, detail="Selection has no resolvable source nodes")

    combined_text = "\n\n".join(text_parts)

    try:
        result = generate_test_cases(combined_text)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}")

    record = save_generation(
        selection_id=selection_id,
        source_nodes=source_nodes,
        test_cases=[tc.model_dump() for tc in result.test_cases],
    )
    return {"status": "generated", **record}