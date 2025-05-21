# app/services/event.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid

from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate

def get_by_id(db: Session, event_id: uuid.UUID) -> Optional[Event]:
    return db.query(Event).filter(Event.id == event_id).first()

def get_by_owner(db: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Event]:
    return db.query(Event).filter(Event.owner_id == owner_id).offset(skip).limit(limit).all()

def get_events_in_range(db: Session, start_date: datetime, end_date: datetime, owner_id: Optional[int] = None) -> List[Event]:
    query = db.query(Event).filter(
        and_(
            Event.start_time >= start_date,
            Event.end_time <= end_date
        )
    )
    
    if owner_id:
        query = query.filter(Event.owner_id == owner_id)
    
    return query.all()

def create(db: Session, *, obj_in: EventCreate, owner_id: str) -> Event:
    # Double-check for conflicts before creating
    conflicts = check_for_conflicts(db, obj_in.start_time, obj_in.end_time, owner_id)
    if conflicts:
        # Log a warning if we somehow got here with conflicts
        print(f"WARNING: Creating event despite conflicts: {[str(c.id) for c in conflicts]}")
    
    db_obj = Event(
        title=obj_in.title,
        description=obj_in.description,
        start_time=obj_in.start_time,
        end_time=obj_in.end_time,
        location=obj_in.location,
        is_recurring=obj_in.is_recurring,
        recurrence_pattern=obj_in.recurrence_pattern,
        owner_id=owner_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    # Create initial version and changelog
    from app.services import version as version_service
    version = version_service.create_version(db, db_obj, owner_id, "Initial version")
    version_service.create_changelog(
        db, 
        str(db_obj.id), 
        owner_id, 
        'create', 
        None, 
        version.version_number, 
        None
    )
    return db_obj

def update(db: Session, *, db_obj: Event, obj_in: EventUpdate) -> Event:
    # Store the original data for diff
    from app.services import version as version_service
    latest_version = version_service.get_latest_version(db, str(db_obj.id))
    old_data = latest_version.data if latest_version else None

    # Event Update
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # Increment version on update
    db_obj.current_version += 1
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    new_version = version_service.create_version(
        db, 
        db_obj, 
        db_obj.owner_id, 
        "Update event"
    )
    
    # Generate diff and create changelog
    if old_data:
        # Create event data for diff
        event_data = {
            "id": str(db_obj.id),
            "title": db_obj.title,
            "description": db_obj.description,
            "start_time": db_obj.start_time.isoformat() if db_obj.start_time else None,
            "end_time": db_obj.end_time.isoformat() if db_obj.end_time else None,
            "location": db_obj.location,
            "is_recurring": db_obj.is_recurring,
            "recurrence_pattern": db_obj.recurrence_pattern,
            "owner_id": str(db_obj.owner_id),
            "created_at": db_obj.created_at.isoformat() if db_obj.created_at else None,
            "updated_at": db_obj.updated_at.isoformat() if db_obj.updated_at else None,
            "current_version": db_obj.current_version
        }
        
        changes = version_service.generate_diff(old_data, event_data)
        version_service.create_changelog(
            db,
            str(db_obj.id),
            str(db_obj.owner_id),
            'update',
            latest_version.version_number,
            new_version.version_number,
            changes
        )
    return db_obj

def delete(db: Session, *, db_obj: Event) -> None:
    db.delete(db_obj)
    db.commit()

def create_batch(db: Session, *, obj_in_list: List[EventCreate], owner_id: int) -> List[Event]:
    db_objs = []
    for obj_in in obj_in_list:
        db_obj = Event(
            title=obj_in.title,
            description=obj_in.description,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time,
            location=obj_in.location,
            is_recurring=obj_in.is_recurring,
            recurrence_pattern=obj_in.recurrence_pattern,
            owner_id=owner_id,
        )
        db.add(db_obj)
        db_objs.append(db_obj)
    
    db.commit()
    for obj in db_objs:
        db.refresh(obj)
    
    return db_objs

def check_for_conflicts(db: Session, start_time: datetime, end_time: datetime, owner_id: str, event_id: Optional[str] = None) -> List[Event]:
    
    from datetime import timezone
    print(f"Checking conflicts for: {start_time} to {end_time}")
    
    # Convert start_time and end_time to UTC if they have timezone info
    if start_time.tzinfo:
        start_time = start_time.astimezone(timezone.utc)
    if end_time.tzinfo:
        end_time = end_time.astimezone(timezone.utc)
    
    # Get all events for the owner
    all_events = db.query(Event).filter(Event.owner_id == owner_id)
    if event_id:
        all_events = all_events.filter(Event.id != event_id)
    
    all_events = all_events.all()
    print(f"Found {len(all_events)} existing events for owner")
    
    # Check each event for conflicts
    conflicts = []
    for event in all_events:
        event_start = event.start_time
        event_end = event.end_time
        
        # Convert to UTC if they have timezone info
        if event_start.tzinfo:
            event_start = event_start.astimezone(timezone.utc)
        if event_end.tzinfo:
            event_end = event_end.astimezone(timezone.utc)
            
        print(f"Comparing with event {event.id}: {event_start} to {event_end}")
        
        # Case 1: New event starts during an existing event
        if event_start <= start_time < event_end:
            print(f"Conflict: New event starts during existing event {event.id}")
            conflicts.append(event)
            continue
            
        # Case 2: New event ends during an existing event
        if event_start < end_time <= event_end:
            print(f"Conflict: New event ends during existing event {event.id}")
            conflicts.append(event)
            continue
            
        # Case 3: New event completely contains an existing event
        if start_time <= event_start and end_time >= event_end:
            print(f"Conflict: New event contains existing event {event.id}")
            conflicts.append(event)
            continue
            
        # Case 4: New event is completely contained within an existing event
        if event_start <= start_time and event_end >= end_time:
            print(f"Conflict: New event is contained within existing event {event.id}")
            conflicts.append(event)
            continue
    
    print(f"Found {len(conflicts)} conflicts")
    return conflicts

def check_user_access(db: Session, event_id: str, user_id: str, permission_type: str = 'view') -> bool:
    """
    Check if a user has access to an event.
    Returns True if the user is the owner or has the specified permission.
    """
    event = get_by_id(db, event_id)
    if not event:
        return False
    
    # Owner has all permissions
    if event.owner_id == user_id:
        return True
    
    # Check specific permission for non-owners
    from app.services import permission as permission_service
    return permission_service.check_permission(db, event_id, user_id, permission_type)
    
    # Exclude the current event if updating
    if event_id:
        query = query.filter(Event.id != event_id)
    
    return query.all()