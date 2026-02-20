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

# Future forms (Module 6+)
# from app.forms.budget import BudgetGoalForm
