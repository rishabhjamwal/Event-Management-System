# app/services/auth.py
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, is_token_blacklisted
from app.models.token import TokenBlacklist
from app.services import user as user_service

def login(db: Session, username_or_email: str, password: str):
    user = user_service.authenticate(db, username_or_email=username_or_email, password=password)
    if not user:
        return None
    if not user.is_active:
        return None
    
    # Update last login
    user_service.update_last_login(db, user=user)
    
    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

def refresh_token(db: Session, token: str):
    try:
        from jose import jwt
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            return None
        
        if is_token_blacklisted(db, token):
            return None
        
        user_id = int(payload.get("sub"))
        user = user_service.get_by_id(db, user_id)
        
        if not user or not user.is_active:
            return None
        
        access_token = create_access_token(user.id)
        
        # Add the user field to match the Token schema
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    except Exception as e:
        print(f"Error in refresh_token: {e}")  # Add debugging
        return None

def logout(db: Session, token: str):
    try:
        from jose import jwt
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        
        expire = datetime.fromtimestamp(payload.get("exp"))
        
        # Add token to blacklist
        db_obj = TokenBlacklist(
            token=token,
            expires_at=expire
        )
        db.add(db_obj)
        db.commit()
        
        return True
    except:
        return False