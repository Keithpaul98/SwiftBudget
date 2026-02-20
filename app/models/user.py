"""
User Model - Represents application users.

Why this design?
- Password stored as hash (bcrypt) - never store plain text passwords
- Email unique constraint - prevents duplicate accounts
- Timestamps track account creation - useful for analytics/auditing
- Relationships defined here - SQLAlchemy handles foreign keys automatically
"""

from datetime import datetime
from app import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """
    User model for authentication and user data.
    
    Inherits from:
    - db.Model: SQLAlchemy base class for database models
    - UserMixin: Flask-Login mixin providing default implementations for:
        - is_authenticated, is_active, is_anonymous, get_id()
    
    Why UserMixin?
    - Provides required methods for Flask-Login
    - Saves us from writing boilerplate code
    - Standard pattern for Flask authentication
    """
    
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # User Credentials
    username = db.Column(
        db.String(80), 
        unique=True, 
        nullable=False,
        index=True  # Index for fast username lookups during login
    )
    
    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False,
        index=True  # Index for fast email lookups
    )
    
    password_hash = db.Column(
        db.String(255), 
        nullable=False
    )
    # Why String(255)? Bcrypt hashes are 60 chars, but we use 255 for future flexibility
    
    # Timestamps
    created_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow
    )
    # Why utcnow? Always store times in UTC, convert to local timezone in UI
    
    # Relationships (defined as strings - SQLAlchemy resolves them later)
    # Why strings? Models may not be defined yet, SQLAlchemy resolves at runtime
    
    # One user has many categories
    categories = db.relationship(
        'Category',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # One user has many transactions
    transactions = db.relationship(
        'Transaction',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # One user has many budget goals
    budget_goals = db.relationship(
        'BudgetGoal',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # One user has many projects
    projects = db.relationship(
        'Project',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    # Why projects relationship?
    # - User can have multiple projects
    # - Projects help organize transactions
    # - cascade='all, delete-orphan': delete projects when user deleted
    
    def __repr__(self):
        """
        String representation for debugging.
        
        Why __repr__?
        - Helpful when debugging (print statements, error messages)
        - Shows in Python shell when inspecting objects
        - Never include sensitive data (password_hash) in repr
        """
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Hash and set user password.
        
        Why separate method?
        - Never store plain text passwords
        - Encapsulates bcrypt logic
        - Easy to change hashing algorithm later
        
        Args:
            password (str): Plain text password
        """
        from app import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        # Why decode('utf-8')? Bcrypt returns bytes, we need string for database
    
    def check_password(self, password):
        """
        Verify password against stored hash.
        
        Args:
            password (str): Plain text password to check
        
        Returns:
            bool: True if password matches, False otherwise
        
        Why separate method?
        - Encapsulates bcrypt verification logic
        - Constant-time comparison (security - prevents timing attacks)
        """
        from app import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Convert user to dictionary (for JSON responses in future API).
        
        Why to_dict?
        - Easy serialization for API responses
        - Control what data is exposed (exclude password_hash)
        - Consistent format across application
        
        Returns:
            dict: User data (safe for external exposure)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
            # Why isoformat()? Standard ISO 8601 format for dates in JSON
            # Note: password_hash is NOT included (security)
        }
