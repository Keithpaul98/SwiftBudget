"""
Forms package.

Why separate forms?
- Organization: Each form type in its own file
- Reusability: Forms can be imported across routes
- Validation: Centralized form validation logic
"""

# Import forms here for easy access
from app.forms.auth import SignupForm, LoginForm
from app.forms.transaction import TransactionForm, TransactionFilterForm
from app.forms.budget import BudgetGoalForm
from app.forms.project import ProjectForm
