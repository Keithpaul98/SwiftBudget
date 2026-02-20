"""
Configuration classes for SwiftBudget application.

Why separate configs?
- Different settings for development, testing, and production
- Prevents accidental use of debug mode in production
- Allows easy switching between environments
- Follows Flask best practices (12-factor app methodology)
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """
    Base configuration class.
    Contains settings common to all environments.
    """
    
    # Flask Core Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/swiftbudget_dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable Flask-SQLAlchemy event system (saves memory)
    
    # Why SQLALCHEMY_TRACK_MODIFICATIONS = False?
    # - Flask-SQLAlchemy's event system is rarely needed
    # - Disabling it reduces memory overhead
    # - SQLAlchemy's own event system still works
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Sessions expire after 24 hours
    SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access (XSS protection)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # Email Configuration (Gmail SMTP)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    # Currency Configuration
    CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', 'MK')
    CURRENCY_CODE = os.getenv('CURRENCY_CODE', 'MWK')  # Malawi Kwacha
    
    # Email sender configuration
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    
    # Rate Limiting (Flask-Limiter)
    RATELIMIT_STORAGE_URL = 'memory://'  # Use Redis in production for distributed systems
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/swiftbudget.log')


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Why separate development config?
    - Debug mode enabled for detailed error pages
    - SQL queries logged for debugging
    - Less strict security (no HTTPS required)
    """
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_ECHO = True  # Log all SQL queries (helpful for debugging)
    
    # Session
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development (no HTTPS required)
    
    # Email (optional in development)
    MAIL_SUPPRESS_SEND = False  # Set to True to prevent actual email sending


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Why separate testing config?
    - Uses in-memory SQLite for fast tests
    - CSRF disabled for easier form testing
    - Email sending suppressed
    """
    
    TESTING = True
    DEBUG = False
    
    # Use SQLite in-memory database for tests (fast, isolated)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing (easier to test forms)
    WTF_CSRF_ENABLED = False
    
    # Suppress email sending in tests
    MAIL_SUPPRESS_SEND = True
    
    # Faster password hashing in tests (bcrypt cost factor 4 instead of 12)
    BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Why separate production config?
    - Debug mode disabled (security)
    - HTTPS enforced
    - Connection pooling optimized for free tier
    - Strict security settings
    """
    
    DEBUG = False
    TESTING = False
    
    # Database Connection Pooling (CRITICAL for free tier - see DDD section 10.3)
    # Why NullPool? Supabase free tier has 60 connection limit
    # NullPool opens/closes connections per request, preventing exhaustion
    from sqlalchemy.pool import NullPool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool,  # No persistent connections
        'pool_pre_ping': True,  # Verify connection before use
    }
    
    # Alternative: Small pool size (if you prefer persistent connections)
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     'pool_size': 5,
    #     'max_overflow': 10,
    #     'pool_recycle': 3600,
    #     'pool_pre_ping': True,
    # }
    
    # Session Security (HTTPS only)
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    
    # Email
    MAIL_SUPPRESS_SEND = False  # Enable email sending in production


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class by name.
    
    Args:
        config_name (str): Name of configuration ('development', 'testing', 'production')
    
    Returns:
        Config class
    
    Example:
        config_class = get_config('production')
        app.config.from_object(config_class)
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)
