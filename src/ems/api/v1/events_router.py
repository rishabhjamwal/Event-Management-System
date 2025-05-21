# app/api/v1/events.py
import uuid
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from ems.dependencies import deps
from ems.models.user_model import User
from ems.schemas.event_schema import Event, EventCreate, EventUpdate
from ems.services import event_service 

router = APIRouter()

# Create a schema for conflict response
from pydantic import BaseModel

class ConflictResponse(BaseModel):
    detail: str
    conflicts: List[uuid.UUID]  # Just store the IDs of conflicting events

@router.post("/", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(
    *,
    db: Session = Depends(deps.get_db),
    event_in: EventCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create a new event.
    """
    
    # Check for conflicting events
    conflicts = event_service.check_for_conflicts(
        db, 
        event_in.start_time, 
        event_in.end_time, 
        str(current_user.id)
    )
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Event conflicts with existing events",
                "conflict_ids": [str(conflict.id) for conflict in conflicts]
            }
        )
    # Create the event
    return event_service.create(db, obj_in=event_in, owner_id=current_user.id)
 

@router.get("/", response_model=List[Event])
def read_events(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Retrieve events.
    """
    if start_date and end_date:
        events = event_service.get_events_in_range(db, start_date, end_date, current_user.id)
    else:
        events = event_service.get_by_owner(db, current_user.id, skip=skip, limit=limit)
    return events

@router.get("/{event_id}", response_model=Event)
def read_event(
    *,
    db: Session = Depends(deps.get_db),
    event_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get event by ID.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        from ems.services import permission_service
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_view:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    return event

@router.put("/{event_id}", response_model=Event)
def update_event(
    *,
    db: Session = Depends(deps.get_db),
    event_id: uuid.UUID,
    event_in: EventUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Update an event.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        from ems.services import permission_service
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_edit:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check for conflicts if date/time is being updated
    if event_in.start_time or event_in.end_time:
        start_time = event_in.start_time or event.start_time
        end_time = event_in.end_time or event.end_time
        
        conflicts = event_service.check_for_conflicts(
            db, 
            start_time, 
            end_time, 
            current_user.id,
            event_id
        )
        if conflicts:
            # Return HTTPException with conflict details
            raise HTTPException(
                status_code=409,  # Conflict status code
                detail={
                    "message": "Event update conflicts with existing events",
                    "conflict_ids": [str(conflict.id) for conflict in conflicts]
                }
            )
    
    event = event_service.update(db, db_obj=event, obj_in=event_in)
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    *,
    db: Session = Depends(deps.get_db),
    event_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user)
) -> None:
    """
    Delete an event.
    """
    event = event_service.get_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        from ems.services import permission_service
        permission = permission_service.get_permission(db, str(event_id), str(current_user.id))
        if not permission or not permission.can_delete:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    event_service.delete(db, db_obj=event)
    return 

@router.post("/batch", response_model=List[Event])
def create_batch_events(
    *,
    db: Session = Depends(deps.get_db),
    events_in: List[EventCreate],
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Create multiple events in a single request.
    """
    # Check for conflicts for all events
    all_conflicts = []
    for event_in in events_in:
        conflicts = event_service.check_for_conflicts(
            db, 
            event_in.start_time, 
            event_in.end_time, 
            current_user.id
        )
        if conflicts:
            all_conflicts.extend(conflicts)
    
    if all_conflicts:
        # Return HTTPException with conflict details
        raise HTTPException(
            status_code=409,  # Conflict status code
            detail={
                "message": "Some events conflict with existing events",
                "conflict_ids": [str(conflict.id) for conflict in all_conflicts]
            }
        )
    
    events = event_service.create_batch(db, obj_in_list=events_in, owner_id=current_user.id)
    return events