# app/schemas/token.py
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    user: dict
    

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
