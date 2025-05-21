# app/schemas/__init__.py
# Import schemas for easier access
from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.schemas.token import Token, TokenPayload
from app.schemas.event import Event, EventCreate, EventUpdate

# Add other schemas as they are created