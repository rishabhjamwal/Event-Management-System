# app/api/v1/permissions.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
import uuid

from ems.dependencies import deps
from ems.models.user_model import User
from ems.schemas.permission_schema import Permission, PermissionCreate, PermissionUpdate, ShareEventRequest
from ems.services import  event_service, permission_service, user_service
from ems.utils.helper import permission_to_dict
from ems.db import session


router = APIRouter()

@router.post("/{event_id}/share", response_model=List[Permission])
def share_event(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    share_data: ShareEventRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Share an event with other users.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if the current user is the owner or has share permission
    if event.owner_id != current_user.id:
        permission = permission_service.get_permission(db, event_id, current_user.id)
        if not permission or not permission.can_share:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    results = []
    for user_role in share_data.users:
        permission_in = PermissionCreate(user_id=user_role.user_id, role=user_role.role)
        # Check if the user exists
        user = user_service.get_by_id(db, permission_in.user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {permission_in.user_id} not found")
        
        # Check if permission already exists
        existing_permission = permission_service.get_permission(db, event_id, permission_in.user_id)
        if existing_permission:
            # Update existing permission
            permission = permission_service.update_permission(db, existing_permission, permission_in)
        else:
            # Create new permission
            permission = permission_service.create_permission(
                db, permission_in, event_id, current_user.id
            )
        
        # Add username to the result
        permission_dict = permission_to_dict(permission, user.username)
        results.append(Permission.model_validate(permission_dict))
    
    return results

@router.get("/{event_id}/permissions", response_model=List[Permission])
def get_event_permissions(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get all permissions for an event.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if the current user has access to the event
    if event.owner_id != current_user.id:
        permission = permission_service.get_permission(db, event_id, current_user.id)
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    permissions = permission_service.get_permissions_by_event(db, event_id)
    
    # Add username to each permission
    result = []
    for permission in permissions:
        user = user_service.get_by_id(db, permission.user_id)
        username = user.username if user else "Unknown"
        permission_dict = permission_to_dict(permission, username)
        result.append(Permission.model_validate(permission_dict))
    
    return result

@router.put("/{event_id}/permissions/{user_id}", response_model=Permission)
def update_user_permission(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    user_id: str = Path(...),
    permission_in: PermissionUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Update permissions for a user.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if the current user is the owner or has share permission
    if event.owner_id != current_user.id:
        permission = permission_service.get_permission(db, event_id, current_user.id)
        if not permission or not permission.can_edit:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if the user exists
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if permission exists
    permission = permission_service.get_permission(db, event_id, user_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Don't allow changing the owner's permissions
    if event.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change owner's permissions")
    
    # Update permission
    updated_permission = permission_service.update_permission(db, permission, permission_in)
    
    # Add username to the result
    permission_dict = permission_to_dict(updated_permission, user.username)
    result = Permission.model_validate(permission_dict)
    
    return result

@router.delete("/{event_id}/permissions/{user_id}", status_code=204)
def remove_user_access(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    user_id: str = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> None:
    """
    Remove access for a user.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if the current user is the owner or has share permission
    if event.owner_id != current_user.id:
        permission = permission_service.get_permission(db, event_id, current_user.id)
        if not permission or not permission.can_delete:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Don't allow removing the owner's access
    if event.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove owner's access")
    
    # Check if permission exists
    permission = permission_service.get_permission(db, event_id, user_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Delete permission
    permission_service.delete_permission(db, permission)