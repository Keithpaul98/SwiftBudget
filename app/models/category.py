"""
Category Model - Represents expense/income categories.

Why this design?
- Default categories (Food, Rent, etc.) provided for all users
- Users can create custom categories
- is_default flag prevents users from deleting default categories
- Relationship to User ensures data isolation
"""

from datetime import datetime
from app import db


class Category(db.Model):
    """
    Category model for organizing transactions.
    
    Categories can be:
    1. Default (system-provided, shared by all users)
    2. Custom (user-created, specific to one user)
    
    Why both types?
    - Default categories provide immediate usability (new users don't start from scratch)
    - Custom categories allow personalization (user-specific needs)
    """
    
    __tablename__ = 'categories'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Category Details
    name = db.Column(
        db.String(50), 
        nullable=False
    )
    # Why String(50)? Category names should be short and descriptive
    
    is_default = db.Column(
        db.Boolean, 
        nullable=False, 
        default=False
    )
    # Why is_default?
    # - Default categories (Food, Rent) can't be deleted by users
    # - Ensures consistency across the application
    # - Users can still create custom categories
    
    # Foreign Key
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True  # Index for fast user-specific queries
    )
    # Why CASCADE?
    # - When user is deleted, their custom categories are deleted
    # - Default categories belong to a "system" user (user_id=0 or special user)
    
    # Timestamps
    created_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow
    )
    
    # Relationships
    # One category has many transactions
    transactions = db.relationship(
        'Transaction',
        backref='category',
        lazy='dynamic'
        # Note: No cascade delete - RESTRICT in foreign key prevents category deletion
        # if it has transactions (prevents accidental data loss)
    )
    
    # Constraints
    __table_args__ = (
        # Ensure category name is unique per user
        db.UniqueConstraint('user_id', 'name', name='uq_user_category_name'),
        # Why unique constraint?
        # - User can't have two categories with same name (confusing)
        # - But different users CAN have categories with same name
        # - Example: User A has "Food", User B can also have "Food"
    )
    
    def __repr__(self):
        """
        String representation for debugging.
        
        Returns:
            str: Category name and type (default/custom)
        """
        category_type = "default" if self.is_default else "custom"
        return f'<Category {self.name} ({category_type})>'
    
    def to_dict(self):
        """
        Convert category to dictionary (for JSON responses).
        
        Returns:
            dict: Category data
        """
        return {
            'id': self.id,
            'name': self.name,
            'is_default': self.is_default,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_default_categories():
        """
        Get list of default category names.
        
        Why static method?
        - Doesn't need instance (self)
        - Can be called without creating Category object
        - Useful for seeding database with default categories
        
        Returns:
            list: Default category names
        """
        return [
            'Food & Dining',
            'Groceries',
            'Rent/Mortgage',
            'Utilities',
            'Transportation',
            'Healthcare',
            'Entertainment',
            'Shopping',
            'Income',
            'Other'
        ]
        # Why these categories?
        # - Cover most common expense types
        # - "Income" for salary, bonuses, etc.
        # - "Other" as catch-all for miscellaneous
    
    @classmethod
    def create_default_categories_for_user(cls, user_id):
        """
        Create default categories for a new user.
        
        Why class method?
        - Operates on the class (Category), not instance
        - Can create multiple Category objects
        - Called when new user signs up
        
        Args:
            user_id (int): User ID to create categories for
        
        Returns:
            list: Created Category objects
        """
        categories = []
        
        for category_name in cls.get_default_categories():
            category = cls(
                name=category_name,
                user_id=user_id,
                is_default=True
            )
            categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        return categories
