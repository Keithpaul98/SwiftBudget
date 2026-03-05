"""
Audit logging utility functions.

Provides convenient methods for logging financial operations
from route handlers.
"""

from flask import request
from flask_login import current_user
from app.models.audit_log import AuditLog


def audit_log(action, entity_type, entity_id=None, old_value=None, new_value=None):
    """
    Log an audit event with current request context.
    
    Args:
        action: Action type (CREATE, UPDATE, DELETE, LOGIN, etc.)
        entity_type: Type of entity affected
        entity_id: ID of entity affected
        old_value: Dict or string of old values
        new_value: Dict or string of new values
    
    Returns:
        AuditLog entry
    """
    user_id = current_user.id if current_user and hasattr(current_user, 'id') and current_user.is_authenticated else None
    ip_address = request.remote_addr if request else None
    user_agent = str(request.user_agent)[:255] if request and request.user_agent else None
    
    return AuditLog.log(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent
    )
