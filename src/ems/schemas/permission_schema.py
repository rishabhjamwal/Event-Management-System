# app/schemas/permission.py
from typing import Optional, List, Union
from pydantic import BaseModel, validator, field_validator
from datetime import datetime
import uuid

class PermissionBase(BaseModel):
    role: str    
    @validator('role')
    @classmethod
    def role_must_be_valid(cls, v):
        valid_roles = ['owner', 'editor', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of {valid_roles}')
        return v

class PermissionCreate(PermissionBase):
    user_id: str

class PermissionUpdate(BaseModel):
    role: Optional[str] = None    
    @validator('role')
    @classmethod
    def role_must_be_valid(cls, v):
        if v is not None:
            valid_roles = ['owner', 'editor', 'viewer']
            if v not in valid_roles:
                raise ValueError(f'Role must be one of {valid_roles}')
        return v

class PermissionInDBBase(PermissionBase):
    id: Union[str, uuid.UUID]  # Accept either string or UUID
    event_id: Union[str, uuid.UUID]
    user_id: Union[str, uuid.UUID]
    granted_at: datetime
    granted_by_id: Optional[Union[str, uuid.UUID]] = None
    
    # Include computed fields for the API
    can_view: bool 
    can_edit: bool
    can_delete: bool 
    can_share: bool 
    
    model_config = {"from_attributes": True}
    
    # Convert all UUIDs to strings
    @field_validator('id', 'event_id', 'user_id', 'granted_by_id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class Permission(PermissionInDBBase):
    username: str  # Include the username for display purposes

class UserRolePair(BaseModel):
    user_id: str
    role: str
    
    @field_validator('role')
    @classmethod
    def role_must_be_valid(cls, v):
        valid_roles = ['owner', 'editor', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of {valid_roles}')
        return v

class ShareEventRequest(BaseModel):
    users: List[UserRolePair]