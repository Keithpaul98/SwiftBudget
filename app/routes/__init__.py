"""
Routes package.

Why separate routes into blueprints?
- Organization: Each feature has its own blueprint
- Scalability: Easy to add new features without cluttering a single file
- URL Prefixes: Group related routes under a common prefix
- Modularity: Blueprints can be registered/unregistered easily
"""

# Import blueprints
from app.routes.auth import auth_bp

# Future blueprints (Module 5+)
# from app.routes.dashboard import dashboard_bp
# from app.routes.transactions import transactions_bp
