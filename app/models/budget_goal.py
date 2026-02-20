"""
BudgetGoal Model - Represents budget limits for categories.

Why this design?
- Set spending limits per category (e.g., $500/month for Food)
- Alert users when approaching budget limit (80% threshold)
- Support different periods (monthly, weekly, yearly)
- Track budget vs actual spending
"""

from datetime import datetime
from decimal import Decimal
from app import db


class BudgetGoal(db.Model):
    """
    BudgetGoal model for setting spending limits.
    
    Users can set budget goals like:
    - "Spend no more than $500/month on Food"
    - "Limit Utilities to $200/month"
    - "Keep Entertainment under $100/week"
    
    Why budget goals?
    - Helps users control spending
    - Provides alerts when approaching limit
    - Enables financial planning
    """
    
    __tablename__ = 'budget_goals'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Budget Details
    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )
    # Why Numeric(10,2)?
    # - Same as Transaction model for consistency
    # - Exact decimal arithmetic
    
    period = db.Column(
        db.String(20),
        nullable=False
    )
    # Period types: 'monthly', 'weekly', 'yearly'
    # Why String not Enum?
    # - Simpler for SQLite compatibility
    # - Can add CHECK constraint for validation
    
    alert_threshold = db.Column(
        db.Integer,
        nullable=False,
        default=80
    )
    # Alert when spending reaches X% of budget
    # Default: 80% (alert when user spends 80% of budget)
    # Why Integer?
    # - Percentage value (0-100)
    # - Example: 80 means "alert at 80%"
    
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    # Why is_active?
    # - Users can temporarily disable budget goals
    # - Don't delete (preserve history)
    # - Can reactivate later
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    # Why CASCADE?
    # - If category deleted, budget goal should be deleted too
    # - Budget goal is meaningless without category
    
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
    
    # Constraints
    __table_args__ = (
        # Ensure amount is positive
        db.CheckConstraint('amount > 0', name='check_positive_budget_amount'),
        # Ensure period is valid
        db.CheckConstraint(
            "period IN ('monthly', 'weekly', 'yearly')",
            name='check_budget_period'
        ),
        # Ensure alert_threshold is between 0 and 100
        db.CheckConstraint(
            'alert_threshold >= 0 AND alert_threshold <= 100',
            name='check_alert_threshold_range'
        ),
        # One budget goal per category per user
        db.UniqueConstraint('user_id', 'category_id', name='uq_user_category_budget'),
    )
    
    def __repr__(self):
        """
        String representation for debugging.
        
        Returns:
            str: Budget amount, period, and category
        """
        return f'<BudgetGoal ${self.amount}/{self.period} for category_id={self.category_id}>'
    
    def to_dict(self):
        """
        Convert budget goal to dictionary (for JSON responses).
        
        Returns:
            dict: Budget goal data
        """
        return {
            'id': self.id,
            'amount': float(self.amount),
            'period': self.period,
            'alert_threshold': self.alert_threshold,
            'is_active': self.is_active,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_spending(self, start_date, end_date):
        """
        Get total spending for this category in date range.
        
        Args:
            start_date (date): Start of period
            end_date (date): End of period
        
        Returns:
            Decimal: Total spending in period
        """
        from app.models.transaction import Transaction
        
        transactions = Transaction.query.filter(
            Transaction.user_id == self.user_id,
            Transaction.category_id == self.category_id,
            Transaction.transaction_type == 'expense',
            Transaction.is_deleted == False,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).all()
        
        total = Decimal('0.00')
        for transaction in transactions:
            total += transaction.amount
        
        return total
    
    def get_current_period_spending(self):
        """
        Get spending for current budget period.
        
        Returns:
            Decimal: Total spending in current period
        """
        from datetime import date, timedelta
        
        today = date.today()
        
        if self.period == 'weekly':
            # Current week (Monday to Sunday)
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        
        elif self.period == 'monthly':
            # Current month
            start_date = today.replace(day=1)
            # Last day of month
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        elif self.period == 'yearly':
            # Current year
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        
        else:
            # Default to monthly
            start_date = today.replace(day=1)
            end_date = today
        
        return self.get_spending(start_date, end_date)
    
    def get_remaining_budget(self):
        """
        Get remaining budget for current period.
        
        Returns:
            Decimal: Remaining budget (can be negative if over budget)
        """
        spending = self.get_current_period_spending()
        return self.amount - spending
    
    def get_percentage_used(self):
        """
        Get percentage of budget used in current period.
        
        Returns:
            float: Percentage used (0-100+, can exceed 100 if over budget)
        """
        spending = self.get_current_period_spending()
        
        if self.amount == 0:
            return 0.0
        
        percentage = (float(spending) / float(self.amount)) * 100
        return round(percentage, 2)
    
    def is_over_budget(self):
        """
        Check if spending exceeds budget.
        
        Returns:
            bool: True if over budget, False otherwise
        """
        return self.get_current_period_spending() > self.amount
    
    def should_alert(self):
        """
        Check if alert should be triggered.
        
        Alert triggers when spending reaches alert_threshold percentage.
        
        Returns:
            bool: True if should alert, False otherwise
        """
        if not self.is_active:
            return False
        
        percentage_used = self.get_percentage_used()
        return percentage_used >= self.alert_threshold
    
    def get_alert_message(self):
        """
        Get alert message for user.
        
        Returns:
            str: Alert message or None if no alert needed
        """
        if not self.should_alert():
            return None
        
        percentage = self.get_percentage_used()
        spending = self.get_current_period_spending()
        
        if self.is_over_budget():
            over_amount = spending - self.amount
            return (
                f"⚠️ Budget Alert: You've exceeded your {self.period} "
                f"budget for {self.category.name} by ${over_amount:.2f}! "
                f"(${spending:.2f} / ${self.amount:.2f})"
            )
        else:
            return (
                f"⚠️ Budget Alert: You've used {percentage:.0f}% of your "
                f"{self.period} budget for {self.category.name}. "
                f"(${spending:.2f} / ${self.amount:.2f})"
            )
