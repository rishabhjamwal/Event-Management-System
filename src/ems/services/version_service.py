# app/services/version.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import uuid
from datetime import datetime

from ems.models.event_model import Event
from ems.models.version_model import EventVersion, EventChangelog
from ems.schemas.version_schema import EventVersionCreate, ChangelogCreate
from ems.services import event_service
from ems.services import user_service

def get_version_by_number(db: Session, event_id: str, version_number: int) -> Optional[EventVersion]:
    return db.query(EventVersion).filter(
        and_(
            EventVersion.event_id == event_id,
            EventVersion.version_number == version_number
        )
    ).first()

def get_latest_version(db: Session, event_id: str) -> Optional[EventVersion]:
    return db.query(EventVersion).filter(
        EventVersion.event_id == event_id
    ).order_by(desc(EventVersion.version_number)).first()

def get_all_versions(db: Session, event_id: str) -> List[EventVersion]:
    return db.query(EventVersion).filter(
        EventVersion.event_id == event_id
    ).order_by(desc(EventVersion.version_number)).all()

def create_version(db: Session, event: Event, user_id: str, description: Optional[str] = None) -> EventVersion:
    # Get the latest version number and increment
    latest_version = get_latest_version(db, str(event.id))
    version_number = 1 if not latest_version else latest_version.version_number + 1
    
    # Create the event data to store
    event_data = {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "location": event.location,
        "is_recurring": event.is_recurring,
        "recurrence_pattern": event.recurrence_pattern,
        "owner_id": str(event.owner_id),
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
        "current_version": event.current_version
    }
    
    # Create the version
    db_obj = EventVersion(
        event_id=event.id,
        version_number=version_number,
        data=event_data,
        created_by_id=user_id,
        change_description=description
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Update the event's current_version
    event.current_version = version_number
    db.add(event)
    db.commit()
    
    return db_obj

def create_changelog(db: Session, event_id: str, user_id: str, action: str, 
                    version_from: Optional[int] = None, version_to: Optional[int] = None, 
                    changes: Optional[Dict[str, Any]] = None) -> EventChangelog:
    db_obj = EventChangelog(
        event_id=event_id,
        user_id=user_id,
        action=action,
        version_from=version_from,
        version_to=version_to,
        changes=changes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_changelogs(db: Session, event_id: str) -> List[EventChangelog]:
    return db.query(EventChangelog).filter(
        EventChangelog.event_id == event_id
    ).order_by(desc(EventChangelog.timestamp)).all()

def generate_diff(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a diff between two event data dictionaries.
    Returns a dictionary of field names and their old/new values.
    """
    diff = {}
    
    # Compare each field
    for key in set(old_data.keys()) | set(new_data.keys()):
        # Skip id and timestamps
        if key in ['id', 'created_at']:
            continue
            
        # Get values, defaulting to None if not present
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        # Add to diff if values are different
        if old_value != new_value:
            diff[key] = {
                'old': old_value,
                'new': new_value
            }
    
    return diff

def rollback_event(db: Session, event_id: str, version_number: int, user_id: str) -> Event:
    # Get the specified version
    version = get_version_by_number(db, event_id, version_number)
    if not version:
        return None
    
    # Get the event
    event = event_service.get_by_id(db, event_id)
    if not event:
        return None
    
    # Get the current version data for changelog
    current_version = get_latest_version(db, event_id)
    
    # Apply the version data to the event
    version_data = version.data
    event.title = version_data.get('title', event.title)
    event.description = version_data.get('description', event.description)
    
    # Handle datetime fields specially
    if 'start_time' in version_data and version_data['start_time']:
        event.start_time = datetime.fromisoformat(version_data['start_time'])
    if 'end_time' in version_data and version_data['end_time']:
        event.end_time = datetime.fromisoformat(version_data['end_time'])
    
    event.location = version_data.get('location', event.location)
    event.is_recurring = version_data.get('is_recurring', event.is_recurring)
    event.recurrence_pattern = version_data.get('recurrence_pattern', event.recurrence_pattern)
    
    # Update the event with the rolled back data
    event.updated_at = datetime.now()
    db.add(event)
    
    # Create a new version with the rolled back data
    new_version = create_version(
        db, 
        event, 
        user_id, 
        f"Rollback to version {version_number}"
    )
    
    # Create a changelog entry
    changes = generate_diff(current_version.data, version.data)
    create_changelog(
        db,
        event_id,
        user_id,
        'rollback',
        current_version.version_number,
        new_version.version_number,
        changes
    )
    
    db.commit()
    db.refresh(event)
    
    return event