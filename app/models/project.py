"""
Project Model - Group related transactions together.

Why Projects?
- Group related expenses (e.g., "Parents Shopping - Feb 2026")
- Track spending for specific purposes (e.g., "Home Renovation", "Vacation")
- Generate project-specific reports
- Better organization and context for transactions

Use Cases:
- Shopping for parents
- Business expenses
- Vacation costs
- Home improvement projects
"""

from datetime import datetime
from app import db


class Project(db.Model):
    """
    Project model for grouping related transactions.
    
    Examples:
    - "Parents Shopping - Feb 2026"
    - "Vacation to Lake Malawi"
    - "Home Office Setup"
    - "Business Trip - March"
    """
    
    __tablename__ = 'projects'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Project Details
    name = db.Column(
        db.String(100),
        nullable=False
    )
    # Why String(100)?
    # - Descriptive project names
    # - Example: "Parents Shopping - February 2026"
    
    description = db.Column(
        db.String(500),
        nullable=True
    )
    # Optional detailed description
    # Example: "Monthly shopping for parents including groceries and household items"
    
    color = db.Column(
        db.String(7),
        nullable=True,
        default='#6c757d'
    )
    # Why color?
    # - Visual distinction in UI
    # - Hex color code (e.g., #FF5733)
    # - Default: Bootstrap secondary gray
    
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    # Why is_active?
    # - Archive completed projects
    # - Don't delete (preserve history)
    # - Can reactivate if needed
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    # Why CASCADE?
    # - If user deleted, projects should be deleted too
    # - Projects belong to specific users
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    transactions = db.relationship(
        'Transaction',
        backref='project',
        lazy='dynamic'
    )
    # Why lazy='dynamic'?
    # - Returns query object, not list
    # - Can filter/paginate transactions
    # - Example: project.transactions.filter_by(transaction_type='expense').all()
    
    # Note: user relationship is defined in User model via backref
    
    # Constraints
    __table_args__ = (
        # Ensure project names are unique per user
        db.UniqueConstraint('user_id', 'name', name='uq_user_project_name'),
    )
    
    def __repr__(self):
        """
        String representation for debugging.
        
        Returns:
            str: Project name and status
        """
        status = 'Active' if self.is_active else 'Archived'
        return f'<Project "{self.name}" ({status})>'
    
    def to_dict(self):
        """
        Convert project to dictionary (for JSON responses).
        
        Returns:
            dict: Project data
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'is_active': self.is_active,
            'user_id': self.user_id,
            'transaction_count': self.transactions.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_total_spending(self):
        """
        Calculate total spending for this project.
        
        Returns:
            Decimal: Total expenses minus income
        """
        from decimal import Decimal
        
        total_income = sum(
            t.amount for t in self.transactions.filter_by(transaction_type='income', is_deleted=False).all()
        ) or Decimal('0')
        
        total_expenses = sum(
            t.amount for t in self.transactions.filter_by(transaction_type='expense', is_deleted=False).all()
        ) or Decimal('0')
        
        return total_expenses - total_income
    
    def get_transaction_summary(self):
        """
        Get summary statistics for project transactions.
        
        Returns:
            dict: Summary with income, expenses, net, and count
        """
        from decimal import Decimal
        
        active_transactions = self.transactions.filter_by(is_deleted=False).all()
        
        total_income = sum(
            t.amount for t in active_transactions if t.transaction_type == 'income'
        ) or Decimal('0')
        
        total_expenses = sum(
            t.amount for t in active_transactions if t.transaction_type == 'expense'
        ) or Decimal('0')
        
        return {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_spending': float(total_expenses - total_income),
            'transaction_count': len(active_transactions)
        }
