# app/models/permission.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class EventPermission(Base):
    __tablename__ = "event_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role = Column(String)  # 'owner', 'editor', 'viewer'
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
        
    # Relationships
    event = relationship("Event", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], back_populates="event_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    
    __table_args__ = (
        UniqueConstraint('event_id', 'user_id', name='event_user_uc'),
    )

    @property
    def can_view(self):
        # All roles can view
        return True
    
    @property
    def can_edit(self):
        # Editor and owner can edit
        return self.role in ['editor', 'owner']
    
    @property
    def can_delete(self):
        # Only owner can delete
        return self.role == 'owner'
    
    @property
    def can_share(self):
        # Only owner can share
        return self.role == 'owner'