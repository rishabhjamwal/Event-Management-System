# app/schemas/version.py
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid

class EventVersionBase(BaseModel):
    version_number: int
    data: Dict[str, Any]
    change_description: Optional[str] = None

class EventVersionCreate(EventVersionBase):
    pass

class EventVersion(EventVersionBase):
    id: Union[str, uuid.UUID]
    event_id: Union[str, uuid.UUID]
    created_by_id: Union[str, uuid.UUID]
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    # Convert UUIDs to strings
    @field_validator('id', 'event_id', 'created_by_id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class ChangelogBase(BaseModel):
    action: str
    version_from: Optional[int] = None
    version_to: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None

class ChangelogCreate(ChangelogBase):
    pass

class Changelog(ChangelogBase):
    id: Union[str, uuid.UUID]
    event_id: Union[str, uuid.UUID]
    user_id: Union[str, uuid.UUID]
    timestamp: datetime
    username: str  # Added for display purposes
    
    model_config = {"from_attributes": True}
    
    # Convert UUIDs to strings
    @field_validator('id', 'event_id', 'user_id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class DiffResponse(BaseModel):
    event_id: str
    version1: int
    version2: int
    diff: Dict[str, Any]