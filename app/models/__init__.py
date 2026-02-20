"""
Models package.

Why separate models into a package?
- Organization: Each model in its own file (user.py, transaction.py, etc.)
- Scalability: Easy to add new models without cluttering a single file
- Imports: Centralized model imports for easy access
"""

# Import models here for easy access
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget_goal import BudgetGoal
from app.models.project import Project
