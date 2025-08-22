from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    title: str
    content: str
    parent_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class NoteRead(NoteBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    user_id: int
    model_config = ConfigDict(from_attributes=True)


    