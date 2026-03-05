"""
Recurring Transaction Form - Create and manage recurring transactions.
"""

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, DateField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, Length
from datetime import date
from app.validators import DecimalRange, SafeString


class RecurringTransactionForm(FlaskForm):
    """Form for creating/editing recurring transactions."""
    
    amount = DecimalField(
        'Amount',
        validators=[
            DataRequired(message='Amount is required'),
            DecimalRange(min=0.01, max=9999999.99, precision=2)
        ],
        render_kw={'placeholder': '0.00', 'class': 'form-control', 'step': '0.01', 'min': '0.01'}
    )
    
    transaction_type = SelectField(
        'Type',
        validators=[DataRequired()],
        choices=[('expense', 'Expense'), ('income', 'Income')],
        render_kw={'class': 'form-select'}
    )
    
    category_id = SelectField(
        'Category',
        validators=[DataRequired(message='Category is required')],
        coerce=int,
        render_kw={'class': 'form-select'}
    )
    
    project_id = SelectField(
        'Project',
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={'class': 'form-select'}
    )
    
    frequency = SelectField(
        'Frequency',
        validators=[DataRequired()],
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly')
        ],
        render_kw={'class': 'form-select'}
    )
    
    start_date = DateField(
        'Start Date',
        validators=[DataRequired(message='Start date is required')],
        default=date.today,
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    
    end_date = DateField(
        'End Date (optional)',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    
    description = StringField(
        'Description',
        validators=[Optional(), Length(max=200), SafeString()],
        render_kw={'placeholder': 'e.g. Monthly rent, Weekly groceries', 'class': 'form-control'}
    )
    
    is_active = BooleanField('Active', default=True)
    
    submit = SubmitField('Save Recurring Transaction', render_kw={'class': 'btn btn-primary'})
