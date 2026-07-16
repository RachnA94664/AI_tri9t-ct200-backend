from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.services.generation_store import get_generations_by_selection, get_generations_by_node
from app.services.staleness import check_staleness

router = APIRouter(prefix="/generations", tags=["retrieval"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_generations(
    selection_id: int | None = Query(default=None),
    node_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if selection_id is not None:
        records = get_generations_by_selection(selection_id)
    elif node_id is not None:
        records = get_generations_by_node(node_id)
    else:
        raise HTTPException(status_code=400, detail="Provide selection_id or node_id")

    results = []
    for record in records:
        staleness = check_staleness(db, record)
        results.append({**record, "staleness": staleness})
    return results
