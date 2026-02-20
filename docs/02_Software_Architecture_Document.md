# SwiftBudget - Software Architecture Document (SAD)

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Framework:** Flask (Python)  
**Architecture Pattern:** Model-View-Controller (MVC) with Service Layer

---

## 1. Architecture Overview

SwiftBudget follows a **layered MVC architecture** with an additional **Service Layer** to encapsulate business logic. This design ensures:

1. **Separation of Concerns**: Database, business logic, and presentation are isolated
2. **Testability**: Each layer can be unit tested independently
3. **Framework Portability**: Service layer enables future Flask → Django migration
4. **Maintainability**: Clear boundaries reduce code coupling

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│  (Web Browser - Chrome, Firefox, Safari, Edge)              │
│         HTML5 │ CSS3 (Bootstrap 5) │ JavaScript              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                    (Flask + Jinja2)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │   Templates  │  │    Forms     │      │
│  │ (Controller) │  │    (View)    │  │ (Flask-WTF)  │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
└─────────┼──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                            │
│              (Business Logic & Validation)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ UserService  │  │TransactionSvc│  │ BudgetService│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                       │
│                   (SQLAlchemy ORM Models)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  User Model  │  │Transaction   │  │ Category     │      │
│  │              │  │    Model     │  │   Model      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER                           │
│              PostgreSQL 14+ (Supabase/ElephantSQL)          │
│                    ACID Compliant Storage                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SMTP Server  │  │  PayJungle   │  │   Logging    │      │
│  │ (Flask-Mail) │  │ (Future API) │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Layers

### 2.1 Presentation Layer (View + Controller)

**Responsibilities:**
- Handle HTTP requests/responses
- Render HTML templates with Jinja2
- Validate form inputs (client-side + server-side)
- Manage user sessions and authentication

**Components:**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Routes** | Flask Blueprints | URL routing and request handling |
| **Templates** | Jinja2 | Dynamic HTML generation |
| **Forms** | Flask-WTF | Form rendering and CSRF protection |
| **Static Assets** | Bootstrap 5, CSS, JS | Frontend styling and interactivity |

**Example Route Structure:**
```
app/
├── routes/
│   ├── __init__.py
│   ├── auth.py          # /login, /signup, /logout
│   ├── dashboard.py     # /dashboard
│   ├── transactions.py  # /transactions/add, /transactions/edit/<id>
│   └── budget.py        # /budget/goals
```

**Key Design Decisions:**
- **Blueprints**: Modular route organization (auth, transactions, budget)
- **Template Inheritance**: Base template with blocks for DRY principles
- **Flash Messages**: User feedback for success/error states
- **AJAX Support**: Optional for real-time balance updates

---

### 2.2 Service Layer (Business Logic)

**Responsibilities:**
- Encapsulate all business rules and calculations
- Validate data before database operations
- Coordinate between multiple models
- Provide framework-agnostic interfaces

**Why a Service Layer?**
> When migrating from Flask to Django, you only need to rewrite the routes and models. The service layer (pure Python functions) remains unchanged, saving 40-60% of refactoring effort.

**Service Classes:**

#### **UserService**
```python
# Pseudo-code example
class UserService:
    @staticmethod
    def register_user(username, email, password):
        # 1. Validate email format
        # 2. Check if username/email already exists
        # 3. Hash password with bcrypt
        # 4. Create User model instance
        # 5. Save to database
        # 6. Send welcome email (optional)
        return user_object
    
    @staticmethod
    def authenticate(username, password):
        # 1. Query user by username
        # 2. Compare hashed passwords
        # 3. Return user object or None
```

#### **TransactionService**
```python
class TransactionService:
    @staticmethod
    def add_transaction(user_id, amount, description, date, category_id):
        # 1. Validate amount (must be numeric, > 0)
        # 2. Validate date (not in future)
        # 3. Check category belongs to user
        # 4. Create Transaction model
        # 5. Update user's cached balance (optional)
        return transaction_object
    
    @staticmethod
    def calculate_balance(user_id, start_date=None, end_date=None):
        # 1. Query all transactions for user
        # 2. Filter by date range if provided
        # 3. Sum income - expenses
        return balance_decimal
    
    @staticmethod
    def get_category_breakdown(user_id, month, year):
        # 1. Query transactions for specific month
        # 2. Group by category
        # 3. Calculate totals
        return {category_name: total_amount}
```

#### **BudgetService**
```python
class BudgetService:
    @staticmethod
    def set_budget_goal(user_id, category_id, amount, period='monthly'):
        # 1. Validate amount > 0
        # 2. Create or update BudgetGoal model
        return budget_goal_object
    
    @staticmethod
    def check_budget_alerts(user_id):
        # 1. Get all budget goals for user
        # 2. Calculate current spending per category
        # 3. Compare against goals
        # 4. Return list of categories exceeding 80%
        return alert_list
```

**Benefits:**
- **Reusability**: Services can be called from routes, CLI scripts, or background jobs
- **Testing**: Mock database layer, test business logic in isolation
- **Migration**: Swap Flask routes for Django views without touching services

---

### 2.3 Data Access Layer (Models)

**Responsibilities:**
- Define database schema via SQLAlchemy ORM
- Handle CRUD operations
- Enforce data integrity constraints
- Manage relationships between entities

**ORM Models:**

#### **User Model**
```python
class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship('Transaction', backref='user', lazy=True)
    categories = relationship('Category', backref='user', lazy=True)
    budget_goals = relationship('BudgetGoal', backref='user', lazy=True)
```

#### **Category Model**
```python
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_default = Column(Boolean, default=False)  # System vs. user-created
    
    # Relationships
    transactions = relationship('Transaction', backref='category', lazy=True)
```

#### **Transaction Model**
```python
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10, 2), nullable=False)  # Precision for currency
    description = Column(String(200))
    date = Column(Date, nullable=False)
    type = Column(Enum('income', 'expense'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### **BudgetGoal Model** (Should Have)
```python
class BudgetGoal(db.Model):
    __tablename__ = 'budget_goals'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    period = Column(String(20), default='monthly')  # monthly, weekly, yearly
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Design Decisions:**
- **Numeric Type**: Use `Numeric(10, 2)` instead of `Float` to avoid rounding errors (critical for financial data)
- **Soft Deletes**: Add `is_deleted` column instead of hard deletes (audit trail)
- **Indexes**: Add indexes on `user_id`, `date`, `category_id` for query performance
- **Constraints**: Enforce `amount > 0` at database level

---

### 2.4 Database Layer

**Technology:** PostgreSQL 14+ (hosted on Supabase or ElephantSQL)

**Why PostgreSQL over NoSQL?**

| Requirement | PostgreSQL | MongoDB (NoSQL) |
|-------------|-----------|-----------------|
| **ACID Compliance** | ✅ Full support | ⚠️ Limited (eventual consistency) |
| **Transactions** | ✅ Native support | ⚠️ Complex for multi-document |
| **Data Integrity** | ✅ Foreign keys, constraints | ❌ Application-level only |
| **Query Complexity** | ✅ JOINs, aggregations | ⚠️ Requires denormalization |
| **Financial Data** | ✅ `NUMERIC` type (exact) | ❌ `Double` (floating-point errors) |
| **Free Tier** | ✅ Supabase 500MB | ✅ MongoDB Atlas 512MB |

**Verdict:** PostgreSQL is superior for financial applications where data accuracy is non-negotiable.

**Schema Design Principles:**
- **Normalization**: 3rd Normal Form (3NF) to eliminate redundancy
- **Referential Integrity**: Foreign keys with `ON DELETE CASCADE`
- **Indexing Strategy**: Composite indexes on `(user_id, date)` for transaction queries
- **Partitioning**: (Future) Partition transactions table by year for scalability

---

## 3. Design Patterns

### 3.1 MVC Pattern

**Model:**
- SQLAlchemy ORM classes
- Represent database tables
- No business logic (only data validation)

**View:**
- Jinja2 templates
- Pure presentation logic
- No database queries

**Controller:**
- Flask routes/blueprints
- Orchestrate requests
- Call service layer methods

**Flow Example: Adding a Transaction**
```
1. User submits form → POST /transactions/add
2. Controller (routes/transactions.py) receives request
3. Controller validates form with Flask-WTF
4. Controller calls TransactionService.add_transaction()
5. Service validates business rules (amount > 0, date valid)
6. Service creates Transaction model and saves to DB
7. Service returns success/error to Controller
8. Controller flashes message and redirects to dashboard
9. View (dashboard.html) renders updated balance
```

### 3.2 Repository Pattern (Optional for v2.0)

For advanced abstraction, introduce repositories:
```python
class TransactionRepository:
    @staticmethod
    def get_by_user(user_id):
        return Transaction.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_by_date_range(user_id, start, end):
        return Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date.between(start, end)
        ).all()
```

**Benefit:** Swap SQLAlchemy for raw SQL or another ORM without changing services.

### 3.3 Factory Pattern (Configuration)

```python
# config.py
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

# app/__init__.py
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])
    return app
```

---

## 4. Component Interaction Diagrams

### 4.1 Sequence Diagram: User Authentication

```
┌──────┐          ┌──────────┐       ┌─────────┐       ┌──────────┐
│Client│          │Flask Route│      │UserService│     │Database │
└──┬───┘          └────┬─────┘       └────┬────┘       └────┬─────┘
   │                   │                  │                 │
   │ POST /login       │                  │                 │
   │ (username, pwd)   │                  │                 │
   ├──────────────────>│                  │                 │
   │                   │                  │                 │
   │                   │ authenticate()   │                 │
   │                   ├─────────────────>│                 │
   │                   │                  │                 │
   │                   │                  │ SELECT * FROM   │
   │                   │                  │ users WHERE...  │
   │                   │                  ├────────────────>│
   │                   │                  │                 │
   │                   │                  │ User object     │
   │                   │                  │<────────────────┤
   │                   │                  │                 │
   │                   │  bcrypt.check()  │                 │
   │                   │  (password hash) │                 │
   │                   │                  │                 │
   │                   │ User object      │                 │
   │                   │<─────────────────┤                 │
   │                   │                  │                 │
   │  Set session      │                  │                 │
   │  cookie, redirect │                  │                 │
   │<──────────────────┤                  │                 │
   │                   │                  │                 │
```

### 4.2 Activity Diagram: Adding a Transaction

```
                    ┌─────────────────┐
                    │  User clicks    │
                    │ "Add Transaction"│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Fill form:      │
                    │ - Amount        │
                    │ - Description   │
                    │ - Date          │
                    │ - Category      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Submit form     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Flask-WTF       │
                    │ validates form  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                 Valid?            Invalid
                    │                 │
                    ▼                 ▼
          ┌─────────────────┐  ┌─────────────────┐
          │ Call Transaction│  │ Flash error     │
          │ Service.add()   │  │ Re-render form  │
          └────────┬────────┘  └─────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Validate amount │
          │ (must be > 0)   │
          └────────┬────────┘
                   │
          ┌────────┴────────┐
          │                 │
       Valid?            Invalid
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│ Create Transaction│ │ Return error   │
│ model           │  │ to controller   │
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Save to database│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Flash success   │
│ "Transaction    │
│ added!"         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Redirect to     │
│ dashboard       │
└─────────────────┘
```

### 4.3 Component Diagram: Email Notification System

```
┌─────────────────────────────────────────────────────────┐
│              Background Job (Optional)                   │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │  Scheduled Task (Cron or APScheduler)    │           │
│  │  - Daily at 8 AM: Send budget alerts     │           │
│  │  - Weekly: Send spending summary         │           │
│  └────────────────┬─────────────────────────┘           │
│                   │                                      │
│                   ▼                                      │
│  ┌──────────────────────────────────────────┐           │
│  │         BudgetService.check_alerts()     │           │
│  │  - Query users with budget goals         │           │
│  │  - Calculate current spending            │           │
│  │  - Identify users exceeding 80%          │           │
│  └────────────────┬─────────────────────────┘           │
│                   │                                      │
│                   ▼                                      │
│  ┌──────────────────────────────────────────┐           │
│  │         EmailService.send_alert()        │           │
│  │  - Render email template (Jinja2)        │           │
│  │  - Use Flask-Mail to send via SMTP       │           │
│  └────────────────┬─────────────────────────┘           │
└───────────────────┼─────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  SMTP Server     │
          │  (Gmail/SendGrid)│
          └──────────────────┘
```

---

## 5. Technology Stack

### 5.1 Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.9+ | Core language |
| **Web Framework** | Flask | 2.3+ | HTTP handling, routing |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Database** | PostgreSQL | 14+ | Data persistence |
| **Migration Tool** | Flask-Migrate (Alembic) | 4.0+ | Schema versioning |
| **Forms** | Flask-WTF | 1.1+ | Form validation, CSRF |
| **Authentication** | Flask-Login | 0.6+ | Session management |
| **Password Hashing** | Bcrypt | 4.0+ | Secure password storage |
| **Email** | Flask-Mail | 0.9+ | SMTP integration |
| **Environment** | python-dotenv | 1.0+ | Config management |

### 5.2 Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Template Engine** | Jinja2 | 3.1+ | Server-side rendering |
| **CSS Framework** | Bootstrap | 5.3+ | Responsive design |
| **Icons** | Bootstrap Icons | 1.10+ | UI icons |
| **JavaScript** | Vanilla JS | ES6+ | Form validation, AJAX |
| **Charts** | Chart.js | 4.0+ (Could Have) | Data visualization |

### 5.3 Infrastructure

| Component | Service | Tier | Purpose |
|-----------|---------|------|---------|
| **Hosting** | Render.com | Free (512MB RAM) | Application server |
| **Database** | Supabase | Free (500MB) | PostgreSQL hosting |
| **Email** | Gmail SMTP | Free (500/day) | Transactional emails |
| **Version Control** | GitHub | Free | Code repository |
| **CI/CD** | Render Auto-Deploy | Free | Continuous deployment |

---

## 6. Security Architecture

### 6.1 Authentication Flow

```
1. User submits login form
2. Flask-WTF validates CSRF token
3. UserService queries database for username
4. Bcrypt compares submitted password with stored hash
5. If match: Flask-Login creates session
6. Session cookie (HTTP-only, Secure flag) sent to client
7. Subsequent requests include session cookie
8. Flask-Login validates session on each request
```

### 6.2 Authorization

**Role-Based Access Control (RBAC) - Future:**
- Currently: All users have equal permissions (own data only)
- Future: Admin role for managing default categories

**Data Isolation:**
- All queries filtered by `user_id` (e.g., `Transaction.query.filter_by(user_id=current_user.id)`)
- SQLAlchemy prevents SQL injection via parameterized queries

### 6.3 Security Layers

| Layer | Protection Mechanism |
|-------|---------------------|
| **Transport** | HTTPS/TLS 1.3 (enforced in production) |
| **Session** | Secure, HTTP-only cookies with 24-hour expiration |
| **CSRF** | Flask-WTF tokens on all POST/PUT/DELETE forms |
| **XSS** | Jinja2 auto-escaping (e.g., `{{ user_input }}` sanitized) |
| **SQL Injection** | SQLAlchemy ORM (no raw SQL) |
| **Password** | Bcrypt with cost factor 12 (2^12 iterations) |
| **Rate Limiting** | Flask-Limiter (100 requests/hour per IP) - Should Have |

---

## 7. Scalability Considerations

### 7.1 Current Limitations (Free Tier)

| Resource | Limit | Impact |
|----------|-------|--------|
| **RAM** | 512MB | ~100 concurrent users max |
| **Database** | 500MB | ~5,000 transactions/user |
| **Bandwidth** | 2GB/month | ~10,000 page views/month |
| **Cold Start** | 10-30 seconds | First request after inactivity |

### 7.2 Optimization Strategies

**Database:**
- Index on `(user_id, date)` for transaction queries
- Pagination (50 transactions per page)
- Lazy loading for relationships

**Caching (Future):**
- Flask-Caching for dashboard balance (TTL: 5 minutes)
- Redis for session storage (upgrade from cookies)

**Frontend:**
- Minify CSS/JS
- CDN for Bootstrap (reduce server load)
- Lazy load images

### 7.3 Migration Path to Paid Tier

**When to Upgrade:**
- >200 active users
- >1GB database size
- Cold starts impacting UX

**Render.com Paid Tier ($7/month):**
- 512MB → 2GB RAM
- No cold starts
- Custom domain

---

## 8. Framework Migration Strategy (Flask → Django)

### 8.1 Why Service Layer Matters

**Without Service Layer:**
```python
# Flask route with embedded logic (BAD)
@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    amount = request.form['amount']
    # Business logic mixed with routing
    if float(amount) <= 0:
        flash('Amount must be positive')
        return redirect('/transactions')
    transaction = Transaction(amount=amount, user_id=current_user.id)
    db.session.add(transaction)
    db.session.commit()
    return redirect('/dashboard')
```

**Migration Effort:** Rewrite entire route for Django views (high effort)

---

**With Service Layer:**
```python
# Flask route (thin controller)
@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    result = TransactionService.add_transaction(
        user_id=current_user.id,
        amount=request.form['amount'],
        description=request.form['description']
    )
    if result.success:
        flash('Transaction added!')
    else:
        flash(result.error)
    return redirect('/dashboard')

# Django view (same service call)
def add_transaction(request):
    result = TransactionService.add_transaction(
        user_id=request.user.id,
        amount=request.POST['amount'],
        description=request.POST['description']
    )
    if result.success:
        messages.success(request, 'Transaction added!')
    else:
        messages.error(request, result.error)
    return redirect('dashboard')
```

**Migration Effort:** Only rewrite routes/views (low effort, service unchanged)

### 8.2 Migration Checklist

| Component | Flask | Django | Effort |
|-----------|-------|--------|--------|
| **Routes** | Blueprints | URLs + Views | Medium |
| **Models** | SQLAlchemy | Django ORM | High |
| **Templates** | Jinja2 | Django Templates | Low (syntax similar) |
| **Forms** | Flask-WTF | Django Forms | Medium |
| **Services** | Pure Python | **No change** | **None** |

---

## 9. Error Handling & Logging

### 9.1 Error Handling Strategy

**User-Facing Errors:**
- Flash messages for validation errors
- Custom 404/500 error pages

**Developer Errors:**
- Centralized logging with Python `logging` module
- Log levels: DEBUG (dev), INFO (prod), ERROR (critical)

**Example:**
```python
# app/services/transaction_service.py
import logging

logger = logging.getLogger(__name__)

class TransactionService:
    @staticmethod
    def add_transaction(user_id, amount, ...):
        try:
            # Business logic
            transaction = Transaction(...)
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"Transaction added: {transaction.id}")
            return Result(success=True)
        except Exception as e:
            logger.error(f"Failed to add transaction: {str(e)}")
            db.session.rollback()
            return Result(success=False, error="An error occurred")
```

### 9.2 Logging Configuration

```python
# config.py
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'level': 'INFO'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}
```

---

## 10. API Design (Future REST API)

### 10.1 RESTful Endpoints (Could Have for v2.0)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user, return JWT |
| GET | `/api/v1/transactions` | List user's transactions |
| POST | `/api/v1/transactions` | Create new transaction |
| PUT | `/api/v1/transactions/<id>` | Update transaction |
| DELETE | `/api/v1/transactions/<id>` | Delete transaction |
| GET | `/api/v1/dashboard/balance` | Get current balance |

**Authentication:** JWT tokens (Flask-JWT-Extended)

---

## 11. Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                     │
│                  (Source Code + Docs)                    │
└────────────────────┬────────────────────────────────────┘
                     │ Git Push
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Render.com                            │
│  ┌────────────────────────────────────────────────┐     │
│  │  Auto-Deploy Trigger (on push to main branch) │     │
│  └────────────────┬───────────────────────────────┘     │
│                   ▼                                      │
│  ┌────────────────────────────────────────────────┐     │
│  │  Build Process:                                │     │
│  │  1. Install dependencies (requirements.txt)    │     │
│  │  2. Run database migrations (flask db upgrade) │     │
│  │  3. Collect static files                       │     │
│  │  4. Start Gunicorn server                      │     │
│  └────────────────┬───────────────────────────────┘     │
│                   ▼                                      │
│  ┌────────────────────────────────────────────────┐     │
│  │  Flask App Running (Gunicorn + 4 workers)      │     │
│  │  Port: 10000 (Render default)                  │     │
│  └────────────────┬───────────────────────────────┘     │
└───────────────────┼─────────────────────────────────────┘
                    │ HTTPS
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Supabase PostgreSQL Database                │
│  - Connection via DATABASE_URL environment variable      │
│  - SSL/TLS encrypted connection                          │
└─────────────────────────────────────────────────────────┘
```

---

## 12. Architectural Decision Records (ADRs)

### ADR-001: Why Flask over Django?

**Decision:** Use Flask for initial development

**Rationale:**
- Lightweight (faster learning curve)
- Minimal boilerplate for MVP
- Service layer enables future Django migration

**Consequences:**
- Must manually configure many features (auth, admin panel)
- Less "batteries included" than Django

---

### ADR-002: Why PostgreSQL over SQLite?

**Decision:** Use PostgreSQL from day one

**Rationale:**
- Production-ready (no migration from SQLite later)
- Better concurrency handling
- ACID compliance for financial data

**Consequences:**
- Requires external hosting (Supabase)
- Slightly more complex local setup

---

### ADR-003: Why Service Layer?

**Decision:** Introduce service layer between routes and models

**Rationale:**
- Framework-agnostic business logic
- Easier testing (mock database)
- Enables Flask → Django migration

**Consequences:**
- Additional abstraction layer (more files)
- Requires discipline to avoid logic in routes

---

## 13. Future Enhancements

### 13.1 Microservices (v3.0+)

**Potential Split:**
- **Auth Service**: User management, JWT tokens
- **Transaction Service**: CRUD operations
- **Notification Service**: Email/push notifications
- **Analytics Service**: Spending insights, charts

**Communication:** REST APIs or message queue (RabbitMQ)

### 13.2 Real-Time Features

- **WebSockets**: Live balance updates for shared households
- **Server-Sent Events (SSE)**: Budget alert notifications

---

## 14. Conclusion

SwiftBudget's architecture balances **simplicity** (for rapid MVP development) with **flexibility** (for future scaling and framework migration). The service layer is the cornerstone of this design, ensuring business logic remains portable and testable.

**Key Takeaways:**
1. **MVC + Service Layer** = Clean separation of concerns
2. **PostgreSQL** = ACID compliance for financial data
3. **Flask Blueprints** = Modular, maintainable routes
4. **Service Layer** = Framework-agnostic, migration-ready

---

## 15. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial SAD creation |

**Next Document:** Database Design Document (DDD)
