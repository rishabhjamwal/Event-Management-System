# app/api/v1/versions.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ems.dependencies import deps
from ems.models.user_model import User
from ems.schemas.event_schema import Event as EventSchema
from ems.schemas.version_schema import EventVersion as EventVersionSchema, Changelog as ChangelogSchema, DiffResponse
from ems.services import event_service, version_service, permission_service
from ems.db import session



router = APIRouter()

@router.get("/{event_id}/history/{version_id}", response_model=EventVersionSchema)
def get_event_version(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    version_id: int = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a specific version of an event.
    """
    # Check if event exists
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user has access to this event
    if str(event.owner_id) != str(current_user.id):
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the requested version
    version = version_service.get_version_by_number(db, event_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version

@router.post("/{event_id}/rollback/{version_id}", response_model=EventSchema)
def rollback_event(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    version_id: int = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Rollback to a previous version.
    """
    # Check if event exists
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user has edit permission
    if str(event.owner_id) != str(current_user.id):
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_edit:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if version exists
    version = version_service.get_version_by_number(db, event_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Rollback the event
    updated_event = version_service.rollback_event(db, event_id, version_id, str(current_user.id))
    if not updated_event:
        raise HTTPException(status_code=400, detail="Failed to rollback event")
    
    return updated_event

@router.get("/{event_id}/changelog", response_model=List[ChangelogSchema])
def get_event_changelog(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a chronological log of all changes to an event.
    """
    # Check if event exists
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user has access to this event
    if str(event.owner_id) != str(current_user.id):
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the changelog
    changelogs = version_service.get_changelogs(db, event_id)
    
    # Add username to each changelog entry
    result = []
    for log in changelogs:
        log_dict = {
            "id": str(log.id),
            "event_id": str(log.event_id),
            "user_id": str(log.user_id),
            "timestamp": log.timestamp,
            "action": log.action,
            "version_from": log.version_from,
            "version_to": log.version_to,
            "changes": log.changes,
            "username": "Unknown"
        }
        
        # Get username if user exists
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                log_dict["username"] = user.username
        
        result.append(ChangelogSchema.model_validate(log_dict))
    
    return result

@router.get("/{event_id}/diff/{version_id1}/{version_id2}", response_model=DiffResponse)
def get_event_diff(
    *,
    db: Session = Depends(session.get_db),
    event_id: str = Path(...),
    version_id1: int = Path(...),
    version_id2: int = Path(...),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a diff between two versions.
    """
    # Check if event exists
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user has access to this event
    if str(event.owner_id) != str(current_user.id):
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the versions
    version1 = version_service.get_version_by_number(db, event_id, version_id1)
    if not version1:
        raise HTTPException(status_code=404, detail=f"Version {version_id1} not found")
    
    version2 = version_service.get_version_by_number(db, event_id, version_id2)
    if not version2:
        raise HTTPException(status_code=404, detail=f"Version {version_id2} not found")
    
    # Generate diff
    diff = version_service.generate_diff(version1.data, version2.data)
    
    return {
        "event_id": event_id,
        "version1": version_id1,
        "version2": version_id2,
        "diff": diff
    }