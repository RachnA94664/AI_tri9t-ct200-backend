from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("SelectionItem", back_populates="selection", cascade="all, delete-orphan")


class SelectionItem(Base):
    """
    A single (node_id, document_version_id) pin. We store the version_id
    explicitly, NOT just node_id, so that if the document is re-ingested
    later (creating new Node rows with new ids), this selection still
    resolves to the EXACT node it was created against — not "whatever
    node currently has this heading_number."
    """
    __tablename__ = "selection_items"

    id = Column(Integer, primary_key=True)
    selection_id = Column(Integer, ForeignKey("selections.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    document_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)

    selection = relationship("Selection", back_populates="items")
    node = relationship("Node")