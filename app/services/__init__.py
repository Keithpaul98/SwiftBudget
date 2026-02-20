"""
Services package.

Why Service Layer?
- Separation of Concerns: Business logic separate from routes
- Reusability: Services can be used across multiple routes
- Testability: Easy to unit test business logic
- Maintainability: Easier to modify logic without touching routes
- Framework Independence: Can switch frameworks without rewriting business logic
"""

# Import services
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.budget_service import BudgetService
from app.services.project_service import ProjectService
