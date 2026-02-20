"""
Transaction Model - Represents financial transactions (income/expense).

Why this design?
- NUMERIC(10,2) for exact decimal arithmetic (no floating-point errors)
- Soft delete (is_deleted) for audit trail
- Transaction type (income/expense) for filtering
- Relationships to User and Category for data organization
"""

from datetime import datetime
from decimal import Decimal
from app import db


class Transaction(db.Model):
    """
    Transaction model for tracking income and expenses.
    
    Critical for financial data:
    - Uses NUMERIC(10,2) not FLOAT (prevents rounding errors)
    - Soft delete (is_deleted) preserves audit trail
    - Immutable once created (edit creates new transaction)
    
    Why NUMERIC instead of FLOAT?
    - FLOAT: 0.1 + 0.2 = 0.30000000000000004 (WRONG for money!)
    - NUMERIC: 0.1 + 0.2 = 0.30 (CORRECT)
    - Financial data requires exact decimal arithmetic
    """
    
    __tablename__ = 'transactions'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Transaction details
    amount = db.Column(
        db.Numeric(10, 2),  # 10 digits total, 2 after decimal
        nullable=False
    )
    # Why Numeric(10, 2)?
    # - Precise decimal arithmetic (no floating point errors)
    # - 10 digits total, 2 after decimal point
    # - Max value: 99,999,999.99 (sufficient for personal finance)
    # - Example: 1234.56
    
    quantity = db.Column(
        db.Integer,
        nullable=True,
        default=1
    )
    # Why quantity?
    # - Track number of items purchased
    # - Example: "5 apples" or "3 coffees"
    # - Optional: defaults to 1 if not specified
    # - Nullable: for backward compatibility
    
    unit_price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )
    # Why unit_price?
    # - Track price per item
    # - Example: "$2.00 per apple"
    # - Optional: if specified, amount = quantity * unit_price
    # - Nullable: for backward compatibility
    
    description = db.Column(
        db.String(200),
        nullable=True  # Optional description
    )
    
    transaction_type = db.Column(
        db.String(20),
        nullable=False
    )
    # Why String not Enum?
    # - Simpler for SQLite compatibility
    # - Values: 'income' or 'expense'
    # - Can add CHECK constraint for validation
    
    transaction_date = db.Column(
        db.Date,
        nullable=False,
        index=True  # Index for date-range queries
    )
    # Why Date not DateTime?
    # - Transactions are typically daily (not hourly)
    # - Simpler for filtering by month/year
    # - created_at tracks exact creation time
    
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True  # Index for filtering active transactions
    )
    # Why soft delete?
    # - Audit trail: see what was deleted and when
    # - Undo functionality: restore deleted transactions
    # - Compliance: some regulations require transaction history
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    # Why RESTRICT not CASCADE?
    # - Prevent accidental data loss
    # - If category deleted, transactions should remain (set to "Uncategorized")
    # - Or prevent category deletion if it has transactions
    
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    # Why project_id?
    # - Optional: transactions can exist without projects
    # - Groups related transactions (e.g., "Parents Shopping")
    # - SET NULL: if project deleted, transaction remains but loses project link
    # - Nullable: not all transactions belong to project
    
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
    # Why updated_at?
    # - Track when transaction was last modified
    # - Useful for sync/audit purposes
    
    # Constraints
    __table_args__ = (
        # Ensure amount is positive
        db.CheckConstraint('amount > 0', name='check_positive_amount'),
        # Ensure transaction_type is valid
        db.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name='check_transaction_type'
        ),
    )
    
    def __repr__(self):
        """
        String representation for debugging.
        
        Returns:
            str: Transaction type, amount, and date
        """
        return f'<Transaction {self.transaction_type} ${self.amount} on {self.transaction_date}>'
    
    def to_dict(self):
        """
        Convert transaction to dictionary (for JSON responses).
        
        Why convert Decimal to float for JSON?
        - JSON doesn't support Decimal type
        - float() converts for serialization
        - Frontend displays as currency
        
        Returns:
            dict: Transaction data
        """
        return {
            'id': self.id,
            'amount': float(self.amount),  # Convert Decimal to float for JSON
            'description': self.description,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def soft_delete(self):
        """
        Soft delete transaction (set is_deleted=True).
        
        Why soft delete?
        - Preserves data for audit trail
        - Allows undo functionality
        - Maintains referential integrity
        
        Example:
            transaction.soft_delete()
            db.session.commit()
        """
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """
        Restore soft-deleted transaction.
        
        Example:
            transaction.restore()
            db.session.commit()
        """
        self.is_deleted = False
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_balance(user_id, include_deleted=False):
        """
        Calculate user's current balance (income - expenses).
        
        Why static method?
        - Doesn't need instance (self)
        - Operates on multiple transactions
        - Utility function
        
        Args:
            user_id (int): User ID
            include_deleted (bool): Include soft-deleted transactions
        
        Returns:
            Decimal: Current balance
        """
        query = Transaction.query.filter_by(user_id=user_id)
        
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        transactions = query.all()
        
        balance = Decimal('0.00')
        
        for transaction in transactions:
            if transaction.transaction_type == 'income':
                balance += transaction.amount
            else:  # expense
                balance -= transaction.amount
        
        return balance
    
    @classmethod
    def get_monthly_summary(cls, user_id, year, month):
        """
        Get income/expense summary for a specific month.
        
        Args:
            user_id (int): User ID
            year (int): Year (e.g., 2026)
            month (int): Month (1-12)
        
        Returns:
            dict: {'income': Decimal, 'expense': Decimal, 'balance': Decimal}
        """
        from sqlalchemy import extract
        
        transactions = cls.query.filter(
            cls.user_id == user_id,
            cls.is_deleted == False,
            extract('year', cls.transaction_date) == year,
            extract('month', cls.transaction_date) == month
        ).all()
        
        income = Decimal('0.00')
        expense = Decimal('0.00')
        
        for transaction in transactions:
            if transaction.transaction_type == 'income':
                income += transaction.amount
            else:
                expense += transaction.amount
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense
        }
