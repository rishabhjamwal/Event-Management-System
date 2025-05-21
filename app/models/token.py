# app/models/token.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True, index=True)
    blacklisted_on = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))