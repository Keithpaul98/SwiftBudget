"""
Unit tests for CategoryService.

Why test services?
- Business logic validation
- Ensure error handling works
- Verify authorization checks
- Test edge cases
"""

import pytest
from decimal import Decimal
from app import db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.services.category_service import CategoryService


class TestCategoryService:
    """Test suite for CategoryService."""
    
    def test_create_category(self, app):
        """Test creating a new category."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id)
            
            assert category.id is not None
            assert category.name == 'Food'
            assert category.user_id == user.id
            assert category.is_default is False
    
    def test_create_duplicate_category(self, app):
        """Test creating duplicate category raises error."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            CategoryService.create_category('Food', user.id)
            
            with pytest.raises(ValueError, match='already exists'):
                CategoryService.create_category('Food', user.id)
    
    def test_get_user_categories(self, app):
        """Test getting all user categories."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            CategoryService.create_category('Food', user.id)
            CategoryService.create_category('Rent', user.id)
            
            categories = CategoryService.get_user_categories(user.id)
            
            assert len(categories) == 2
            assert categories[0].name == 'Food'
            assert categories[1].name == 'Rent'
    
    def test_update_category(self, app):
        """Test updating category name."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id)
            
            updated = CategoryService.update_category(category.id, user.id, 'Groceries')
            
            assert updated.name == 'Groceries'
    
    def test_cannot_update_default_category(self, app):
        """Test cannot update default categories."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id, is_default=True)
            
            with pytest.raises(ValueError, match='Cannot modify default'):
                CategoryService.update_category(category.id, user.id, 'Groceries')
    
    def test_delete_category(self, app):
        """Test deleting a category."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id)
            
            CategoryService.delete_category(category.id, user.id)
            
            deleted = Category.query.get(category.id)
            assert deleted is None
    
    def test_cannot_delete_category_with_transactions(self, app):
        """Test cannot delete category with transactions."""
        with app.app_context():
            from datetime import date
            
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id)
            
            # Create transaction
            transaction = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            with pytest.raises(ValueError, match='Cannot delete category with'):
                CategoryService.delete_category(category.id, user.id)
    
    def test_get_category_statistics(self, app):
        """Test getting category statistics."""
        with app.app_context():
            from datetime import date
            
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = CategoryService.create_category('Food', user.id)
            
            # Create transactions
            t1 = Transaction(
                amount=Decimal('100.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            t2 = Transaction(
                amount=Decimal('50.00'),
                transaction_type='expense',
                transaction_date=date.today(),
                user_id=user.id,
                category_id=category.id
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            
            stats = CategoryService.get_category_statistics(category.id, user.id)
            
            assert stats['transaction_count'] == 2
            assert stats['total_spent'] == 150.0
            assert stats['total_earned'] == 0.0
