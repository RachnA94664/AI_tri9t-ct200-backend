from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class NodeBase(BaseModel):
    heading_number: Optional[str]
    heading_text: str
    level: int
    body_text: str
    content_hash: str
    order_index: int


class NodeSummary(NodeBase):
    id: int
    document_version_id: int
    parent_id: Optional[int]

    class Config:
        from_attributes = True


class NodeDetail(NodeSummary):
    children: List["NodeSummary"] = []


class DocumentVersionOut(BaseModel):
    id: int
    label: str
    source_filename: str
    ingested_at: datetime

    class Config:
        from_attributes = True


NodeDetail.model_rebuild()