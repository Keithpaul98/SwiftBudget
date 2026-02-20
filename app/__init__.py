"""
Flask Application Factory.

Why use an application factory?
1. Multiple Instances: Can create multiple app instances (e.g., for testing)
2. Configuration Flexibility: Easy to switch between dev/test/prod configs
3. Extension Initialization: Extensions initialized with app context
4. Circular Import Prevention: Avoids circular imports in large applications
5. Testing: Each test can have its own isolated app instance

Pattern: Application Factory Pattern
Reference: https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import get_config

# Initialize extensions (but don't bind to app yet)
# Why initialize here? Extensions need to be imported by models/routes
# Why not bind to app? App doesn't exist yet (created in create_app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=["200 per day", "50 per hour"]  # Default limits for all routes
)


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name (str): Configuration name ('development', 'testing', 'production')
    
    Returns:
        Flask: Configured Flask application instance
    
    Example:
        app = create_app('production')
        app.run()
    """
    
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    # Why here? Now that app exists, we can bind extensions to it
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'  # Flash message category
    
    # Why set login_view? Flask-Login needs to know where to redirect
    # unauthenticated users who try to access @login_required routes
    
    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        """
        Load user by ID for Flask-Login.
        
        Why user_loader?
        - Flask-Login needs to reload user from session
        - Called on every request for authenticated users
        - Returns User object or None
        
        Args:
            user_id (str): User ID from session
        
        Returns:
            User: User object or None if not found
        """
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Configure logging (only in production/development, not testing)
    if not app.config['TESTING']:
        configure_logging(app)
    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Future blueprints (Module 5+)
    # from app.routes.dashboard import dashboard_bp
    # from app.routes.transactions import transactions_bp
    # app.register_blueprint(dashboard_bp)
    # app.register_blueprint(transactions_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Import models (required for Flask-Migrate to detect them)
    # Why here? Models need app context and db to be initialized first
    with app.app_context():
        from app.models import User, Category, Transaction, BudgetGoal
        
        # Note: db.create_all() disabled - using Flask-Migrate instead
        # Database schema is now managed by migrations (flask db upgrade)
        # This ensures consistent schema across dev/test/prod environments
    
    # Log startup message
    app.logger.info(f'SwiftBudget started in {config_name} mode')
    
    return app


def configure_logging(app):
    """
    Configure application logging.
    
    Why separate logging function?
    - Keeps create_app() clean and focused
    - Logging configuration is complex enough to warrant its own function
    - Easier to modify logging without touching app factory
    
    Logging Strategy:
    - Development: Console + file (DEBUG level)
    - Production: File only (INFO level)
    - Rotating file handler prevents log files from growing infinitely
    """
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    
    # File handler (rotating to prevent huge log files)
    # Why rotating? Log files can grow infinitely, filling disk space
    # maxBytes=10MB, backupCount=10 means max 100MB of logs
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    
    # Log format: timestamp, level, message, file location
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # In development, also log to console
    if app.config['DEBUG']:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)


def register_error_handlers(app):
    """
    Register custom error handlers.
    
    Why custom error handlers?
    - Provide user-friendly error pages (not stack traces)
    - Log errors for debugging
    - Maintain consistent UI even on errors
    - Security: Don't expose internal details to users
    """
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        app.logger.warning(f'404 error: {error}')
        # TODO: Render custom 404 template in future module
        return {'error': 'Page not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'500 error: {error}')
        db.session.rollback()  # Rollback any failed database transactions
        # TODO: Render custom 500 template in future module
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors (authorization failures)."""
        app.logger.warning(f'403 error: {error}')
        return {'error': 'Access forbidden'}, 403
