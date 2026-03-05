"""
Recurring Transaction Model - Automates repeated transactions.

Supports daily, weekly, monthly, and yearly recurrence patterns.
Tracks last execution and next due date for processing.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from app import db


class RecurringTransaction(db.Model):
    """Model for recurring/scheduled transactions."""
    
    __tablename__ = 'recurring_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='RESTRICT'),
        nullable=False
    )
    
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Recurrence settings
    frequency = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # NULL = no end date
    
    # Tracking
    next_due_date = db.Column(db.Date, nullable=False, index=True)
    last_created_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('recurring_transactions', lazy='dynamic'))
    category = db.relationship('Category')
    project = db.relationship('Project')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_recurring_positive_amount'),
        db.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name='check_recurring_transaction_type'
        ),
        db.CheckConstraint(
            "frequency IN ('daily', 'weekly', 'monthly', 'yearly')",
            name='check_recurring_frequency'
        ),
    )
    
    def __repr__(self):
        return f'<RecurringTransaction {self.frequency} {self.transaction_type} {self.amount}>'
    
    def calculate_next_due(self, from_date=None):
        """Calculate the next due date based on frequency."""
        base = from_date or self.next_due_date
        if self.frequency == 'daily':
            return base + timedelta(days=1)
        elif self.frequency == 'weekly':
            return base + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return base + relativedelta(months=1)
        elif self.frequency == 'yearly':
            return base + relativedelta(years=1)
        return base
    
    def is_due(self):
        """Check if this recurring transaction is due for processing."""
        if not self.is_active:
            return False
        if self.end_date and date.today() > self.end_date:
            return False
        return date.today() >= self.next_due_date
