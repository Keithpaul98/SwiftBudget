"""
Pytest configuration and fixtures.

Why conftest.py?
- Shared fixtures available to all tests
- Configuration for pytest
- Setup/teardown for test database

This file will be expanded in Module 2 when we add database models.
"""

import pytest
from app import create_app, db
from app.models.user import User
from app.models.category import Category


@pytest.fixture(scope='session')
def app():
    """
    Create application for testing.
    
    Scope='session': Created once per test session (all tests share same app)
    
    Why testing config?
    - Uses in-memory SQLite (fast, isolated)
    - CSRF disabled (easier form testing)
    - Email suppressed
    """
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Flask test client.
    
    Why test client?
    - Simulates HTTP requests without running server
    - Used for integration tests (testing routes)
    
    Example:
        response = client.get('/dashboard')
        assert response.status_code == 200
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Flask CLI test runner.
    
    Why CLI runner?
    - Test Flask CLI commands
    - Example: flask db upgrade, custom commands
    """
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_database(app):
    """
    Reset database before each test.
    
    Why autouse=True?
    - Runs automatically before every test
    - Ensures test isolation (each test starts with clean database)
    
    Why needed?
    - Tests can modify database (create users, transactions)
    - Without reset, tests would interfere with each other
    """
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()


@pytest.fixture
def test_user(app):
    """
    Create a test user for authentication tests.
    
    Returns a user with:
    - username: testuser
    - email: test@example.com
    - password: password123 (hashed)
    """
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture
def test_category(app, test_user):
    """
    Create a test category for transaction tests.
    
    Returns an expense category owned by test_user.
    """
    with app.app_context():
        category = Category(
            name='Test Category',
            user_id=test_user.id,
            is_default=False
        )
        db.session.add(category)
        db.session.commit()
        
        db.session.refresh(category)
        return category


class AuthActions:
    """
    Helper class for authentication actions in tests.
    
    Provides login/logout methods for testing.
    """
    def __init__(self, client, test_user):
        self._client = client
        self._test_user = test_user
    
    def login(self, email=None, password=None):
        """Login with test user credentials."""
        return self._client.post('/auth/login', data={
            'email': email or self._test_user.email,
            'password': password or 'password123',
            'csrf_token': 'test'
        }, follow_redirects=True)
    
    def logout(self):
        """Logout current user."""
        return self._client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def auth(client, test_user):
    """
    Authentication helper fixture.
    
    Provides easy login/logout for tests.
    
    Example:
        auth.login()
        response = client.get('/dashboard')
        auth.logout()
    """
    return AuthActions(client, test_user)


@pytest.fixture
def db_session(app):
    """
    Provide database session for tests that need direct DB access.
    
    Returns the db object for database operations.
    """
    return db
