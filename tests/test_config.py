"""
Test configuration classes.

Why test configuration?
- Ensure correct settings loaded for each environment
- Verify environment variables parsed correctly
- Catch configuration errors early
"""

import pytest
from config import DevelopmentConfig, TestingConfig, ProductionConfig


class TestDevelopmentConfig:
    """Test development configuration."""
    
    def test_debug_enabled(self):
        """Development should have debug enabled."""
        assert DevelopmentConfig.DEBUG is True
    
    def test_testing_disabled(self):
        """Development should not be in testing mode."""
        assert DevelopmentConfig.TESTING is False
    
    def test_sql_echo_enabled(self):
        """Development should log SQL queries."""
        assert DevelopmentConfig.SQLALCHEMY_ECHO is True


class TestTestingConfig:
    """Test testing configuration."""
    
    def test_testing_enabled(self):
        """Testing config should have testing enabled."""
        assert TestingConfig.TESTING is True
    
    def test_debug_disabled(self):
        """Testing should not have debug enabled."""
        assert TestingConfig.DEBUG is False
    
    def test_sqlite_database(self):
        """Testing should use in-memory SQLite."""
        assert 'sqlite:///:memory:' in TestingConfig.SQLALCHEMY_DATABASE_URI
    
    def test_csrf_disabled(self):
        """Testing should have CSRF disabled for easier form testing."""
        assert TestingConfig.WTF_CSRF_ENABLED is False


class TestProductionConfig:
    """Test production configuration."""
    
    def test_debug_disabled(self):
        """Production should have debug disabled."""
        assert ProductionConfig.DEBUG is False
    
    def test_testing_disabled(self):
        """Production should not be in testing mode."""
        assert ProductionConfig.TESTING is False
    
    def test_session_cookie_secure(self):
        """Production should require HTTPS for session cookies."""
        assert ProductionConfig.SESSION_COOKIE_SECURE is True
    
    def test_nullpool_configured(self):
        """Production should use NullPool for free-tier database."""
        from sqlalchemy.pool import NullPool
        assert ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS['poolclass'] == NullPool
