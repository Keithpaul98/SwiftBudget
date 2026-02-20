"""
Test Flask application factory.

Why test app factory?
- Ensure app creates successfully
- Verify extensions initialized
- Test different configurations
"""

import pytest
from app import create_app, db, login_manager, bcrypt, mail


class TestAppFactory:
    """Test application factory function."""
    
    def test_create_app_development(self):
        """Test creating app with development config."""
        app = create_app('development')
        
        assert app is not None
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False
    
    def test_create_app_testing(self):
        """Test creating app with testing config."""
        app = create_app('testing')
        
        assert app is not None
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is False
    
    def test_create_app_production(self):
        """Test creating app with production config."""
        app = create_app('production')
        
        assert app is not None
        assert app.config['DEBUG'] is False
        assert app.config['SESSION_COOKIE_SECURE'] is True
    
    def test_extensions_initialized(self, app):
        """Test that all extensions are initialized."""
        # Database
        assert db is not None
        
        # Flask-Login
        assert login_manager is not None
        assert login_manager.login_view == 'auth.login'
        
        # Bcrypt
        assert bcrypt is not None
        
        # Flask-Mail
        assert mail is not None
    
    def test_error_handlers_registered(self, client):
        """Test that error handlers are registered."""
        # Test 404 handler
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'error' in response.data
    
    def test_logging_configured(self, app):
        """Test that logging is configured."""
        assert app.logger is not None
        
        # Test logging works
        app.logger.info('Test log message')
        # If no exception raised, logging is working
