"""
Transaction Service - Business logic for transaction management.

Why TransactionService?
- Encapsulates transaction CRUD operations
- Handles soft deletes (is_deleted flag)
- Validates transaction data
- Calculates spending summaries
- Filters transactions by date, category, type

Design Pattern: Service Layer Pattern
"""

from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from app import db
from app.models.transaction import Transaction
from app.models.category import Category


class TransactionService:
    """Service class for transaction operations."""
    
    @staticmethod
    def create_transaction(
        user_id: int,
        amount: Decimal,
        category_id: int,
        transaction_type: str,
        transaction_date: date,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Create a new transaction.
        
        Validations:
        - Amount must be positive
        - Category must exist and belong to user
        - Transaction type must be 'income' or 'expense'
        
        Args:
            user_id: User ID
            amount: Transaction amount (positive)
            category_id: Category ID
            transaction_type: 'income' or 'expense'
            transaction_date: Date of transaction
            description: Optional description
        
        Returns:
            Created Transaction object
        
        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError('Amount must be positive')
        
        # Validate transaction type
        if transaction_type not in ['income', 'expense']:
            raise ValueError('Transaction type must be "income" or "expense"')
        
        # Validate category ownership
        category = Category.query.filter_by(id=category_id, user_id=user_id).first()
        if not category:
            raise ValueError('Category not found or does not belong to user')
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            category_id=category_id,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            description=description
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def get_transaction_by_id(transaction_id: int, user_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID (with user ownership check).
        
        Why filter by is_deleted=False?
        - Soft deletes: Don't show deleted transactions
        - User can't access deleted transactions
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID (for ownership verification)
        
        Returns:
            Transaction object or None
        """
        return Transaction.query.filter_by(
            id=transaction_id,
            user_id=user_id,
            is_deleted=False
        ).first()
    
    @staticmethod
    def get_user_transactions(
        user_id: int,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Transaction]:
        """
        Get user transactions with optional filters.
        
        Why flexible filtering?
        - Dashboard: Show recent transactions
        - Reports: Filter by date range
        - Category view: Show transactions for specific category
        - Budget tracking: Filter by type and date
        
        Args:
            user_id: User ID
            category_id: Filter by category (optional)
            transaction_type: Filter by type: 'income' or 'expense' (optional)
            start_date: Filter from this date (optional)
            end_date: Filter to this date (optional)
            limit: Maximum number of transactions (optional)
        
        Returns:
            List of Transaction objects (newest first)
        """
        query = Transaction.query.filter_by(user_id=user_id, is_deleted=False)
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Order by date (newest first)
        query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def update_transaction(
        transaction_id: int,
        user_id: int,
        amount: Optional[Decimal] = None,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        transaction_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Update a transaction.
        
        Why allow partial updates?
        - User might only want to change amount
        - Flexibility in UI design
        - Only update what's provided
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID (for ownership verification)
            amount: New amount (optional)
            category_id: New category ID (optional)
            transaction_type: New type (optional)
            transaction_date: New date (optional)
            description: New description (optional)
        
        Returns:
            Updated Transaction object
        
        Raises:
            ValueError: If validation fails or transaction not found
        """
        transaction = TransactionService.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            raise ValueError('Transaction not found')
        
        # Update fields if provided
        if amount is not None:
            if amount <= 0:
                raise ValueError('Amount must be positive')
            transaction.amount = amount
        
        if category_id is not None:
            # Validate category ownership
            category = Category.query.filter_by(id=category_id, user_id=user_id).first()
            if not category:
                raise ValueError('Category not found or does not belong to user')
            transaction.category_id = category_id
        
        if transaction_type is not None:
            if transaction_type not in ['income', 'expense']:
                raise ValueError('Transaction type must be "income" or "expense"')
            transaction.transaction_type = transaction_type
        
        if transaction_date is not None:
            transaction.transaction_date = transaction_date
        
        if description is not None:
            transaction.description = description
        
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def delete_transaction(transaction_id: int, user_id: int) -> None:
        """
        Soft delete a transaction.
        
        Why soft delete?
        - Data preservation: Keep transaction history
        - Undo capability: Can restore if needed
        - Audit trail: Know what was deleted and when
        - Budget calculations: Can exclude deleted transactions
        
        Hard delete would be:
        - db.session.delete(transaction)
        
        Soft delete is:
        - transaction.is_deleted = True
        
        Args:
            transaction_id: Transaction ID
            user_id: User ID (for ownership verification)
        
        Raises:
            ValueError: If transaction not found
        """
        transaction = TransactionService.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            raise ValueError('Transaction not found')
        
        transaction.soft_delete()
        db.session.commit()
    
    @staticmethod
    def get_spending_summary(
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Get spending summary for a user.
        
        Why summary?
        - Dashboard overview: Show total income/expenses
        - Budget tracking: Compare against budget goals
        - Financial insights: Understand spending patterns
        
        Args:
            user_id: User ID
            start_date: Start date for summary (optional, defaults to current month)
            end_date: End date for summary (optional, defaults to today)
        
        Returns:
            Dictionary with summary:
            {
                'total_income': Decimal,
                'total_expenses': Decimal,
                'net_balance': Decimal,
                'transaction_count': int,
                'by_category': {category_name: amount, ...}
            }
        """
        # Default to current month if no dates provided
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
        
        # Get transactions for period
        transactions = TransactionService.get_user_transactions(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate totals
        total_income = sum(
            t.amount for t in transactions if t.transaction_type == 'income'
        )
        total_expenses = sum(
            t.amount for t in transactions if t.transaction_type == 'expense'
        )
        
        # Group by category
        by_category = {}
        for t in transactions:
            category_name = t.category.name
            if category_name not in by_category:
                by_category[category_name] = {
                    'income': Decimal('0.00'),
                    'expense': Decimal('0.00')
                }
            
            if t.transaction_type == 'income':
                by_category[category_name]['income'] += t.amount
            else:
                by_category[category_name]['expense'] += t.amount
        
        return {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_balance': float(total_income - total_expenses),
            'transaction_count': len(transactions),
            'by_category': by_category,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    @staticmethod
    def get_monthly_trend(user_id: int, months: int = 6) -> List[Dict]:
        """
        Get monthly spending trend.
        
        Why trend analysis?
        - Visualize spending over time
        - Identify patterns and anomalies
        - Track progress toward financial goals
        
        Args:
            user_id: User ID
            months: Number of months to include (default 6)
        
        Returns:
            List of monthly summaries:
            [
                {
                    'month': 'YYYY-MM',
                    'income': Decimal,
                    'expenses': Decimal,
                    'net': Decimal
                },
                ...
            ]
        """
        trends = []
        today = date.today()
        
        for i in range(months):
            # Calculate month boundaries
            if i == 0:
                # Current month
                start = today.replace(day=1)
                end = today
            else:
                # Previous months
                month_date = today - timedelta(days=30 * i)
                start = month_date.replace(day=1)
                # Last day of month
                if start.month == 12:
                    end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
            
            # Get summary for month
            summary = TransactionService.get_spending_summary(
                user_id=user_id,
                start_date=start,
                end_date=end
            )
            
            trends.append({
                'month': start.strftime('%Y-%m'),
                'income': summary['total_income'],
                'expenses': summary['total_expenses'],
                'net': summary['net_balance']
            })
        
        # Reverse to show oldest first
        return list(reversed(trends))
