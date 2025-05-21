# app/api/deps.py
from typing import Generator, Optional, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import is_token_blacklisted
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services import user as user_service
from app.models.event import Event  

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_service.get_by_id(db, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

# def get_event_with_permission(permission_type: str = "view"):
    """
    Dependency factory for checking event permissions.
    """
    def get_event(
        event_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Event:
        # First check the user is authenticated
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        
        # Get the event
        from app.services import event as event_service
        event = event_service.get_by_id(db, event_id)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        
        # Check if user is the owner
        if str(event.owner_id) == str(current_user.id):
            return event  # Owner has all permissions
        
        # Check if user has the required permission
        from app.services import permission as permission_service
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        
        # Check specific permission
        has_permission = False
        if permission_type == "view" and permission.can_view:
            has_permission = True
        elif permission_type == "edit" and permission.can_edit:
            has_permission = True
        elif permission_type == "delete" and permission.can_delete:
            has_permission = True
        elif permission_type == "share" and permission.can_share:
            has_permission = True
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to {permission_type} this event",
            )
        
        return event
    
    return get_event