# app/schemas/event.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid

class RecurrencePatternBase(BaseModel):
    frequency: str  # 'daily', 'weekly', 'monthly', 'yearly'
    interval: int = 1
    end_date: Optional[datetime] = None
    count: Optional[int] = None
    days_of_week: Optional[list[int]] = None  # 0-6 for Monday-Sunday
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    
    @field_validator('frequency')
    def frequency_must_be_valid(cls, v):
        valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
        if v not in valid_frequencies:
            raise ValueError(f'Frequency must be one of {valid_frequencies}')
        return v

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    @field_validator('end_time')
    @classmethod
    def end_time_after_start_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @field_validator('recurrence_pattern')
    def validate_recurrence(cls, v, info):
        if info.data.get('is_recurring', False) and not v:
            raise ValueError('Recurrence pattern required for recurring events')
        return v

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None

class EventInDBBase(EventBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    current_version: int
    
    model_config = {"from_attributes": True}  # Pydantic v2 style

class Event(EventInDBBase):
    pass