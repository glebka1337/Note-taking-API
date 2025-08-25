from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TagBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)  

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: int
    uuid: UUID
    model_config = ConfigDict(from_attributes=True)