from pydantic import BaseModel
from typing import List
from datetime import datetime


class SelectionCreate(BaseModel):
    name: str
    node_ids: List[int]  # resolved to CURRENT version at creation time


class SelectionItemOut(BaseModel):
    node_id: int
    document_version_id: int
    heading_text: str
    heading_number: str | None
    body_text: str

    class Config:
        from_attributes = True


class SelectionOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    items: List[SelectionItemOut]

    class Config:
        from_attributes = True