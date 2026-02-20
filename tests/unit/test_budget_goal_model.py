"""
Unit tests for BudgetGoal model.

Why test budget goals?
- Verify budget limits work correctly
- Test different period types (monthly, weekly, yearly)
- Test alert threshold calculations
- Test spending vs budget comparisons
- Critical for budget tracking feature
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from app import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget_goal import BudgetGoal


class TestBudgetGoalModel:
    """Test suite for BudgetGoal model."""
    
    def test_create_budget_goal(self, app):
        """
        Test creating a basic budget goal.
        
        Why this test?
        - Verifies BudgetGoal model can be created
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
            
            # Create budget goal
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Verify budget was saved
            assert budget.id is not None
            assert budget.amount == Decimal('500.00')
            assert budget.period == 'monthly'
            assert budget.alert_threshold == 80  # Default
            assert budget.is_active is True
    
    def test_budget_periods(self, app):
        """
        Test different budget periods (monthly, weekly, yearly).
        
        Why this test?
        - Verifies all period types are supported
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Test each period type
            for period in ['monthly', 'weekly', 'yearly']:
                budget = BudgetGoal(
                    amount=Decimal('100.00'),
                    period=period,
                    user_id=user.id,
                    category_id=category.id
                )
                assert budget.period == period
    
    def test_invalid_period(self, app):
        """
        Test invalid period type is rejected.
        
        Why this test?
        - Database CHECK constraint validates period
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Try invalid period
            budget = BudgetGoal(
                amount=Decimal('100.00'),
                period='invalid',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_positive_amount_constraint(self, app):
        """
        Test budget amount must be positive.
        
        Why this test?
        - Database CHECK constraint: amount > 0
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Try negative amount
            budget = BudgetGoal(
                amount=Decimal('-100.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_alert_threshold_range(self, app):
        """
        Test alert_threshold must be between 0 and 100.
        
        Why this test?
        - Percentage value must be valid
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Try invalid threshold (> 100)
            budget = BudgetGoal(
                amount=Decimal('100.00'),
                period='monthly',
                alert_threshold=150,
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_unique_budget_per_category(self, app):
        """
        Test user can only have one budget goal per category.
        
        Why this test?
        - Unique constraint: (user_id, category_id)
        - Prevents confusion (multiple budgets for same category)
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create first budget
            budget1 = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget1)
            db.session.commit()
            
            # Try to create second budget for same category
            budget2 = BudgetGoal(
                amount=Decimal('600.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget2)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_get_current_period_spending(self, app):
        """
        Test calculating spending for current period.
        
        Why this test?
        - Verifies spending calculation works
        - Critical for budget tracking
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            # Create budget goal
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Create transactions
            transaction1 = Transaction(
                amount=Decimal('100.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            transaction2 = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            
            db.session.add_all([transaction1, transaction2])
            db.session.commit()
            
            # Get spending
            spending = budget.get_current_period_spending()
            assert spending == Decimal('150.00')
    
    def test_get_remaining_budget(self, app):
        """
        Test calculating remaining budget.
        
        Why this test?
        - Shows how much budget is left
        - Budget - Spending = Remaining
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Create transaction
            transaction = Transaction(
                amount=Decimal('200.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Remaining = 500 - 200 = 300
            remaining = budget.get_remaining_budget()
            assert remaining == Decimal('300.00')
    
    def test_get_percentage_used(self, app):
        """
        Test calculating percentage of budget used.
        
        Why this test?
        - Shows budget usage as percentage
        - Used for alerts and progress bars
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Spend 400 out of 500 = 80%
            transaction = Transaction(
                amount=Decimal('400.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            percentage = budget.get_percentage_used()
            assert percentage == 80.0
    
    def test_is_over_budget(self, app):
        """
        Test detecting when budget is exceeded.
        
        Why this test?
        - Alerts user when spending exceeds budget
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Spend more than budget
            transaction = Transaction(
                amount=Decimal('600.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert budget.is_over_budget() is True
    
    def test_should_alert(self, app):
        """
        Test alert triggers at threshold.
        
        Why this test?
        - Verifies alert logic works
        - Default threshold is 80%
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                alert_threshold=80,
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            # Spend 400 (80%) - should alert
            transaction = Transaction(
                amount=Decimal('400.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert budget.should_alert() is True
    
    def test_to_dict(self, app):
        """
        Test to_dict method returns budget data.
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            budget = BudgetGoal(
                amount=Decimal('500.00'),
                period='monthly',
                alert_threshold=75,
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(budget)
            db.session.commit()
            
            budget_dict = budget.to_dict()
            
            assert budget_dict['amount'] == 500.00
            assert budget_dict['period'] == 'monthly'
            assert budget_dict['alert_threshold'] == 75
            assert budget_dict['is_active'] is True
