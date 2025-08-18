from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    title: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(NoteBase):
    tag_ids: Optional[List[int]] = []


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tag_ids: Optional[List[int]] = None

    model_config = ConfigDict(from_attributes=True)


class NoteRead(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
