"""
Application entry point.

Why separate run.py from app/__init__.py?
1. Clean Separation: Application factory (create_app) separate from execution
2. Flexibility: Can import app in other scripts without running server
3. Testing: Tests can create app instances without starting server
4. Production: Gunicorn uses app:app pattern (imports from app/__init__.py)

Usage:
    Development: python run.py
    Production: gunicorn -w 4 -b 0.0.0.0:10000 run:app
"""

import os
from app import create_app

# Create application instance
# Uses FLASK_ENV environment variable to determine config
# Defaults to 'development' if not set
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    """
    Run development server.
    
    Why check __name__ == '__main__'?
    - Only runs when script is executed directly (python run.py)
    - Doesn't run when imported (e.g., by Gunicorn or tests)
    
    Development server settings:
    - host='0.0.0.0': Accept connections from any IP (useful for testing on network)
    - port=5000: Default Flask port
    - debug: Controlled by config (True in development, False in production)
    """
    
    # Get port from environment variable (useful for cloud platforms)
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
