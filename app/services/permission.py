# app/services/permission.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.permission import EventPermission
from app.models.user import User
from app.schemas.permission import PermissionCreate, PermissionUpdate

def get_permission(db: Session, event_id: str, user_id: str) -> Optional[EventPermission]:
    return db.query(EventPermission).filter(
        and_(
            EventPermission.event_id == event_id,
            EventPermission.user_id == user_id
        )
    ).first()

def get_permissions_by_event(db: Session, event_id: str) -> List[EventPermission]:
    return db.query(EventPermission).filter(EventPermission.event_id == event_id).all()

def create_permission(db: Session, permission_in: PermissionCreate, event_id: str, granted_by_id: str) -> EventPermission:
    db_obj = EventPermission(
        event_id=event_id,
        user_id=permission_in.user_id,
        role=permission_in.role,
        granted_by_id=granted_by_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_permission(db: Session, db_obj: EventPermission, permission_in: PermissionUpdate) -> EventPermission:
    db_obj.role = permission_in.role
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
def delete_permission(db: Session, db_obj: EventPermission) -> None:
    db.delete(db_obj)
    db.commit()

def check_permission(db: Session, event_id: str, user_id: str, permission_type: str) -> bool:
    """
    Check if a user has a specific permission for an event.
    permission_type can be 'view', 'edit', 'delete', or 'share'.
    """
    permission = get_permission(db, event_id, user_id)
    
    if not permission:
        return False
    
    if permission_type == 'view':
        return permission.can_view
    elif permission_type == 'edit':
        return permission.can_edit
    elif permission_type == 'delete':
        return permission.can_delete
    elif permission_type == 'share':
        return permission.can_share
    
    return False