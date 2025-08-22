
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class FolderBase(BaseModel):
    title: str = Field(..., max_length=100)


class FolderCreate(FolderBase):
    parent_id: Optional[int] = None  


class FolderUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[int] = None


class FolderRead(FolderBase):
    id: int
    slug: str
    parent_id: Optional[int] = None
    children: List["FolderRead"] = [] 

    
