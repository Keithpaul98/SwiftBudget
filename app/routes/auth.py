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

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from app import db, limiter
from app.models.user import User
from app.models.category import Category
from app.forms.auth import SignupForm, LoginForm, ProfileForm
from app.utils.audit import audit_log
from werkzeug.utils import secure_filename
import bleach
import os
import uuid

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
@limiter.limit("5 per minute")  # Prevent signup spam
@limiter.limit("20 per hour")
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
            username=bleach.clean(form.username.data, tags=[], strip=True),
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
            
            # Send welcome email
            try:
                from app.services.email_service import EmailService
                EmailService.send_welcome_email(user.email, user.username)
            except Exception as e:
                current_app.logger.error(f'Failed to send welcome email: {e}')
            
            audit_log('CREATE', 'User', user.id, new_value={'username': user.username, 'email': user.email})
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during signup. Please try again.', 'danger')
            current_app.logger.error(f'Signup failed: {e}', exc_info=True)
    
    # GET request or form validation failed
    return render_template('auth/signup.html', form=form, title='Sign Up')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Prevent brute force attacks
@limiter.limit("20 per hour")
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
        
        # Check if account is locked
        if user and user.locked_until:
            if user.locked_until > datetime.utcnow():
                remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
                flash(f'Account temporarily locked due to multiple failed login attempts. Please try again in {remaining_minutes} minutes.', 'danger')
                return render_template('auth/login.html', form=form, title='Log In')
            else:
                # Lock period expired, reset
                user.locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()
        
        # Verify user exists and password is correct
        if user and user.check_password(form.password.data):
            # Successful login - reset failed attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            
            login_user(user)
            audit_log('LOGIN', 'User', user.id)
            db.session.commit()
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
            # Failed login - increment failed attempts
            if user:
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    db.session.commit()
                    audit_log('LOCKOUT', 'User', user.id, new_value={'failed_attempts': user.failed_login_attempts})
                    db.session.commit()
                    flash('Too many failed login attempts. Your account has been locked for 15 minutes.', 'danger')
                    
                    # TODO: Send email notification about account lockout
                    try:
                        from app.services.email_service import EmailService
                        # EmailService.send_account_lockout_email(user.email, user.username)
                    except Exception as e:
                        current_app.logger.error(f'Failed to send lockout email: {e}')
                else:
                    db.session.commit()
                    remaining_attempts = 5 - user.failed_login_attempts
                    flash(f'Invalid email or password. {remaining_attempts} attempts remaining.', 'danger')
            else:
                # Generic error message (security - don't reveal if email exists)
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
    audit_log('LOGOUT', 'User', current_user.id)
    db.session.commit()
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
    
    Query Parameters:
        range: Time range – '30d' (default), '90d', '6mo', '1yr'
    
    Shows:
    - Spending summary for selected range
    - Trend chart (bar + line) aggregated by day/week/month
    - Category breakdown doughnut
    - Budget progress bars
    - Recent transactions
    """
    from app.services.transaction_service import TransactionService
    from app.services.category_service import CategoryService
    from app.services.budget_service import BudgetService
    from datetime import datetime, timedelta
    from sqlalchemy import func, case, extract
    from sqlalchemy.orm import joinedload
    from app.models.transaction import Transaction
    
    # ── Determine time range ──
    RANGE_OPTIONS = {
        '30d':  {'days': 30,  'label': 'Last 30 Days',   'agg': 'daily'},
        '90d':  {'days': 90,  'label': 'Last 90 Days',   'agg': 'weekly'},
        '6mo':  {'days': 182, 'label': 'Last 6 Months',  'agg': 'monthly'},
        '1yr':  {'days': 365, 'label': 'Last 12 Months', 'agg': 'monthly'},
    }
    selected_range = request.args.get('range', '30d')
    if selected_range not in RANGE_OPTIONS:
        selected_range = '30d'
    
    range_cfg = RANGE_OPTIONS[selected_range]
    today = datetime.now().date()
    range_start = today - timedelta(days=range_cfg['days'])
    
    # ── Summary for selected range ──
    summary = TransactionService.get_spending_summary(
        current_user.id,
        start_date=range_start,
        end_date=today
    )
    
    # ── Yesterday comparison ──
    yesterday = today - timedelta(days=1)
    yesterday_expenses = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False,
        Transaction.transaction_date == yesterday
    ).scalar()
    today_expenses = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False,
        Transaction.transaction_date == today
    ).scalar()
    expense_diff_yesterday = float(today_expenses) - float(yesterday_expenses)
    
    # ── Projected monthly expense ──
    import calendar
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    day_of_month = today.day
    month_start = today.replace(day=1)
    month_expenses_so_far = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False,
        Transaction.transaction_date >= month_start,
        Transaction.transaction_date <= today
    ).scalar()
    month_expenses_so_far = float(month_expenses_so_far)
    projected_monthly_expense = (month_expenses_so_far / max(day_of_month, 1)) * days_in_month
    
    # ── Savings rate ──
    savings_rate = 0.0
    if summary['total_income'] > 0:
        savings_rate = ((summary['total_income'] - summary['total_expenses']) / summary['total_income']) * 100
    
    # ── Budget pacer: % through current month ──
    month_progress_pct = (day_of_month / days_in_month) * 100
    
    # ── Recent transactions (last 10) ──
    recent_transactions = TransactionService.get_user_transactions(
        user_id=current_user.id,
        limit=10
    )
    
    # ── Categories ──
    categories = CategoryService.get_user_categories(current_user.id)
    
    # ── Budget statuses ──
    budget_statuses = BudgetService.get_all_budget_statuses(current_user.id)
    alert_budgets = BudgetService.get_budgets_needing_alerts(current_user.id)
    
    # ── Category spending for doughnut (group <5% into Miscellaneous) ──
    raw_category_spending = db.session.query(
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False,
        Transaction.transaction_date >= range_start
    ).group_by(Category.name).all()
    
    total_cat_spending = sum(float(c.total) for c in raw_category_spending) or 1
    category_spending_names = []
    category_spending_values = []
    misc_total = 0.0
    for cat in raw_category_spending:
        pct = (float(cat.total) / total_cat_spending) * 100
        if pct < 5:
            misc_total += float(cat.total)
        else:
            category_spending_names.append(cat.name)
            category_spending_values.append(float(cat.total))
    if misc_total > 0:
        category_spending_names.append('Miscellaneous')
        category_spending_values.append(misc_total)
    
    # ── Trend data (aggregated differently per range) ──
    agg_mode = range_cfg['agg']
    
    if agg_mode == 'daily':
        # Build contiguous daily labels for smooth area chart
        all_days = []
        d = range_start
        while d <= today:
            all_days.append(d)
            d += timedelta(days=1)
        
        trend_data = db.session.query(
            Transaction.transaction_date.label('period'),
            func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label('expenses'),
            func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label('income')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= range_start,
            Transaction.is_deleted == False
        ).group_by(Transaction.transaction_date).order_by(Transaction.transaction_date).all()
        
        data_map = {r.period: r for r in trend_data}
        trend_labels = [d.strftime('%b %d') for d in all_days]
        trend_expenses = [float(data_map[d].expenses) if d in data_map else 0 for d in all_days]
        trend_income = [float(data_map[d].income) if d in data_map else 0 for d in all_days]
        # Index of today in the array for the "Today" pacer line
        today_index = len(all_days) - 1
        
    elif agg_mode == 'weekly':
        trend_data = db.session.query(
            extract('isoyear', Transaction.transaction_date).label('yr'),
            extract('week', Transaction.transaction_date).label('wk'),
            func.min(Transaction.transaction_date).label('week_start'),
            func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label('expenses'),
            func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label('income')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= range_start,
            Transaction.is_deleted == False
        ).group_by('yr', 'wk').order_by('yr', 'wk').all()
        
        trend_labels = [f"Wk {r.week_start.strftime('%b %d')}" for r in trend_data]
        trend_expenses = [float(r.expenses or 0) for r in trend_data]
        trend_income = [float(r.income or 0) for r in trend_data]
        today_index = len(trend_labels) - 1
        
    else:  # monthly
        trend_data = db.session.query(
            extract('year', Transaction.transaction_date).label('yr'),
            extract('month', Transaction.transaction_date).label('mo'),
            func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label('expenses'),
            func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label('income')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= range_start,
            Transaction.is_deleted == False
        ).group_by('yr', 'mo').order_by('yr', 'mo').all()
        
        trend_labels = [f"{calendar.month_abbr[int(r.mo)]} {int(r.yr)}" for r in trend_data]
        trend_expenses = [float(r.expenses or 0) for r in trend_data]
        trend_income = [float(r.income or 0) for r in trend_data]
        today_index = len(trend_labels) - 1
    
    # ── Projected expense line (extend trend_expenses with projection) ──
    if trend_expenses and day_of_month > 0:
        daily_avg = month_expenses_so_far / day_of_month
        projected_expenses = list(trend_expenses)  # copy actual
        # Fill remaining days with projected values (only for daily view)
        if agg_mode == 'daily':
            remaining = days_in_month - day_of_month
            for i in range(remaining):
                projected_expenses.append(daily_avg)
    else:
        projected_expenses = trend_expenses[:]
    
    return render_template(
        'dashboard/index.html',
        title='Dashboard',
        summary=summary,
        recent_transactions=recent_transactions,
        categories=categories,
        budget_statuses=budget_statuses,
        alert_budgets=alert_budgets,
        category_spending_names=category_spending_names,
        category_spending_values=category_spending_values,
        total_expenses_for_donut=summary['total_expenses'],
        trend_labels=trend_labels,
        trend_expenses=trend_expenses,
        trend_income=trend_income,
        today_index=today_index,
        projected_monthly_expense=projected_monthly_expense,
        month_expenses_so_far=month_expenses_so_far,
        expense_diff_yesterday=expense_diff_yesterday,
        savings_rate=savings_rate,
        month_progress_pct=month_progress_pct,
        days_in_month=days_in_month,
        day_of_month=day_of_month,
        daily_avg_expense=month_expenses_so_far / max(day_of_month, 1),
        selected_range=selected_range,
        range_options=RANGE_OPTIONS
    )


@auth_bp.route('/help')
@login_required
def help_guide():
    """User guide and help page."""
    return render_template('help/index.html', title='Help & Guide')


@auth_bp.route('/profile')
@login_required
def profile():
    """View user profile."""
    return render_template('profile/index.html', title='My Profile')


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile (username, email, password, profile image)."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if username is taken by another user
        if form.username.data != current_user.username:
            existing = User.query.filter_by(username=form.username.data).first()
            if existing:
                flash('Username already taken.', 'danger')
                return render_template('profile/edit.html', form=form, title='Edit Profile')
        
        # Check if email is taken by another user
        if form.email.data != current_user.email:
            existing = User.query.filter_by(email=form.email.data).first()
            if existing:
                flash('Email already registered to another account.', 'danger')
                return render_template('profile/edit.html', form=form, title='Edit Profile')
        
        # Handle password change
        if form.new_password.data:
            if not form.current_password.data:
                flash('Current password is required to set a new password.', 'danger')
                return render_template('profile/edit.html', form=form, title='Edit Profile')
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('profile/edit.html', form=form, title='Edit Profile')
            current_user.set_password(form.new_password.data)
        
        # Handle profile image upload
        if form.profile_image.data:
            file = form.profile_image.data
            if hasattr(file, 'filename') and file.filename:
                if current_app.config.get('CLOUDINARY_CLOUD_NAME'):
                    # Upload to Cloudinary CDN
                    import cloudinary.uploader
                    # Delete old Cloudinary image if exists
                    if current_user.profile_image and current_user.profile_image.startswith('http'):
                        old_public_id = f"swiftbudget/profiles/{current_user.id}"
                        try:
                            cloudinary.uploader.destroy(old_public_id)
                        except Exception:
                            pass
                    result = cloudinary.uploader.upload(
                        file,
                        folder='swiftbudget/profiles',
                        public_id=str(current_user.id),
                        overwrite=True,
                        transformation=[
                            {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}
                        ]
                    )
                    current_user.profile_image = result['secure_url']
                else:
                    # Local fallback when Cloudinary is not configured
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
                    unique_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
                    
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Delete old local image if exists
                    if current_user.profile_image and not current_user.profile_image.startswith('http'):
                        old_path = os.path.join(upload_dir, current_user.profile_image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    file.save(os.path.join(upload_dir, unique_name))
                    current_user.profile_image = unique_name
        
        # Update basic fields
        current_user.username = bleach.clean(form.username.data.strip())
        current_user.email = form.email.data.strip().lower()
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile/edit.html', form=form, title='Edit Profile')


@auth_bp.route('/profile/remove-image', methods=['POST'])
@login_required
def remove_profile_image():
    """Remove the user's profile image."""
    if current_user.profile_image:
        if current_user.profile_image.startswith('http') and current_app.config.get('CLOUDINARY_CLOUD_NAME'):
            # Delete from Cloudinary
            import cloudinary.uploader
            try:
                cloudinary.uploader.destroy(f"swiftbudget/profiles/{current_user.id}")
            except Exception:
                pass
        elif not current_user.profile_image.startswith('http'):
            # Delete local file
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
            old_path = os.path.join(upload_dir, current_user.profile_image)
            if os.path.exists(old_path):
                os.remove(old_path)
        current_user.profile_image = None
        db.session.commit()
        flash('Profile image removed.', 'success')
    return redirect(url_for('auth.edit_profile'))
