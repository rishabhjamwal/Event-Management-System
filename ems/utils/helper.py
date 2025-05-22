def permission_to_dict(permission, username=None):
    """Convert an EventPermission object to a dictionary with string UUIDs"""
    return {
        "id": str(permission.id),
        "event_id": str(permission.event_id),
        "user_id": str(permission.user_id),
        "granted_by_id": str(permission.granted_by_id) if permission.granted_by_id else None,
        "role": permission.role,
        "can_view": permission.can_view,
        "can_edit": permission.can_edit,
        "can_delete": permission.can_delete,
        "can_share": permission.can_share,
        "granted_at": permission.granted_at,
        "username": username or "Unknown"
    }