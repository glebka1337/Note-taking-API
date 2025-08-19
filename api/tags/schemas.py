from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TagBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)  

class TagCreate(TagBase):
    user_id: int

class TagRead(TagBase):
    id: int
    model_config = ConfigDict(from_attributes=True)