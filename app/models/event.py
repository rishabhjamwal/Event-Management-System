# app/models/event.py
import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Store recurrence rules as JSON
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    current_version = Column(Integer, default=1)
    
    # Relationships
    owner = relationship("User", back_populates="events")
    permissions = relationship("EventPermission", back_populates="event", cascade="all, delete-orphan")
    versions = relationship("EventVersion", back_populates="event", cascade="all, delete-orphan")
    changelogs = relationship("EventChangelog", back_populates="event", cascade="all, delete-orphan")
