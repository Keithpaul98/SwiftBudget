"""
AuditLog Model - Tracks all financial operations for compliance.

Why audit logging?
- Track who changed what and when
- Financial compliance requirements
- Fraud detection capability
- Data recovery and debugging
"""

from datetime import datetime
from app import db


class AuditLog(db.Model):
    """
    Audit log for tracking all financial operations.
    
    Records:
    - User who performed the action
    - Type of action (CREATE, UPDATE, DELETE)
    - Entity affected (Transaction, Budget, Category, Project)
    - Old and new values (for updates)
    - IP address of the request
    - Timestamp
    """
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who performed the action
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # What action was performed
    action = db.Column(
        db.String(20),
        nullable=False
    )  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, LOCKOUT
    
    # What entity was affected
    entity_type = db.Column(
        db.String(50),
        nullable=False
    )  # Transaction, BudgetGoal, Category, Project, User
    
    entity_id = db.Column(
        db.Integer,
        nullable=True
    )
    
    # What changed
    old_value = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_value = db.Column(db.Text, nullable=True)  # JSON string of new values
    
    # Request context
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    
    # When
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Relationship
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id} by user:{self.user_id}>'
    
    @staticmethod
    def log(user_id, action, entity_type, entity_id=None, old_value=None, new_value=None, ip_address=None, user_agent=None):
        """
        Create an audit log entry.
        
        Args:
            user_id: ID of user performing action
            action: Action type (CREATE, UPDATE, DELETE, LOGIN, etc.)
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            old_value: JSON string of old values (for updates)
            new_value: JSON string of new values (for creates/updates)
            ip_address: IP address of the request
            user_agent: User agent string
        """
        import json
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=json.dumps(old_value) if isinstance(old_value, dict) else old_value,
            new_value=json.dumps(new_value) if isinstance(new_value, dict) else new_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(log_entry)
        # Don't commit here - let the caller manage the transaction
        return log_entry
