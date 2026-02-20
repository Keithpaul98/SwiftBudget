"""
Transaction Forms - Create and Edit Transactions.

Why separate transaction forms?
- Different validation for income vs expense
- Date picker integration
- Category selection from user's categories
- Amount validation (positive numbers)
"""

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from datetime import date


class TransactionForm(FlaskForm):
    """
    Form for creating/editing transactions.
    
    Fields:
    - amount: Transaction amount (positive)
    - category_id: Category selection
    - transaction_type: Income or Expense
    - transaction_date: Date of transaction
    - description: Optional description
    """
    
    amount = DecimalField(
        'Total Amount',
        validators=[
            DataRequired(message='Amount is required'),
            NumberRange(min=0.01, message='Amount must be greater than 0')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'id': 'amount'
        }
    )
    # Why DecimalField?
    # - Precise decimal arithmetic (no floating point errors)
    # - Financial data requires exact values
    # - Database stores as NUMERIC(10,2)
    
    quantity = DecimalField(
        'Quantity',
        validators=[Optional(), NumberRange(min=1, message='Quantity must be at least 1')],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-control',
            'step': '1',
            'min': '1',
            'id': 'quantity'
        }
    )
    # Why quantity?
    # - Track number of items (e.g., "5 apples")
    # - Optional: defaults to 1
    # - Auto-calculates total when used with unit_price
    
    unit_price = DecimalField(
        'Unit Price',
        validators=[Optional(), NumberRange(min=0.01, message='Unit price must be greater than 0')],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'id': 'unit_price'
        }
    )
    # Why unit_price?
    # - Track price per item (e.g., "$2.00 per apple")
    # - Optional: if provided, amount = quantity * unit_price
    # - Helps with detailed expense tracking
    
    category_id = SelectField(
        'Category',
        validators=[DataRequired(message='Category is required')],
        coerce=int,
        render_kw={'class': 'form-select'}
    )
    # Why SelectField?
    # - Dropdown of user's categories
    # - Prevents invalid category selection
    # - coerce=int converts string to integer
    # - choices will be populated dynamically in route
    
    transaction_type = SelectField(
        'Type',
        validators=[DataRequired(message='Transaction type is required')],
        choices=[
            ('expense', 'Expense'),
            ('income', 'Income')
        ],
        render_kw={'class': 'form-select'}
    )
    # Why fixed choices?
    # - Only two valid types: income or expense
    # - Database CHECK constraint enforces this
    # - User-friendly labels
    
    transaction_date = DateField(
        'Date',
        validators=[DataRequired(message='Date is required')],
        default=date.today,
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    # Why DateField?
    # - HTML5 date picker
    # - Automatic validation
    # - Defaults to today
    # - Prevents future dates (can add validator)
    
    description = StringField(
        'Description',
        validators=[Optional(), Length(max=200, message='Description must be 200 characters or less')],
        render_kw={
            'placeholder': 'Optional: Add a note about this transaction',
            'class': 'form-control'
        }
    )
    # Why optional?
    # - Not all transactions need descriptions
    # - Amount and category are often self-explanatory
    
    project_id = SelectField(
        'Project',
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={'class': 'form-select'}
    )
    # Why project_id?
    # - Optional: not all transactions belong to projects
    # - Groups related transactions (e.g., "Parents Shopping")
    # - Helps with reporting and organization
    
    submit = SubmitField(
        'Save Transaction',
        render_kw={'class': 'btn btn-primary'}
    )
    
    def validate_transaction_date(self, transaction_date):
        """
        Custom validator: Prevent future dates.
        
        Why prevent future dates?
        - Transactions are historical records
        - Future transactions are budgets/plans (different feature)
        - Prevents user confusion
        
        Args:
            transaction_date: Date field to validate
        
        Raises:
            ValidationError: If date is in the future
        """
        from wtforms.validators import ValidationError
        
        if transaction_date.data and transaction_date.data > date.today():
            raise ValidationError('Transaction date cannot be in the future')


class TransactionFilterForm(FlaskForm):
    """
    Form for filtering transactions.
    
    Why separate filter form?
    - Different validation (all fields optional)
    - No submit button needed (auto-filter on change)
    - Cleaner separation of concerns
    """
    
    category_id = SelectField(
        'Category',
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )
    # No coerce=int because we allow empty string for "All Categories"
    
    transaction_type = SelectField(
        'Type',
        validators=[Optional()],
        choices=[
            ('', 'All Types'),
            ('expense', 'Expenses'),
            ('income', 'Income')
        ],
        render_kw={'class': 'form-select'}
    )
    
    start_date = DateField(
        'From',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    
    end_date = DateField(
        'To',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    
    submit = SubmitField(
        'Filter',
        render_kw={'class': 'btn btn-secondary'}
    )
