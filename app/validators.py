"""
Custom validators for SwiftBudget application.

Why separate validators?
- Reusability: Validators can be used across multiple forms
- Security: Centralized validation logic
- Maintainability: Easy to update validation rules
- Testing: Validators can be unit tested independently
"""

from decimal import Decimal, InvalidOperation
from wtforms.validators import ValidationError


class DecimalRange:
    """
    Validator for decimal fields with min/max constraints.
    
    Prevents:
    - Overflow attacks (extremely large numbers)
    - Precision attacks (too many decimal places)
    - Negative amounts (when not allowed)
    
    Usage:
        amount = DecimalField(
            validators=[DecimalRange(min=0.01, max=9999999.99, precision=2)]
        )
    """
    
    def __init__(self, min=None, max=None, precision=2, message=None):
        """
        Initialize decimal range validator.
        
        Args:
            min (Decimal): Minimum allowed value (inclusive)
            max (Decimal): Maximum allowed value (inclusive)
            precision (int): Maximum decimal places allowed
            message (str): Custom error message
        """
        self.min = Decimal(str(min)) if min is not None else None
        self.max = Decimal(str(max)) if max is not None else None
        self.precision = precision
        self.message = message
    
    def __call__(self, form, field):
        """
        Validate the decimal field.
        
        Args:
            form: The form containing the field
            field: The field to validate
        
        Raises:
            ValidationError: If validation fails
        """
        if field.data is None:
            return
        
        try:
            value = Decimal(str(field.data))
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError('Invalid number format')
        
        # Check minimum value
        if self.min is not None and value < self.min:
            message = self.message or f'Amount must be at least {self.min}'
            raise ValidationError(message)
        
        # Check maximum value
        if self.max is not None and value > self.max:
            message = self.message or f'Amount cannot exceed {self.max}'
            raise ValidationError(message)
        
        # Check decimal precision
        if self.precision is not None:
            # Get the exponent (negative for decimal places)
            exponent = value.as_tuple().exponent
            if exponent < -self.precision:
                raise ValidationError(
                    f'Amount cannot have more than {self.precision} decimal places'
                )


class PositiveDecimal:
    """
    Validator to ensure decimal is positive (greater than zero).
    
    Usage:
        amount = DecimalField(validators=[PositiveDecimal()])
    """
    
    def __init__(self, message=None):
        self.message = message or 'Amount must be greater than zero'
    
    def __call__(self, form, field):
        if field.data is None:
            return
        
        try:
            value = Decimal(str(field.data))
            if value <= 0:
                raise ValidationError(self.message)
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError('Invalid number format')


class SafeString:
    """
    Validator to prevent XSS attacks in string fields.
    
    Checks for:
    - HTML tags
    - JavaScript
    - SQL injection patterns
    
    Usage:
        description = StringField(validators=[SafeString()])
    """
    
    def __init__(self, message=None):
        self.message = message or 'Invalid characters detected'
        # Dangerous patterns to check for
        self.dangerous_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onclick=',
            'onload=',
            '<iframe',
            '<object',
            '<embed',
        ]
    
    def __call__(self, form, field):
        if field.data is None:
            return
        
        value = str(field.data).lower()
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern in value:
                raise ValidationError(
                    'Input contains potentially dangerous content'
                )
