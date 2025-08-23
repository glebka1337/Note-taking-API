from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


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

class NoteChildRead(BaseModel):
    uuid: UUID
    title: str
    model_config = ConfigDict(from_attributes=True)

class NoteTagRead(BaseModel):
    uuid: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class NoteLinkRead(BaseModel):
    linked_note_uuid: UUID
    title: str
    model_config = ConfigDict(from_attributes=True)

class NoteRead(NoteBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    user_id: int
    childer_read: Optional[list["NoteChildRead"]] = Field(default_factory=list)
    tags_read: Optional[List["NoteTagRead"]] = Field(default_factory=list)
    links_read: Optional[List["NoteLinkRead"]] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


    