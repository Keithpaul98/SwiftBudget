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
