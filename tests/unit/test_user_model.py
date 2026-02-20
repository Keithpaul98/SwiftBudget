"""
Unit tests for User model.

Why test models?
- Verify database constraints work (unique email, required fields)
- Test password hashing/verification
- Test relationships
- Catch bugs early before they reach production

Testing approach:
- Each test is independent (database reset between tests)
- Test one thing per test function
- Use descriptive test names
"""

import pytest
from app import db
from app.models.user import User


class TestUserModel:
    """Test suite for User model."""
    
    def test_create_user(self, app):
        """
        Test creating a basic user.
        
        Why this test?
        - Verifies User model can be created
        - Tests required fields are set
        - Ensures user is saved to database
        """
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was saved
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.created_at is not None
    
    def test_password_hashing(self, app):
        """
        Test password is hashed, not stored as plain text.
        
        Why this test?
        - Security critical: never store plain text passwords
        - Verify bcrypt hashing works
        - Ensure password_hash is different from plain password
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('mypassword')
            
            # Password hash should NOT equal plain password
            assert user.password_hash != 'mypassword'
            
            # Password hash should be a string (bcrypt hash)
            assert isinstance(user.password_hash, str)
            
            # Hash should be reasonably long (bcrypt hashes are ~60 chars)
            assert len(user.password_hash) > 50
    
    def test_password_verification(self, app):
        """
        Test password verification works correctly.
        
        Why this test?
        - Verifies correct password returns True
        - Verifies wrong password returns False
        - Critical for authentication security
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('correctpassword')
            
            # Correct password should verify
            assert user.check_password('correctpassword') is True
            
            # Wrong password should not verify
            assert user.check_password('wrongpassword') is False
            assert user.check_password('CorrectPassword') is False  # Case sensitive
    
    def test_unique_username(self, app):
        """
        Test username must be unique.
        
        Why this test?
        - Database constraint: usernames must be unique
        - Prevents duplicate accounts
        - Verifies IntegrityError is raised on duplicate
        """
        with app.app_context():
            # Create first user
            user1 = User(username='testuser', email='test1@example.com')
            user1.set_password('password')
            db.session.add(user1)
            db.session.commit()
            
            # Try to create second user with same username
            user2 = User(username='testuser', email='test2@example.com')
            user2.set_password('password')
            db.session.add(user2)
            
            # Should raise IntegrityError
            with pytest.raises(Exception):  # SQLAlchemy raises IntegrityError
                db.session.commit()
            
            db.session.rollback()  # Clean up failed transaction
    
    def test_unique_email(self, app):
        """
        Test email must be unique.
        
        Why this test?
        - Database constraint: emails must be unique
        - Prevents duplicate accounts
        - Email used for password reset, must be unique
        """
        with app.app_context():
            # Create first user
            user1 = User(username='user1', email='test@example.com')
            user1.set_password('password')
            db.session.add(user1)
            db.session.commit()
            
            # Try to create second user with same email
            user2 = User(username='user2', email='test@example.com')
            user2.set_password('password')
            db.session.add(user2)
            
            # Should raise IntegrityError
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_user_repr(self, app):
        """
        Test __repr__ method returns useful string.
        
        Why this test?
        - Helpful for debugging
        - Ensures repr doesn't expose sensitive data
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            
            repr_string = repr(user)
            
            # Should contain username
            assert 'testuser' in repr_string
            
            # Should NOT contain password hash (security)
            assert user.password_hash not in repr_string
    
    def test_to_dict(self, app):
        """
        Test to_dict method returns safe user data.
        
        Why this test?
        - Verifies JSON serialization works
        - Ensures password_hash is NOT exposed
        - Critical for API security
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            # Should contain safe fields
            assert user_dict['username'] == 'testuser'
            assert user_dict['email'] == 'test@example.com'
            assert 'id' in user_dict
            assert 'created_at' in user_dict
            
            # Should NOT contain password_hash (security)
            assert 'password_hash' not in user_dict
    
    def test_flask_login_mixin(self, app):
        """
        Test Flask-Login UserMixin methods work.
        
        Why this test?
        - Verifies UserMixin provides required methods
        - is_authenticated, is_active, is_anonymous, get_id()
        - Required for Flask-Login integration
        """
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # UserMixin provides these methods
            assert user.is_authenticated is True
            assert user.is_active is True
            assert user.is_anonymous is False
            assert user.get_id() == str(user.id)
    
    def test_required_fields(self, app):
        """
        Test required fields cannot be null.
        
        Why this test?
        - Verifies database constraints
        - Username, email, password_hash are required
        """
        with app.app_context():
            # Try to create user without username
            user = User(email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
            
            db.session.rollback()
