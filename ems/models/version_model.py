# app/models/version.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ems.db.base import Base

class EventVersion(Base):
    __tablename__ = "event_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True)
    version_number = Column(Integer, index=True)
    data = Column(JSON)  # Store complete event data as JSON
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    change_description = Column(String, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="versions")
    created_by = relationship("User")
    
    class Meta:
        unique_together = (("event_id", "version_number"),)

class EventChangelog(Base):
    __tablename__ = "event_changelogs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    action = Column(String)  # 'create', 'update', 'rollback'
    version_from = Column(Integer, nullable=True)
    version_to = Column(Integer, nullable=True)
    changes = Column(JSON, nullable=True)  # Store the diff as JSON
    
    # Relationships
    event = relationship("Event", back_populates="changelogs")
    user = relationship("User")