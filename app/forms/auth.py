"""
Authentication Forms - Signup and Login.

Why Flask-WTF?
- CSRF Protection: Automatic CSRF token generation and validation
- Validation: Built-in validators (Email, Length, DataRequired)
- Error Messages: User-friendly error messages
- Security: Prevents common web vulnerabilities

Why separate validators?
- Reusability: Custom validators can be used across forms
- Clarity: Validation logic is explicit and testable
- Maintainability: Easy to modify validation rules
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class SignupForm(FlaskForm):
    """
    User registration form.
    
    Fields:
    - username: Unique username (3-80 chars)
    - email: Valid email address
    - password: Secure password (8+ chars)
    - confirm_password: Must match password
    
    Why these validators?
    - DataRequired: Field cannot be empty
    - Length: Prevents too short/long inputs
    - Email: Validates email format
    - EqualTo: Ensures passwords match
    """
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters')
        ],
        render_kw={'placeholder': 'Choose a username', 'class': 'form-control'}
    )
    # Why render_kw?
    # - Adds HTML attributes to the field
    # - 'placeholder' provides user guidance
    # - 'class' applies Bootstrap styling
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={'placeholder': 'your.email@example.com', 'class': 'form-control', 'type': 'email'}
    )
    # Why Email validator?
    # - Validates email format (user@domain.com)
    # - Prevents typos and invalid emails
    # - Uses email-validator library for robust validation
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, message='Password must be at least 8 characters long')
        ],
        render_kw={'placeholder': 'Create a strong password', 'class': 'form-control'}
    )
    # Why minimum 8 characters?
    # - Security best practice
    # - Harder to brute force
    # - OWASP recommendation
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Re-enter your password', 'class': 'form-control'}
    )
    # Why confirm password?
    # - Prevents typos during registration
    # - User experience best practice
    # - Ensures user knows their password
    
    submit = SubmitField(
        'Sign Up',
        render_kw={'class': 'btn btn-primary w-100'}
    )
    
    def validate_username(self, username):
        """
        Custom validator: Check if username already exists.
        
        Why custom validator?
        - Database-level validation
        - Prevents duplicate usernames
        - Provides immediate feedback to user
        
        Naming convention: validate_<field_name>
        - WTForms automatically calls this method
        - Runs after built-in validators pass
        
        Args:
            username: Username field to validate
        
        Raises:
            ValidationError: If username already exists
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username already taken. Please choose a different username.'
            )
    
    def validate_email(self, email):
        """
        Custom validator: Check if email already exists.
        
        Why validate email uniqueness?
        - One account per email address
        - Prevents duplicate accounts
        - Required for password reset functionality
        
        Args:
            email: Email field to validate
        
        Raises:
            ValidationError: If email already registered
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Email already registered. Please use a different email or log in.'
            )


class LoginForm(FlaskForm):
    """
    User login form.
    
    Fields:
    - email: User's registered email
    - password: User's password
    
    Why email instead of username for login?
    - More user-friendly (people remember emails)
    - Enables password reset via email
    - Industry standard practice
    """
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={'placeholder': 'your.email@example.com', 'class': 'form-control', 'type': 'email'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={'placeholder': 'Enter your password', 'class': 'form-control'}
    )
    # Note: No length validation on login
    # Why? User might have old password that doesn't meet new requirements
    # We only validate password format during signup
    
    submit = SubmitField(
        'Log In',
        render_kw={'class': 'btn btn-primary w-100'}
    )
    
    # Note: No custom validators for login
    # Why? We don't want to reveal if email exists (security)
    # Invalid credentials are handled in the route, not the form
    # This prevents user enumeration attacks
