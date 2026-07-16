from sqlalchemy.orm import Session
from app.models.document import Node, DocumentVersion
from app.services.version_matcher import match_nodes


def check_staleness(db: Session, generation: dict) -> dict:
    """
    For each source node recorded at generation time, find its CURRENT
    counterpart in the latest document version (using the same
    heading_number/heading_text matching logic as Phase 3's version
    matcher), then compare content_hash. Comparing against the original
    fixed row is WRONG — that row's hash never changes, since re-ingestion
    creates new rows rather than mutating old ones.

    KNOWN LIMITATION: binary hash comparison — a cosmetic wording fix and
    a safety-critical threshold change both flip is_stale identically.
    """
    latest_version = db.query(DocumentVersion).order_by(DocumentVersion.id.desc()).first()

    stale_nodes = []
    for source_node in generation["source_nodes"]:
        original_node = db.query(Node).filter(Node.id == source_node["node_id"]).first()
        if original_node is None:
            stale_nodes.append({"node_id": source_node["node_id"], "reason": "node_deleted"})
            continue

        if original_node.document_version_id == latest_version.id:
            # this node's own version IS the latest — nothing to compare against
            continue

        # find this node's counterpart in the latest version
        match_results = match_nodes(db, original_node.document_version_id, latest_version.id)
        match = next((r for r in match_results if r.v1_node and r.v1_node.id == original_node.id), None)

        if match is None or match.v2_node is None:
            stale_nodes.append({"node_id": source_node["node_id"], "reason": "node_removed_in_latest_version"})
        elif match.v2_node.content_hash != source_node["content_hash"]:
            stale_nodes.append({"node_id": source_node["node_id"], "reason": "content_changed"})

    return {
        "generation_id": generation["generation_id"],
        "is_stale": len(stale_nodes) > 0,
        "stale_nodes": stale_nodes,
    }