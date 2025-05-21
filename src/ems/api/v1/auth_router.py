# app/api/v1/auth.py
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ems.dependencies import deps
from ems.schemas.user_schema import User, UserCreate
from ems.schemas.token_schema import Token
from ems.services import user_service , auth_service
from ems.db import session

router = APIRouter()

@router.post("/register", response_model=User)
def register(
    *,
    db: Session = Depends(session.get_db),
    user_in: UserCreate
) -> Any:
    """
    Register a new user.
    """
    # Check if username already exists
    user = user_service.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists   
    if user_service.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    return user_service.create(db, obj_in=user_in)

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(session.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Get access token for user.
    """
   
    if not auth_service.login(db, form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.login(db, form_data.username, form_data.password)

@router.post("/refresh", response_model=Token)
def refresh_token(
    db: Session = Depends(session.get_db),
    refresh_token: str = Body(..., embed=True)
) -> Any:
    """
    Refresh access token.
    """
    if not auth_service.refresh_token(db, refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.refresh_token(db, refresh_token)

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    db: Session = Depends(session.get_db),
    token: str = Depends(deps.oauth2_scheme),
) -> Any:
    """
    Logout current user.
    """
    success = auth_service.logout(db, token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed",
        )
    return {"detail": "Successfully logged out"}

#endpoint for testing purposes
@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Get current user.
    """
    return current_user