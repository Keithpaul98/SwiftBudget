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
from flask import Flask, jsonify, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import get_config

# Initialize extensions (but don't bind to app yet)
# Why initialize here? Extensions need to be imported by models/routes
# Why not bind to app? App doesn't exist yet (created in create_app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
csrf = CSRFProtect()
def get_user_identifier():
    """Rate limit by user ID when authenticated, otherwise by IP."""
    if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return f"ip:{get_remote_address()}"

limiter = Limiter(
    key_func=get_user_identifier,  # Rate limit by user when logged in, IP otherwise
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
    csrf.init_app(app)
    
    # Configure Cloudinary (image CDN) if credentials are set
    if app.config.get('CLOUDINARY_CLOUD_NAME'):
        import cloudinary
        cloudinary.config(
            cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=app.config['CLOUDINARY_API_KEY'],
            api_secret=app.config['CLOUDINARY_API_SECRET'],
            secure=True
        )
    
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
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.projects import projects_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(projects_bp)
    
    from app.routes.recurring import recurring_bp
    app.register_blueprint(recurring_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # HTTPS enforcement with Flask-Talisman (production only)
    if not app.config.get('DEBUG') and not app.config.get('TESTING'):
        from flask_talisman import Talisman
        Talisman(app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            session_cookie_secure=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
                'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
                'img-src': ["'self'", "data:", "res.cloudinary.com"],
                'font-src': ["'self'", "cdn.jsdelivr.net", "fonts.gstatic.com"],
                'connect-src': ["'self'", "cdn.jsdelivr.net"],
            }
        )
    else:
        # In development/testing, add security headers manually (no HTTPS)
        @app.after_request
        def set_security_headers(response):
            """Add security headers to all responses."""
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            return response
    
    # Root route redirect
    @app.route('/')
    def index():
        """Redirect root to dashboard or login."""
        if current_user.is_authenticated:
            return redirect(url_for('auth.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'healthy', 'database': 'connected'}), 200
        except Exception as e:
            app.logger.error(f'Health check failed: {e}')
            return jsonify({'status': 'unhealthy', 'error': 'database connection failed'}), 503
    
    # Add currency to template context
    @app.context_processor
    def inject_currency():
        return {
            'currency_symbol': app.config['CURRENCY_SYMBOL'],
            'currency_code': app.config['CURRENCY_CODE']
        }
    
    # Import models (required for Flask-Migrate to detect them)
    # Why here? Models need app context and db to be initialized first
    with app.app_context():
        from app.models import User, Category, Transaction, BudgetGoal, Project
        
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
    
    ERROR_TEMPLATE = '''
    {% extends "base.html" %}
    {% block content %}
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6 text-center">
                <div class="card border-0 shadow-sm">
                    <div class="card-body py-5">
                        <div style="font-size: 4rem; color: var(--muted-color);">{{ code }}</div>
                        <h2 class="mt-3">{{ title }}</h2>
                        <p class="text-muted mt-2">{{ message }}</p>
                        <a href="{{ url_for('auth.login') }}" class="btn btn-primary mt-3">
                            <i class="bi bi-house"></i> Go Home
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    '''

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {error}')
        return render_template_string(ERROR_TEMPLATE, code=404,
            title='Page Not Found',
            message='The page you are looking for doesn\'t exist or has been moved.'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 error: {error}', exc_info=True)
        db.session.rollback()
        return render_template_string(ERROR_TEMPLATE, code=500,
            title='Server Error',
            message='Something went wrong on our end. Please try again later.'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 error: {error}')
        return render_template_string(ERROR_TEMPLATE, code=403,
            title='Access Forbidden',
            message='You don\'t have permission to access this page.'), 403
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled exception: {error}', exc_info=True)
        db.session.rollback()
        return render_template_string(ERROR_TEMPLATE, code=500,
            title='Unexpected Error',
            message='Something went wrong. Please try again later.'), 500
