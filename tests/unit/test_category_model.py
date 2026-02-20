"""
Unit tests for Category model.

Why test categories?
- Verify unique constraint (user can't have duplicate category names)
- Test default vs custom categories
- Test relationship to User
- Test helper methods (get_default_categories, create_default_categories_for_user)
"""

import pytest
from app import db
from app.models.user import User
from app.models.category import Category


class TestCategoryModel:
    """Test suite for Category model."""
    
    def test_create_category(self, app):
        """
        Test creating a basic category.
        
        Why this test?
        - Verifies Category model can be created
        - Tests required fields are set
        """
        with app.app_context():
            # Create user first (category needs user_id)
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Create category
            category = Category(
                name='Food',
                user_id=user.id,
                is_default=False
            )
            db.session.add(category)
            db.session.commit()
            
            # Verify category was saved
            assert category.id is not None
            assert category.name == 'Food'
            assert category.user_id == user.id
            assert category.is_default is False
            assert category.created_at is not None
    
    def test_default_category(self, app):
        """
        Test creating a default category.
        
        Why this test?
        - Verifies is_default flag works
        - Default categories are system-provided
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(
                name='Rent/Mortgage',
                user_id=user.id,
                is_default=True
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.is_default is True
    
    def test_unique_category_per_user(self, app):
        """
        Test user cannot have duplicate category names.
        
        Why this test?
        - Database constraint: (user_id, name) must be unique
        - Prevents confusion (two "Food" categories for same user)
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Create first category
            category1 = Category(name='Food', user_id=user.id)
            db.session.add(category1)
            db.session.commit()
            
            # Try to create duplicate category for same user
            category2 = Category(name='Food', user_id=user.id)
            db.session.add(category2)
            
            # Should raise IntegrityError
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_different_users_same_category_name(self, app):
        """
        Test different users CAN have categories with same name.
        
        Why this test?
        - Unique constraint is per user, not global
        - User A can have "Food", User B can also have "Food"
        """
        with app.app_context():
            # Create two users
            user1 = User(username='user1', email='user1@example.com')
            user1.set_password('password')
            user2 = User(username='user2', email='user2@example.com')
            user2.set_password('password')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Both users create "Food" category
            category1 = Category(name='Food', user_id=user1.id)
            category2 = Category(name='Food', user_id=user2.id)
            db.session.add_all([category1, category2])
            db.session.commit()
            
            # Should succeed (different users)
            assert category1.id is not None
            assert category2.id is not None
            assert category1.name == category2.name
            assert category1.user_id != category2.user_id
    
    def test_category_repr(self, app):
        """
        Test __repr__ method shows category type.
        
        Why this test?
        - Helpful for debugging
        - Shows if category is default or custom
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Default category
            default_cat = Category(name='Food', user_id=user.id, is_default=True)
            assert 'default' in repr(default_cat).lower()
            
            # Custom category
            custom_cat = Category(name='Custom', user_id=user.id, is_default=False)
            assert 'custom' in repr(custom_cat).lower()
    
    def test_to_dict(self, app):
        """
        Test to_dict method returns category data.
        
        Why this test?
        - Verifies JSON serialization works
        - Useful for API responses
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id, is_default=True)
            db.session.add(category)
            db.session.commit()
            
            category_dict = category.to_dict()
            
            # Should contain all fields
            assert category_dict['name'] == 'Food'
            assert category_dict['user_id'] == user.id
            assert category_dict['is_default'] is True
            assert 'id' in category_dict
            assert 'created_at' in category_dict
    
    def test_get_default_categories(self, app):
        """
        Test get_default_categories static method.
        
        Why this test?
        - Verifies default category list is defined
        - Ensures we have common categories (Food, Rent, etc.)
        """
        with app.app_context():
            default_categories = Category.get_default_categories()
            
            # Should return a list
            assert isinstance(default_categories, list)
            
            # Should have reasonable number of categories
            assert len(default_categories) > 5
            
            # Should include common categories
            assert 'Food & Dining' in default_categories
            assert 'Rent/Mortgage' in default_categories
            assert 'Income' in default_categories
    
    def test_create_default_categories_for_user(self, app):
        """
        Test creating default categories for a new user.
        
        Why this test?
        - Verifies helper method creates all default categories
        - Called when new user signs up
        - Ensures user starts with useful categories
        """
        with app.app_context():
            # Create user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Create default categories
            categories = Category.create_default_categories_for_user(user.id)
            
            # Should create multiple categories
            assert len(categories) > 5
            
            # All should be default categories
            for category in categories:
                assert category.is_default is True
                assert category.user_id == user.id
            
            # Verify categories are in database
            db_categories = Category.query.filter_by(user_id=user.id).all()
            assert len(db_categories) == len(categories)
    
    def test_cascade_delete_with_user(self, app):
        """
        Test categories are deleted when user is deleted.
        
        Why this test?
        - Verifies CASCADE delete works
        - When user deleted, their categories should be deleted too
        - Data cleanup
        """
        with app.app_context():
            # Create user with category
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            category_id = category.id
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            # Category should be deleted too
            deleted_category = Category.query.get(category_id)
            assert deleted_category is None
