from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.base import SessionLocal
from app.models.document import Node, DocumentVersion
from app.schemas.node import NodeSummary, NodeDetail
from app.services.version_matcher import match_nodes, ChangeStatus
from app.services.diff_summary import generate_diff_summary

router = APIRouter(prefix="/browse", tags=["browse"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_version_id(db: Session, version: str) -> int:
    """'latest' resolves to the highest DocumentVersion id (most recently
    ingested). Otherwise version is treated as a label (e.g. 'v1')."""
    if version == "latest":
        dv = db.query(DocumentVersion).order_by(DocumentVersion.id.desc()).first()
    else:
        dv = db.query(DocumentVersion).filter(DocumentVersion.label == version).first()
    if dv is None:
        raise HTTPException(status_code=404, detail=f"No document version found for '{version}'")
    return dv.id


@router.get("/sections", response_model=list[NodeSummary])
def list_sections(version: str = Query(default="latest"), db: Session = Depends(get_db)):
    version_id = resolve_version_id(db, version)
    # top-level sections: level == 1 (root/title is level 0, excluded)
    nodes = (db.query(Node)
             .filter(Node.document_version_id == version_id, Node.level == 1)
             .order_by(Node.order_index)
             .all())
    return nodes


@router.get("/nodes/{node_id}", response_model=NodeDetail)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/search", response_model=list[NodeSummary])
def search_nodes(q: str, version: str = Query(default="latest"), db: Session = Depends(get_db)):
    """
    Uses plain SQL LIKE (case-insensitive) rather than SQLite FTS5, because
    the document is small (~30 nodes) — full-text search's setup cost
    (virtual table, indexing) isn't justified at this scale. Worth
    revisiting if the document set grows significantly.
    """
    version_id = resolve_version_id(db, version)
    pattern = f"%{q}%"
    nodes = (db.query(Node)
             .filter(Node.document_version_id == version_id)
             .filter(or_(Node.heading_text.ilike(pattern), Node.body_text.ilike(pattern)))
             .order_by(Node.order_index)
             .all())
    return nodes


@router.get("/nodes/{node_id}/diff")
def get_node_diff(node_id: int, db: Session = Depends(get_db)):
    """
    Given a node from ANY version, find its counterpart in the adjacent
    version and report whether it changed. Uses the same version_matcher
    logic built in Phase 3, scoped down to a single node's match.
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    versions = db.query(DocumentVersion).order_by(DocumentVersion.id).all()
    version_ids = [v.id for v in versions]
    idx = version_ids.index(node.document_version_id)

    # compare against the NEXT version if one exists, else the PREVIOUS one
    if idx + 1 < len(version_ids):
        other_id = version_ids[idx + 1]
        older_id, newer_id = node.document_version_id, other_id
    elif idx - 1 >= 0:
        other_id = version_ids[idx - 1]
        older_id, newer_id = other_id, node.document_version_id
    else:
        return {"node_id": node_id, "status": "no_other_version", "diff": None}

    results = match_nodes(db, older_id, newer_id)
    match = next((r for r in results if
                  (r.v1_node and r.v1_node.id == node.id) or
                  (r.v2_node and r.v2_node.id == node.id)), None)

    if match is None or match.status == ChangeStatus.UNCHANGED:
        return {"node_id": node_id, "status": "unchanged", "diff": None}

    diff_text = None
    if match.status == ChangeStatus.CHANGED and match.v1_node and match.v2_node:
        diff_text = generate_diff_summary(match.v1_node.body_text, match.v2_node.body_text)

    return {
        "node_id": node_id,
        "status": match.status.value,
        "match_method": match.match_method,
        "diff": diff_text,
    }