# SwiftBudget - Testing Strategy Document

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Testing Framework:** Pytest + Flask-Testing  
**Coverage Target:** 80%+ for critical paths

---

## 1. Testing Overview

### 1.1 Testing Philosophy

SwiftBudget handles **financial data** where bugs can have real consequences (lost transactions, incorrect balances). Our testing strategy prioritizes:

- **Correctness**: Financial calculations must be exact (no rounding errors)
- **Security**: Authentication and authorization thoroughly tested
- **Reliability**: Core user flows must work 99.9% of the time
- **Regression Prevention**: Automated tests catch breaking changes

### 1.2 Testing Pyramid

```
                    ┌─────────────┐
                    │   Manual    │  5%
                    │   Testing   │
                    └─────────────┘
                 ┌──────────────────┐
                 │   E2E Tests      │  15%
                 │  (Playwright)    │
                 └──────────────────┘
            ┌────────────────────────────┐
            │   Integration Tests        │  30%
            │   (API + Database)         │
            └────────────────────────────┘
       ┌─────────────────────────────────────┐
       │        Unit Tests                   │  50%
       │   (Services, Models, Utils)         │
       └─────────────────────────────────────┘
```

**Distribution:**
- **50% Unit Tests**: Fast, isolated tests for business logic
- **30% Integration Tests**: Database interactions, API endpoints
- **15% E2E Tests**: Full user workflows (signup → add transaction → view dashboard)
- **5% Manual Testing**: Exploratory testing, UX validation

---

## 2. Testing Tools & Frameworks

### 2.1 Technology Stack

| Tool | Purpose | Version |
|------|---------|---------|
| **Pytest** | Test framework | 7.4+ |
| **Flask-Testing** | Flask test utilities | 0.8+ |
| **Coverage.py** | Code coverage reporting | 7.3+ |
| **Faker** | Test data generation | 19.0+ |
| **Factory Boy** | Model factories | 3.3+ |
| **Playwright** | E2E browser testing | 1.40+ |
| **pytest-mock** | Mocking framework | 3.12+ |

### 2.2 Installation

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock flask-testing faker factory-boy playwright

# Install Playwright browsers
playwright install
```

### 2.3 Project Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py       # User, Transaction, Category models
│   ├── test_services.py     # Business logic tests
│   └── test_utils.py        # Helper functions
├── integration/
│   ├── __init__.py
│   ├── test_auth_routes.py  # Login, signup, logout
│   ├── test_transaction_routes.py
│   ├── test_budget_routes.py
│   └── test_database.py     # Database operations
├── e2e/
│   ├── __init__.py
│   ├── test_user_flows.py   # Complete user journeys
│   └── test_critical_paths.py
└── fixtures/
    ├── __init__.py
    ├── factories.py         # Factory Boy factories
    └── sample_data.py       # Test data
```

---

## 3. Unit Testing

### 3.1 Model Tests

**Purpose:** Test SQLAlchemy models and relationships

**Example: User Model**
```python
# tests/unit/test_models.py
import pytest
from app.models import User, Category, Transaction
from app import db

class TestUserModel:
    def test_user_creation(self, app):
        """Test creating a user with valid data"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('SecurePass123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.password_hash != 'SecurePass123'  # Hashed
    
    def test_password_hashing(self, app):
        """Test bcrypt password hashing"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('MyPassword123')
            
            assert user.check_password('MyPassword123') is True
            assert user.check_password('WrongPassword') is False
    
    def test_user_relationships(self, app, user_factory):
        """Test user has many transactions"""
        with app.app_context():
            user = user_factory()
            category = Category(name='Food', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                user_id=user.id,
                category_id=category.id,
                amount=45.50,
                description='Lunch',
                transaction_date='2026-02-20',
                type='expense'
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert len(user.transactions) == 1
            assert user.transactions[0].amount == 45.50
```

**Example: Transaction Model**
```python
class TestTransactionModel:
    def test_transaction_validation(self, app, user_factory, category_factory):
        """Test transaction amount must be positive"""
        with app.app_context():
            user = user_factory()
            category = category_factory(user_id=user.id)
            
            # Valid transaction
            transaction = Transaction(
                user_id=user.id,
                category_id=category.id,
                amount=100.00,
                transaction_date='2026-02-20',
                type='expense'
            )
            db.session.add(transaction)
            db.session.commit()
            assert transaction.id is not None
            
            # Invalid transaction (negative amount)
            with pytest.raises(Exception):  # Database constraint violation
                bad_transaction = Transaction(
                    user_id=user.id,
                    category_id=category.id,
                    amount=-50.00,  # Invalid
                    transaction_date='2026-02-20',
                    type='expense'
                )
                db.session.add(bad_transaction)
                db.session.commit()
```

### 3.2 Service Layer Tests

**Purpose:** Test business logic in isolation

**Example: TransactionService**
```python
# tests/unit/test_services.py
import pytest
from decimal import Decimal
from app.services.transaction_service import TransactionService
from app.models import Transaction

class TestTransactionService:
    def test_add_transaction(self, app, user_factory, category_factory):
        """Test adding a transaction via service"""
        with app.app_context():
            user = user_factory()
            category = category_factory(user_id=user.id)
            
            result = TransactionService.add_transaction(
                user_id=user.id,
                category_id=category.id,
                amount=45.50,
                description='Grocery shopping',
                date='2026-02-20',
                type='expense'
            )
            
            assert result.success is True
            assert result.transaction.amount == Decimal('45.50')
            assert result.transaction.description == 'Grocery shopping'
    
    def test_calculate_balance(self, app, user_factory, category_factory):
        """Test balance calculation (income - expenses)"""
        with app.app_context():
            user = user_factory()
            income_cat = category_factory(user_id=user.id, name='Income')
            expense_cat = category_factory(user_id=user.id, name='Food')
            
            # Add income
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=income_cat.id,
                amount=3500.00,
                description='Salary',
                date='2026-02-01',
                type='income'
            )
            
            # Add expenses
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=expense_cat.id,
                amount=45.50,
                description='Lunch',
                date='2026-02-15',
                type='expense'
            )
            
            balance = TransactionService.calculate_balance(user.id)
            assert balance == Decimal('3454.50')  # 3500 - 45.50
    
    def test_category_breakdown(self, app, user_factory, category_factory):
        """Test monthly spending by category"""
        with app.app_context():
            user = user_factory()
            food_cat = category_factory(user_id=user.id, name='Food')
            transport_cat = category_factory(user_id=user.id, name='Transport')
            
            # Add transactions
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=food_cat.id,
                amount=100.00,
                date='2026-02-10',
                type='expense'
            )
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=food_cat.id,
                amount=50.00,
                date='2026-02-15',
                type='expense'
            )
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=transport_cat.id,
                amount=30.00,
                date='2026-02-12',
                type='expense'
            )
            
            breakdown = TransactionService.get_category_breakdown(
                user_id=user.id,
                month=2,
                year=2026
            )
            
            assert breakdown['Food'] == Decimal('150.00')
            assert breakdown['Transport'] == Decimal('30.00')
```

**Example: BudgetService**
```python
class TestBudgetService:
    def test_set_budget_goal(self, app, user_factory, category_factory):
        """Test setting a budget goal"""
        with app.app_context():
            user = user_factory()
            category = category_factory(user_id=user.id, name='Food')
            
            result = BudgetService.set_budget_goal(
                user_id=user.id,
                category_id=category.id,
                amount=500.00,
                period='monthly'
            )
            
            assert result.success is True
            assert result.budget_goal.amount == Decimal('500.00')
    
    def test_check_budget_alerts(self, app, user_factory, category_factory):
        """Test budget alert when 80% spent"""
        with app.app_context():
            user = user_factory()
            category = category_factory(user_id=user.id, name='Food')
            
            # Set budget goal
            BudgetService.set_budget_goal(
                user_id=user.id,
                category_id=category.id,
                amount=500.00,
                period='monthly'
            )
            
            # Spend 85% of budget
            TransactionService.add_transaction(
                user_id=user.id,
                category_id=category.id,
                amount=425.00,
                date='2026-02-20',
                type='expense'
            )
            
            alerts = BudgetService.check_budget_alerts(user.id)
            
            assert len(alerts) == 1
            assert alerts[0]['category'] == 'Food'
            assert alerts[0]['percent_used'] == 85
```

### 3.3 Utility Function Tests

**Example: Date Helpers**
```python
# tests/unit/test_utils.py
from app.utils.date_helpers import get_month_range, is_future_date

class TestDateHelpers:
    def test_get_month_range(self):
        """Test getting first and last day of month"""
        start, end = get_month_range(2026, 2)
        
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)
    
    def test_is_future_date(self):
        """Test future date validation"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        assert is_future_date(tomorrow) is True
        assert is_future_date(today) is False
        assert is_future_date(yesterday) is False
```

---

## 4. Integration Testing

### 4.1 Route Tests

**Purpose:** Test Flask routes with database interactions

**Example: Authentication Routes**
```python
# tests/integration/test_auth_routes.py
import pytest
from flask import url_for

class TestAuthRoutes:
    def test_signup_success(self, client):
        """Test successful user registration"""
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome to SwiftBudget' in response.data
        
        # Verify user created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
    
    def test_signup_duplicate_username(self, client, user_factory):
        """Test signup with existing username"""
        existing_user = user_factory(username='existinguser')
        
        response = client.post('/signup', data={
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123'
        })
        
        assert b'Username already exists' in response.data
    
    def test_login_success(self, client, user_factory):
        """Test successful login"""
        user = user_factory(username='testuser')
        user.set_password('MyPassword123')
        db.session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'MyPassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_login_invalid_credentials(self, client, user_factory):
        """Test login with wrong password"""
        user = user_factory(username='testuser')
        user.set_password('CorrectPassword')
        db.session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, client, authenticated_user):
        """Test logout functionality"""
        response = client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'You have been logged out' in response.data
```

**Example: Transaction Routes**
```python
class TestTransactionRoutes:
    def test_add_transaction_authenticated(self, client, authenticated_user, category_factory):
        """Test adding transaction as logged-in user"""
        category = category_factory(user_id=authenticated_user.id)
        
        response = client.post('/transactions/add', data={
            'amount': '45.50',
            'description': 'Lunch',
            'date': '2026-02-20',
            'category_id': category.id,
            'type': 'expense',
            'csrf_token': get_csrf_token(client)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Transaction added successfully' in response.data
        
        # Verify transaction in database
        transaction = Transaction.query.filter_by(
            user_id=authenticated_user.id,
            description='Lunch'
        ).first()
        assert transaction is not None
        assert transaction.amount == Decimal('45.50')
    
    def test_add_transaction_unauthenticated(self, client):
        """Test adding transaction without login (should redirect)"""
        response = client.post('/transactions/add', data={
            'amount': '45.50',
            'description': 'Lunch',
            'date': '2026-02-20'
        })
        
        assert response.status_code == 302  # Redirect to login
    
    def test_edit_transaction_owner(self, client, authenticated_user, transaction_factory):
        """Test editing own transaction"""
        transaction = transaction_factory(user_id=authenticated_user.id)
        
        response = client.post(f'/transactions/edit/{transaction.id}', data={
            'amount': '100.00',
            'description': 'Updated description',
            'date': transaction.transaction_date,
            'category_id': transaction.category_id,
            'type': 'expense',
            'csrf_token': get_csrf_token(client)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Transaction updated' in response.data
        
        # Verify update
        db.session.refresh(transaction)
        assert transaction.amount == Decimal('100.00')
    
    def test_edit_transaction_not_owner(self, client, authenticated_user, user_factory, transaction_factory):
        """Test editing another user's transaction (should fail)"""
        other_user = user_factory()
        other_transaction = transaction_factory(user_id=other_user.id)
        
        response = client.post(f'/transactions/edit/{other_transaction.id}', data={
            'amount': '100.00',
            'csrf_token': get_csrf_token(client)
        })
        
        assert response.status_code == 403  # Forbidden
```

### 4.2 Database Tests

**Purpose:** Test database operations and constraints

```python
# tests/integration/test_database.py
class TestDatabaseConstraints:
    def test_unique_username_constraint(self, app, user_factory):
        """Test database enforces unique usernames"""
        with app.app_context():
            user1 = user_factory(username='testuser')
            
            with pytest.raises(Exception):  # IntegrityError
                user2 = User(username='testuser', email='other@example.com')
                user2.set_password('password')
                db.session.add(user2)
                db.session.commit()
    
    def test_transaction_amount_positive_constraint(self, app, user_factory, category_factory):
        """Test database enforces positive amounts"""
        with app.app_context():
            user = user_factory()
            category = category_factory(user_id=user.id)
            
            with pytest.raises(Exception):  # CheckConstraint violation
                transaction = Transaction(
                    user_id=user.id,
                    category_id=category.id,
                    amount=-100.00,  # Invalid
                    transaction_date='2026-02-20',
                    type='expense'
                )
                db.session.add(transaction)
                db.session.commit()
    
    def test_cascade_delete_user(self, app, user_factory, transaction_factory):
        """Test deleting user cascades to transactions"""
        with app.app_context():
            user = user_factory()
            transaction = transaction_factory(user_id=user.id)
            transaction_id = transaction.id
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            
            # Verify transaction also deleted
            deleted_transaction = Transaction.query.get(transaction_id)
            assert deleted_transaction is None
```

---

## 5. End-to-End Testing

### 5.1 Playwright Setup

**Purpose:** Test complete user workflows in real browser

**Configuration:**
```python
# tests/e2e/conftest.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
```

### 5.2 Critical User Flows

**Example: Complete User Journey**
```python
# tests/e2e/test_user_flows.py
import pytest
from playwright.sync_api import expect

class TestCompleteUserFlow:
    def test_signup_to_first_transaction(self, page, live_server):
        """Test: New user signs up, adds transaction, views dashboard"""
        base_url = live_server.url()
        
        # 1. Navigate to signup page
        page.goto(f'{base_url}/signup')
        expect(page).to_have_title('Sign Up - SwiftBudget')
        
        # 2. Fill signup form
        page.fill('input[name="username"]', 'e2euser')
        page.fill('input[name="email"]', 'e2e@example.com')
        page.fill('input[name="password"]', 'SecurePass123')
        page.fill('input[name="confirm_password"]', 'SecurePass123')
        page.click('button[type="submit"]')
        
        # 3. Verify redirected to dashboard
        expect(page).to_have_url(f'{base_url}/dashboard')
        expect(page.locator('h1')).to_contain_text('Dashboard')
        
        # 4. Add first transaction
        page.click('a:has-text("Add Transaction")')
        page.fill('input[name="amount"]', '45.50')
        page.fill('input[name="description"]', 'First expense')
        page.fill('input[name="date"]', '2026-02-20')
        page.select_option('select[name="category_id"]', label='Food & Dining')
        page.select_option('select[name="type"]', 'expense')
        page.click('button:has-text("Add Transaction")')
        
        # 5. Verify transaction appears on dashboard
        expect(page.locator('.transaction-list')).to_contain_text('First expense')
        expect(page.locator('.transaction-list')).to_contain_text('$45.50')
        
        # 6. Verify balance updated
        balance = page.locator('.balance-amount').text_content()
        assert '-$45.50' in balance  # Negative because it's an expense
    
    def test_budget_alert_workflow(self, page, live_server, authenticated_user):
        """Test: Set budget goal, exceed threshold, see alert"""
        base_url = live_server.url()
        
        # Login
        login_user(page, base_url, authenticated_user)
        
        # 1. Set budget goal
        page.goto(f'{base_url}/budget/goals')
        page.click('button:has-text("Add Budget Goal")')
        page.select_option('select[name="category_id"]', label='Food & Dining')
        page.fill('input[name="amount"]', '500.00')
        page.select_option('select[name="period"]', 'monthly')
        page.click('button:has-text("Save Goal")')
        
        # 2. Add transaction (85% of budget)
        page.goto(f'{base_url}/transactions/add')
        page.fill('input[name="amount"]', '425.00')
        page.fill('input[name="description"]', 'Big grocery trip')
        page.fill('input[name="date"]', '2026-02-20')
        page.select_option('select[name="category_id"]', label='Food & Dining')
        page.select_option('select[name="type"]', 'expense')
        page.click('button:has-text("Add Transaction")')
        
        # 3. Verify alert on dashboard
        page.goto(f'{base_url}/dashboard')
        expect(page.locator('.budget-alert')).to_contain_text('You have used 85% of your Food & Dining budget')
```

### 5.3 Accessibility Testing

**Example: Keyboard Navigation**
```python
class TestAccessibility:
    def test_keyboard_navigation(self, page, live_server):
        """Test all forms are keyboard-accessible"""
        page.goto(f'{live_server.url()}/login')
        
        # Tab through form
        page.keyboard.press('Tab')  # Focus username
        page.keyboard.type('testuser')
        page.keyboard.press('Tab')  # Focus password
        page.keyboard.type('password123')
        page.keyboard.press('Tab')  # Focus submit button
        page.keyboard.press('Enter')  # Submit form
        
        # Verify form submitted
        expect(page).to_have_url(f'{live_server.url()}/dashboard')
    
    def test_screen_reader_labels(self, page, live_server):
        """Test form inputs have proper labels"""
        page.goto(f'{live_server.url()}/signup')
        
        # Check for aria-labels or associated labels
        username_input = page.locator('input[name="username"]')
        assert username_input.get_attribute('aria-label') or \
               page.locator('label[for="username"]').is_visible()
```

---

## 6. Test Fixtures & Factories

### 6.1 Pytest Fixtures

```python
# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User, Category, Transaction

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Flask CLI test runner"""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def reset_database(app):
    """Reset database before each test"""
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
```

### 6.2 Factory Boy Factories

```python
# tests/fixtures/factories.py
import factory
from app import db
from app.models import User, Category, Transaction
from datetime import date

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password_hash = factory.PostGenerationMethodCall('set_password', 'DefaultPass123')

class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session = db.session
    
    name = factory.Sequence(lambda n: f'Category{n}')
    user = factory.SubFactory(UserFactory)
    is_default = False

class TransactionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Transaction
        sqlalchemy_session = db.session
    
    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    description = factory.Faker('sentence', nb_words=4)
    transaction_date = factory.LazyFunction(date.today)
    type = 'expense'

# Pytest fixtures using factories
@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def category_factory():
    return CategoryFactory

@pytest.fixture
def transaction_factory():
    return TransactionFactory

@pytest.fixture
def authenticated_user(client, user_factory):
    """Create and login a user"""
    user = user_factory()
    with client:
        client.post('/login', data={
            'username': user.username,
            'password': 'DefaultPass123'
        })
        yield user
```

---

## 7. Code Coverage

### 7.1 Coverage Configuration

```ini
# .coveragerc
[run]
source = app
omit =
    */tests/*
    */venv/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
precision = 2

[html]
directory = htmlcov
```

### 7.2 Running Coverage

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Coverage targets
# Overall: 80%+
# Critical paths (auth, transactions): 95%+
# Service layer: 90%+
```

### 7.3 Coverage Targets

| Module | Target | Rationale |
|--------|--------|-----------|
| **Services** | 90%+ | Core business logic |
| **Models** | 85%+ | Data integrity critical |
| **Routes** | 80%+ | User-facing functionality |
| **Utils** | 75%+ | Helper functions |
| **Overall** | 80%+ | Industry standard |

---

## 8. Performance Testing

### 8.1 Load Testing

**Tool:** Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class SwiftBudgetUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tasks"""
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
    
    @task(3)
    def view_dashboard(self):
        """Most common action"""
        self.client.get('/dashboard')
    
    @task(2)
    def view_transactions(self):
        self.client.get('/transactions')
    
    @task(1)
    def add_transaction(self):
        self.client.post('/transactions/add', data={
            'amount': '45.50',
            'description': 'Test transaction',
            'date': '2026-02-20',
            'category_id': 1,
            'type': 'expense'
        })

# Run: locust -f tests/performance/locustfile.py
# Target: 50 concurrent users, <2s response time
```

### 8.2 Database Query Performance

```python
# tests/performance/test_query_performance.py
import pytest
import time

class TestQueryPerformance:
    def test_dashboard_query_speed(self, app, user_factory, transaction_factory):
        """Test dashboard loads in <500ms with 100 transactions"""
        with app.app_context():
            user = user_factory()
            
            # Create 100 transactions
            for _ in range(100):
                transaction_factory(user_id=user.id)
            
            # Measure query time
            start = time.time()
            transactions = Transaction.query.filter_by(user_id=user.id).limit(10).all()
            balance = TransactionService.calculate_balance(user.id)
            end = time.time()
            
            query_time = (end - start) * 1000  # Convert to ms
            assert query_time < 500, f"Query took {query_time}ms (target: <500ms)"
```

---

## 9. Security Testing

### 9.1 Automated Security Tests

```python
# tests/security/test_security.py
class TestSecurity:
    def test_sql_injection_prevention(self, client, authenticated_user):
        """Test SQL injection is prevented"""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post('/transactions/add', data={
            'description': malicious_input,
            'amount': '45.50',
            'date': '2026-02-20',
            'category_id': 1,
            'type': 'expense'
        })
        
        # Verify users table still exists
        assert User.query.count() > 0
    
    def test_xss_prevention(self, client, authenticated_user, category_factory):
        """Test XSS script tags are escaped"""
        category = category_factory(user_id=authenticated_user.id)
        xss_payload = '<script>alert("XSS")</script>'
        
        client.post('/transactions/add', data={
            'description': xss_payload,
            'amount': '45.50',
            'date': '2026-02-20',
            'category_id': category.id,
            'type': 'expense'
        })
        
        response = client.get('/dashboard')
        
        # Verify script tag is escaped
        assert b'<script>' not in response.data
        assert b'&lt;script&gt;' in response.data
    
    def test_csrf_protection(self, client, authenticated_user):
        """Test CSRF token is required"""
        response = client.post('/transactions/add', data={
            'amount': '45.50',
            'description': 'Test',
            'date': '2026-02-20'
            # Missing csrf_token
        })
        
        assert response.status_code == 400  # Bad request
    
    def test_authorization_check(self, client, user_factory, transaction_factory):
        """Test users cannot access other users' data"""
        user1 = user_factory()
        user2 = user_factory()
        transaction = transaction_factory(user_id=user1.id)
        
        # Login as user2
        client.post('/login', data={
            'username': user2.username,
            'password': 'DefaultPass123'
        })
        
        # Try to access user1's transaction
        response = client.get(f'/transactions/edit/{transaction.id}')
        
        assert response.status_code == 403  # Forbidden
```

---

## 10. Continuous Integration

### 10.1 GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 11. Testing Checklist

### 11.1 Pre-Commit

- [ ] All unit tests pass (`pytest tests/unit`)
- [ ] Code coverage >80% (`pytest --cov`)
- [ ] No linting errors (`flake8 app/`)
- [ ] Security scan clean (`bandit -r app/`)

### 11.2 Pre-Deployment

- [ ] All tests pass (unit + integration + e2e)
- [ ] Load testing completed (50 concurrent users)
- [ ] Security testing passed
- [ ] Manual smoke testing on staging
- [ ] Database migrations tested

### 11.3 Post-Deployment

- [ ] Health check endpoint responding
- [ ] Critical user flows tested manually
- [ ] Error monitoring configured
- [ ] Performance metrics within targets

---

## 12. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial testing strategy |

---

**Testing is complete when:**
1. All critical paths have automated tests
2. Code coverage meets targets (80%+)
3. Security tests pass
4. Performance benchmarks met
5. Manual testing confirms UX quality
