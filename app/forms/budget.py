"""
Budget Goal Forms - Create and Edit Budget Goals.

Why separate budget forms?
- Different validation for budget periods
- Alert threshold percentage validation
- Category selection from user's categories
- Amount validation (positive numbers)
"""

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional


class BudgetGoalForm(FlaskForm):
    """
    Form for creating/editing budget goals.
    
    Fields:
    - category_id: Category to budget for
    - amount: Budget limit amount
    - period: Budget period (monthly, weekly, yearly)
    - alert_threshold: Alert at X% of budget (0-100)
    - is_active: Whether budget is active
    """
    
    category_id = SelectField(
        'Category',
        validators=[DataRequired(message='Category is required')],
        coerce=int,
        render_kw={'class': 'form-select'}
    )
    # Why SelectField?
    # - Dropdown of user's categories
    # - One budget per category
    # - Prevents invalid category selection
    
    amount = DecimalField(
        'Budget Amount',
        validators=[
            DataRequired(message='Budget amount is required'),
            NumberRange(min=0.01, message='Budget amount must be greater than 0')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        }
    )
    # Why DecimalField?
    # - Precise decimal arithmetic
    # - Financial data requires exact values
    # - Database stores as NUMERIC(10,2)
    
    period = SelectField(
        'Budget Period',
        validators=[DataRequired(message='Budget period is required')],
        choices=[
            ('monthly', 'Monthly'),
            ('weekly', 'Weekly'),
            ('yearly', 'Yearly')
        ],
        render_kw={'class': 'form-select'}
    )
    # Why fixed choices?
    # - Only three valid periods
    # - Database CHECK constraint enforces this
    # - User-friendly labels
    
    alert_threshold = IntegerField(
        'Alert Threshold (%)',
        validators=[
            DataRequired(message='Alert threshold is required'),
            NumberRange(min=0, max=100, message='Alert threshold must be between 0 and 100')
        ],
        default=80,
        render_kw={
            'placeholder': '80',
            'class': 'form-control',
            'min': '0',
            'max': '100'
        }
    )
    # Why alert threshold?
    # - Warn user before going over budget
    # - Default 80% (common practice)
    # - Percentage makes it flexible for any budget amount
    
    is_active = BooleanField(
        'Active',
        default=True,
        render_kw={'class': 'form-check-input'}
    )
    # Why is_active?
    # - Temporarily disable budget without deleting
    # - Seasonal budgets (enable/disable as needed)
    # - Keep historical data
    
    submit = SubmitField(
        'Save Budget Goal',
        render_kw={'class': 'btn btn-primary'}
    )
