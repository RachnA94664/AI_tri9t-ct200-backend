from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True)
    # human label, e.g. "v1", "v2" — NOT the same as id, so you can
    # re-ingest the same logical version file twice during dev without
    # confusing yourself
    label = Column(String, nullable=False)
    source_filename = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    nodes = relationship("Node", back_populates="document_version")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)

    # self-referential FK — nullable because top-level sections have no parent
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)

    heading_number = Column(String, nullable=True)   # e.g. "2.1.1.1", None for title
    heading_text = Column(String, nullable=False)     # e.g. "Battery Life Under Typical Use"
    level = Column(Integer, nullable=False)           # 0=title, 1=H1, 2=H2, 3=H3, 4=H4...

    body_text = Column(Text, nullable=False, default="")
    content_hash = Column(String, nullable=False)      # sha256 of normalized body_text

    order_index = Column(Integer, nullable=False)      # physical position in document

    document_version = relationship("DocumentVersion", back_populates="nodes")
    parent = relationship("Node", remote_side=[id], backref="children")