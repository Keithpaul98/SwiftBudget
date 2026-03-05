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
    # SECURITY: SECRET_KEY must be set in environment variables
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Allow weak key only in development/testing
        import sys
        if 'pytest' not in sys.modules and os.getenv('FLASK_ENV') == 'production':
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        SECRET_KEY = 'dev-secret-key-ONLY-for-development'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/swiftbudget_dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable Flask-SQLAlchemy event system (saves memory)
    
    # Why SQLALCHEMY_TRACK_MODIFICATIONS = False?
    # - Flask-SQLAlchemy's event system is rarely needed
    # - Disabling it reduces memory overhead
    # - SQLAlchemy's own event system still works
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Sessions expire after 2 hours (security)
    
    # Bcrypt Configuration
    # Lower rounds for production free tier (512MB RAM limit)
    # Default is 12, using 10 for better performance on limited resources
    BCRYPT_LOG_ROUNDS = 10
    SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access (XSS protection)
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on activity
    
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
    
    # Cloudinary Configuration (image CDN)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
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
    
    # Disable rate limiting in tests (allows unlimited requests)
    RATELIMIT_ENABLED = False


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
    
    # Database Connection Pooling - Optimized for production
    # Using small pool size for better performance while managing connections
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,  # 5 persistent connections
        'max_overflow': 10,  # Allow 10 additional connections under load
        'pool_timeout': 30,  # Wait 30s for connection
        'pool_recycle': 1800,  # Recycle connections every 30 min
        'pool_pre_ping': True,  # Verify connection before use
    }
    
    # Alternative for very limited connection tiers (e.g., Supabase free tier):
    # from sqlalchemy.pool import NullPool
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     'poolclass': NullPool,
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
