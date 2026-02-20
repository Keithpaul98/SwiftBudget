"""
Authentication Routes - Signup, Login, Logout.

Why Blueprint?
- Modular organization: Auth routes grouped together
- URL prefix: All auth routes under /auth
- Reusability: Blueprint can be registered in multiple apps
- Separation of concerns: Auth logic separate from other features

Security Considerations:
- CSRF protection via Flask-WTF
- Password hashing via bcrypt
- Session management via Flask-Login
- Flash messages for user feedback
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.category import Category
from app.forms.auth import SignupForm, LoginForm

# Create blueprint
auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)
# Why url_prefix='/auth'?
# - All routes in this blueprint will be prefixed with /auth
# - Example: /auth/signup, /auth/login, /auth/logout
# - Keeps URLs organized and RESTful


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User registration route.
    
    GET: Display signup form
    POST: Process signup form and create user
    
    Why check if user is authenticated?
    - Logged-in users shouldn't access signup page
    - Redirect to dashboard if already logged in
    - Better user experience
    
    Returns:
        GET: Rendered signup template
        POST: Redirect to login page on success, or re-render form with errors
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('auth.dashboard'))
    
    form = SignupForm()
    
    if form.validate_on_submit():
        # Why validate_on_submit()?
        # - Checks if request is POST
        # - Validates all form fields
        # - Checks CSRF token
        # - Returns True only if all validations pass
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data.lower()  # Store email in lowercase
        )
        # Why lowercase email?
        # - Prevents duplicate accounts (User@example.com vs user@example.com)
        # - Case-insensitive login
        # - Database query optimization
        
        user.set_password(form.password.data)
        # Why set_password() method?
        # - Encapsulates bcrypt hashing logic
        # - Never stores plain text password
        # - Consistent hashing across application
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create default categories for new user
            Category.create_default_categories_for_user(user.id)
            # Why create default categories?
            # - Better onboarding experience
            # - User can start tracking immediately
            # - Common categories (Food, Rent, etc.) pre-populated
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during signup. Please try again.', 'danger')
            # Log the error for debugging
            print(f"Signup error: {e}")
    
    # GET request or form validation failed
    return render_template('auth/signup.html', form=form, title='Sign Up')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    
    GET: Display login form
    POST: Authenticate user and create session
    
    Security:
    - Constant-time password comparison (bcrypt)
    - Generic error message (prevents user enumeration)
    - Session management via Flask-Login
    
    Returns:
        GET: Rendered login template
        POST: Redirect to dashboard on success, or re-render form with errors
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by email (case-insensitive)
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # Verify user exists and password is correct
        if user and user.check_password(form.password.data):
            # Why check both user and password?
            # - user is None if email not found
            # - check_password() returns False if password wrong
            # - Both conditions must be True to log in
            
            login_user(user)
            # What does login_user() do?
            # - Creates session for user
            # - Sets current_user to this user
            # - Manages session cookie
            # - Handled by Flask-Login
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            # Why check 'next' parameter?
            # - User might have tried to access protected page
            # - Flask-Login stores original URL in 'next'
            # - Redirect user to where they wanted to go
            
            if next_page:
                # Security: Validate next_page to prevent open redirect
                # Only allow relative URLs (no external redirects)
                from urllib.parse import urlparse
                if urlparse(next_page).netloc == '':
                    return redirect(next_page)
            
            return redirect(url_for('auth.dashboard'))
        
        else:
            # Generic error message (security)
            flash('Invalid email or password. Please try again.', 'danger')
            # Why generic message?
            # - Prevents user enumeration attack
            # - Attacker can't determine if email exists
            # - Security best practice
    
    return render_template('auth/login.html', form=form, title='Log In')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route.
    
    Why @login_required?
    - Only logged-in users can log out
    - Prevents errors if unauthenticated user accesses route
    - Flask-Login decorator handles redirect
    
    Returns:
        Redirect to login page
    """
    logout_user()
    # What does logout_user() do?
    # - Removes user from session
    # - Clears session cookie
    # - Sets current_user to anonymous
    # - Handled by Flask-Login
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard with spending overview.
    
    Shows:
    - Current month spending summary
    - Recent transactions
    - Budget status (Module 6)
    
    Returns:
        Rendered dashboard template
    """
    from app.services.transaction_service import TransactionService
    from app.services.category_service import CategoryService
    from app.services.budget_service import BudgetService
    
    # Get current month summary
    summary = TransactionService.get_spending_summary(current_user.id)
    
    # Get recent transactions (last 10)
    recent_transactions = TransactionService.get_user_transactions(
        user_id=current_user.id,
        limit=10
    )
    
    # Get user categories
    categories = CategoryService.get_user_categories(current_user.id)
    
    # Get budget statuses
    budget_statuses = BudgetService.get_all_budget_statuses(current_user.id)
    alert_budgets = BudgetService.get_budgets_needing_alerts(current_user.id)
    
    return render_template(
        'dashboard/index.html',
        title='Dashboard',
        summary=summary,
        recent_transactions=recent_transactions,
        categories=categories,
        budget_statuses=budget_statuses,
        alert_budgets=alert_budgets
    )
