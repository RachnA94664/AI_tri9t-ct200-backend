from sqlalchemy.orm import Session
from app.models.document import DocumentVersion, Node
from app.services.tree_builder import TreeNode


def persist_tree(db: Session, root: TreeNode, label: str, source_filename: str) -> DocumentVersion:
    doc_version = DocumentVersion(label=label, source_filename=source_filename)
    db.add(doc_version)
    db.flush()  # get doc_version.id without committing yet

    def _persist(node: TreeNode, parent_db_id):
        db_node = Node(
            document_version_id=doc_version.id,
            parent_id=parent_db_id,
            heading_number=node.heading_number,
            heading_text=node.heading_text,
            level=node.level,
            body_text=node.body_text,
            content_hash=node.content_hash,
            order_index=node.order_index,
        )
        db.add(db_node)
        db.flush()  # get db_node.id for children
        for child in node.children:
            _persist(child, db_node.id)

    _persist(root, parent_db_id=None)
    db.commit()
    return doc_version