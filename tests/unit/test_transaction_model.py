"""
Unit tests for Transaction model.

Why test transactions?
- Verify NUMERIC(10,2) data type works correctly
- Test amount validation (positive numbers only)
- Test transaction types (income/expense)
- Test soft delete functionality
- Test balance calculations
- Critical: financial data must be exact (no rounding errors)
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from app import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction


class TestTransactionModel:
    """Test suite for Transaction model."""
    
    def test_create_expense_transaction(self, app):
        """
        Test creating an expense transaction.
        
        Why this test?
        - Verifies Transaction model can be created
        - Tests NUMERIC data type
        - Tests required fields
        """
        with app.app_context():
            # Create user and category
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create transaction
            transaction = Transaction(
                amount=Decimal('50.25'),
                description='Grocery shopping',
                transaction_type='expense',
                transaction_date=date(2026, 2, 20),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Verify transaction was saved
            assert transaction.id is not None
            assert transaction.amount == Decimal('50.25')
            assert transaction.transaction_type == 'expense'
            assert transaction.is_deleted is False
    
    def test_create_income_transaction(self, app):
        """
        Test creating an income transaction.
        
        Why this test?
        - Verifies 'income' transaction type works
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Salary', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=Decimal('5000.00'),
                description='Monthly salary',
                transaction_type='income',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert transaction.transaction_type == 'income'
            assert transaction.amount == Decimal('5000.00')
    
    def test_numeric_precision(self, app):
        """
        Test NUMERIC(10,2) maintains exact decimal precision.
        
        Why this test?
        - CRITICAL: Financial data must be exact
        - NUMERIC avoids floating-point errors
        - Example: 0.1 + 0.2 should equal 0.3 exactly
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Test exact decimal arithmetic
            transaction = Transaction(
                amount=Decimal('0.10') + Decimal('0.20'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Should be exactly 0.30, not 0.30000000000000004
            assert transaction.amount == Decimal('0.30')
            assert str(transaction.amount) == '0.30'
    
    def test_positive_amount_constraint(self, app):
        """
        Test amount must be positive.
        
        Why this test?
        - Database CHECK constraint: amount > 0
        - Prevents negative amounts (use transaction_type instead)
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Try to create transaction with negative amount
            transaction = Transaction(
                amount=Decimal('-50.00'),  # Negative amount
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            
            # Should raise IntegrityError (CHECK constraint violation)
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_invalid_transaction_type(self, app):
        """
        Test transaction_type must be 'income' or 'expense'.
        
        Why this test?
        - Database CHECK constraint validates transaction_type
        - Prevents typos or invalid values
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Try invalid transaction type
            transaction = Transaction(
                amount=Decimal('50.00'),
                transaction_type='invalid',  # Invalid type
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_soft_delete(self, app):
        """
        Test soft delete functionality.
        
        Why this test?
        - Verifies soft_delete() method works
        - Transaction marked as deleted but not removed from database
        - Preserves audit trail
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            transaction_id = transaction.id
            
            # Soft delete
            transaction.soft_delete()
            db.session.commit()
            
            # Transaction still exists in database
            deleted_transaction = Transaction.query.get(transaction_id)
            assert deleted_transaction is not None
            assert deleted_transaction.is_deleted is True
    
    def test_restore_deleted_transaction(self, app):
        """
        Test restoring a soft-deleted transaction.
        
        Why this test?
        - Verifies restore() method works
        - Allows undo functionality
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Soft delete then restore
            transaction.soft_delete()
            db.session.commit()
            assert transaction.is_deleted is True
            
            transaction.restore()
            db.session.commit()
            assert transaction.is_deleted is False
    
    def test_get_balance(self, app):
        """
        Test balance calculation (income - expenses).
        
        Why this test?
        - Verifies get_balance() static method
        - Tests income/expense arithmetic
        - Critical for dashboard display
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='General', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create income transaction
            income = Transaction(
                amount=Decimal('5000.00'),
                transaction_type='income',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            # Create expense transactions
            expense1 = Transaction(
                amount=Decimal('1500.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            expense2 = Transaction(
                amount=Decimal('500.50'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            db.session.add_all([income, expense1, expense2])
            db.session.commit()
            
            # Balance = 5000 - 1500 - 500.50 = 2999.50
            balance = Transaction.get_balance(user.id)
            assert balance == Decimal('2999.50')
    
    def test_get_balance_excludes_deleted(self, app):
        """
        Test balance calculation excludes soft-deleted transactions.
        
        Why this test?
        - Deleted transactions shouldn't affect current balance
        - Unless explicitly requested (include_deleted=True)
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='General', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create two expenses
            expense1 = Transaction(
                amount=Decimal('100.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            expense2 = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            db.session.add_all([expense1, expense2])
            db.session.commit()
            
            # Delete one expense
            expense1.soft_delete()
            db.session.commit()
            
            # Balance should only include active transaction
            balance = Transaction.get_balance(user.id, include_deleted=False)
            assert balance == Decimal('-50.00')
            
            # With deleted transactions included
            balance_with_deleted = Transaction.get_balance(user.id, include_deleted=True)
            assert balance_with_deleted == Decimal('-150.00')
    
    def test_to_dict(self, app):
        """
        Test to_dict method converts Decimal to float for JSON.
        
        Why this test?
        - JSON doesn't support Decimal type
        - Verifies conversion works correctly
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=Decimal('123.45'),
                description='Test transaction',
                transaction_type='expense',
                transaction_date=date(2026, 2, 20),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            transaction_dict = transaction.to_dict()
            
            # Should contain all fields
            assert transaction_dict['amount'] == 123.45  # Converted to float
            assert isinstance(transaction_dict['amount'], float)
            assert transaction_dict['description'] == 'Test transaction'
            assert transaction_dict['transaction_type'] == 'expense'
            assert 'transaction_date' in transaction_dict
    
    def test_transaction_repr(self, app):
        """
        Test __repr__ method shows useful information.
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date(2026, 2, 20),
                user_id=user.id,
                category_id=category.id
            )
            
            repr_string = repr(transaction)
            
            # Should contain type and amount
            assert 'expense' in repr_string.lower()
            assert '50' in repr_string
