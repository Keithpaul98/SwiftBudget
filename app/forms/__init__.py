"""
Forms package.

Why separate forms?
- Organization: Each form type in its own file
- Reusability: Forms can be imported across routes
- Validation: Centralized form validation logic
"""

# Import forms here for easy access
from app.forms.auth import SignupForm, LoginForm

# Future forms (Module 5+)
# from app.forms.transaction import TransactionForm
# from app.forms.budget import BudgetGoalForm
