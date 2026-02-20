# SwiftBudget - API Specification Document

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Framework:** Flask  
**API Type:** RESTful (Future) + Server-Side Rendered (Current)

---

## 1. API Overview

### 1.1 Current Implementation (v1.0 - Server-Side Rendered)

SwiftBudget v1.0 uses **traditional server-side rendering** with Flask routes returning HTML templates. This approach prioritizes:

- **Simplicity**: No need for separate frontend/backend codebases
- **SEO-Friendly**: Full HTML pages rendered server-side
- **Fast Development**: Jinja2 templates with minimal JavaScript
- **Progressive Enhancement**: Works without JavaScript enabled

**Architecture:**
```
Browser → HTTP Request → Flask Route → Service Layer → Database
                              ↓
                         Jinja2 Template
                              ↓
                         HTML Response → Browser
```

### 1.2 Future REST API (v2.0 - Could Have)

For mobile apps or third-party integrations, a RESTful API will be added:

- **JSON Responses**: Structured data instead of HTML
- **JWT Authentication**: Stateless token-based auth
- **Versioned Endpoints**: `/api/v1/...` for backward compatibility
- **Rate Limiting**: Prevent abuse (100 requests/hour)

---

## 2. Route Specifications (v1.0)

### 2.1 Authentication Routes

#### **POST /signup**

**Purpose:** Register a new user account

**Request:**
```http
POST /signup HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=john_doe&email=john@example.com&password=SecurePass123&confirm_password=SecurePass123
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `username` | String | Yes | 3-80 chars, alphanumeric + underscore |
| `email` | String | Yes | Valid email format |
| `password` | String | Yes | Min 8 chars, 1 uppercase, 1 number |
| `confirm_password` | String | Yes | Must match `password` |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /dashboard
Set-Cookie: session=abc123...; HttpOnly; Secure; SameSite=Lax

Flash Message: "Account created successfully! Welcome to SwiftBudget."
```

**Response (Error - Duplicate Username):**
```http
HTTP/1.1 200 OK
Content-Type: text/html

Flash Message: "Username already exists. Please choose another."
(Re-renders signup form with error)
```

**Business Logic:**
1. Validate form inputs (Flask-WTF)
2. Check if username/email already exists
3. Hash password with bcrypt (cost factor 12)
4. Create User record
5. Create default categories for user
6. Create notification preferences
7. Log user in (create session)
8. Redirect to dashboard

---

#### **POST /login**

**Purpose:** Authenticate existing user

**Request:**
```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=SecurePass123&remember_me=on
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `username` | String | Yes | - |
| `password` | String | Yes | - |
| `remember_me` | Boolean | No | Extends session to 30 days |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /dashboard
Set-Cookie: session=xyz789...; HttpOnly; Secure; Max-Age=2592000

Flash Message: "Welcome back, John!"
```

**Response (Error - Invalid Credentials):**
```http
HTTP/1.1 200 OK

Flash Message: "Invalid username or password."
(Re-renders login form)
```

**Business Logic:**
1. Query user by username
2. Compare password hash with bcrypt
3. If match: Create session with Flask-Login
4. If `remember_me`: Set session expiration to 30 days
5. Redirect to dashboard or `next` parameter

---

#### **GET /logout**

**Purpose:** End user session

**Request:**
```http
GET /logout HTTP/1.1
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 302 Found
Location: /login
Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT

Flash Message: "You have been logged out."
```

**Business Logic:**
1. Call `logout_user()` (Flask-Login)
2. Clear session cookie
3. Redirect to login page

---

### 2.2 Dashboard Routes

#### **GET /dashboard**

**Purpose:** Display user's financial overview

**Request:**
```http
GET /dashboard HTTP/1.1
Cookie: session=xyz789...
```

**Authorization:** Requires authenticated user (Flask-Login)

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
  <body>
    <h1>Dashboard</h1>
    <div class="balance">
      <h2>Current Balance: $2,345.50</h2>
    </div>
    <div class="recent-transactions">
      <!-- Last 10 transactions -->
    </div>
    <div class="monthly-summary">
      <!-- Category breakdown chart -->
    </div>
  </body>
</html>
```

**Data Provided to Template:**
```python
{
    'user': current_user,
    'balance': 2345.50,  # Calculated from TransactionService
    'recent_transactions': [
        {
            'id': 123,
            'amount': 45.50,
            'description': 'Grocery shopping',
            'date': '2026-02-20',
            'category': 'Food & Dining',
            'type': 'expense'
        },
        # ... 9 more
    ],
    'monthly_spending': {
        'Food & Dining': 320.00,
        'Transportation': 150.00,
        # ...
    },
    'budget_alerts': [
        {
            'category': 'Entertainment',
            'percent_used': 85,
            'message': 'You have used 85% of your Entertainment budget'
        }
    ]
}
```

**Business Logic:**
1. Get current user from session
2. Calculate balance (TransactionService.calculate_balance)
3. Fetch last 10 transactions
4. Calculate monthly spending by category
5. Check budget alerts (BudgetService.check_alerts)
6. Render `dashboard.html` template

---

### 2.3 Transaction Routes

#### **GET /transactions**

**Purpose:** List all user transactions with filtering

**Request:**
```http
GET /transactions?page=1&category=1&start_date=2026-02-01&end_date=2026-02-28 HTTP/1.1
Cookie: session=xyz789...
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | Integer | No | 1 | Pagination page number |
| `category` | Integer | No | All | Filter by category ID |
| `start_date` | Date | No | 30 days ago | Start of date range (YYYY-MM-DD) |
| `end_date` | Date | No | Today | End of date range (YYYY-MM-DD) |
| `type` | String | No | All | Filter by 'income' or 'expense' |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Paginated table of transactions -->
<!-- 50 transactions per page -->
```

**Business Logic:**
1. Parse query parameters
2. Build filtered query (SQLAlchemy)
3. Paginate results (50 per page)
4. Render `transactions.html` template

---

#### **GET /transactions/add**

**Purpose:** Display form to add new transaction

**Request:**
```http
GET /transactions/add HTTP/1.1
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Form with fields: amount, description, date, category, type -->
```

**Data Provided to Template:**
```python
{
    'form': TransactionForm(),  # Flask-WTF form
    'categories': [
        {'id': 1, 'name': 'Food & Dining'},
        {'id': 2, 'name': 'Transportation'},
        # ...
    ]
}
```

---

#### **POST /transactions/add**

**Purpose:** Create new transaction

**Request:**
```http
POST /transactions/add HTTP/1.1
Content-Type: application/x-www-form-urlencoded

amount=45.50&description=Lunch&date=2026-02-20&category_id=1&type=expense&csrf_token=abc123
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `amount` | Decimal | Yes | > 0, max 2 decimal places |
| `description` | String | No | Max 200 chars |
| `date` | Date | Yes | Not in future, format YYYY-MM-DD |
| `category_id` | Integer | Yes | Must be user's category |
| `type` | String | Yes | 'income' or 'expense' |
| `csrf_token` | String | Yes | Flask-WTF CSRF protection |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /dashboard

Flash Message: "Transaction added successfully!"
```

**Response (Error - Invalid Amount):**
```http
HTTP/1.1 200 OK

Flash Message: "Amount must be a positive number."
(Re-renders form with error)
```

**Business Logic:**
1. Validate form (Flask-WTF)
2. Verify category belongs to user
3. Call TransactionService.add_transaction()
4. Check if budget alert triggered
5. Redirect to dashboard

---

#### **GET /transactions/edit/<id>**

**Purpose:** Display form to edit existing transaction

**Request:**
```http
GET /transactions/edit/123 HTTP/1.1
Cookie: session=xyz789...
```

**Authorization:** Transaction must belong to current user

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Pre-filled form with transaction data -->
```

**Response (Error - Not Found):**
```http
HTTP/1.1 404 Not Found

Flash Message: "Transaction not found."
```

---

#### **POST /transactions/edit/<id>**

**Purpose:** Update existing transaction

**Request:**
```http
POST /transactions/edit/123 HTTP/1.1
Content-Type: application/x-www-form-urlencoded

amount=50.00&description=Updated lunch&date=2026-02-20&category_id=1&type=expense&csrf_token=abc123
```

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /transactions

Flash Message: "Transaction updated successfully!"
```

**Business Logic:**
1. Verify transaction belongs to user
2. Validate form
3. Call TransactionService.update_transaction()
4. Recalculate balance if amount changed
5. Redirect to transactions list

---

#### **POST /transactions/delete/<id>**

**Purpose:** Soft delete transaction

**Request:**
```http
POST /transactions/delete/123 HTTP/1.1
Content-Type: application/x-www-form-urlencoded

csrf_token=abc123
```

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /transactions

Flash Message: "Transaction deleted."
```

**Business Logic:**
1. Verify transaction belongs to user
2. Set `is_deleted = TRUE` (soft delete)
3. Recalculate balance
4. Redirect to transactions list

---

### 2.4 Budget Routes

#### **GET /budget/goals**

**Purpose:** Display and manage budget goals

**Request:**
```http
GET /budget/goals HTTP/1.1
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- List of budget goals with progress bars -->
<!-- Form to add new goal -->
```

**Data Provided to Template:**
```python
{
    'budget_goals': [
        {
            'id': 1,
            'category': 'Food & Dining',
            'amount': 500.00,
            'current_spending': 320.00,
            'percent_used': 64,
            'period': 'monthly'
        },
        # ...
    ],
    'categories': [...]  # For dropdown
}
```

---

#### **POST /budget/goals/add**

**Purpose:** Create new budget goal

**Request:**
```http
POST /budget/goals/add HTTP/1.1
Content-Type: application/x-www-form-urlencoded

category_id=1&amount=500.00&period=monthly&csrf_token=abc123
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `category_id` | Integer | Yes | Must be user's category |
| `amount` | Decimal | Yes | > 0 |
| `period` | String | Yes | 'weekly', 'monthly', or 'yearly' |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /budget/goals

Flash Message: "Budget goal set for Food & Dining: $500.00/month"
```

**Business Logic:**
1. Validate form
2. Check if goal already exists for (category, period)
3. Call BudgetService.set_budget_goal()
4. Redirect to budget goals page

---

#### **POST /budget/goals/delete/<id>**

**Purpose:** Delete budget goal

**Request:**
```http
POST /budget/goals/delete/1 HTTP/1.1
Content-Type: application/x-www-form-urlencoded

csrf_token=abc123
```

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /budget/goals

Flash Message: "Budget goal deleted."
```

---

### 2.5 Settings Routes

#### **GET /settings**

**Purpose:** Display user settings and preferences

**Request:**
```http
GET /settings HTTP/1.1
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Tabs: Profile, Notifications, Categories, Security -->
```

---

#### **POST /settings/notifications**

**Purpose:** Update notification preferences

**Request:**
```http
POST /settings/notifications HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email_enabled=on&budget_alerts=on&weekly_summary=on&alert_threshold=80&csrf_token=abc123
```

**Form Fields:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `email_enabled` | Boolean | No | TRUE |
| `budget_alerts` | Boolean | No | TRUE |
| `weekly_summary` | Boolean | No | TRUE |
| `alert_threshold` | Integer | No | 80 (0-100) |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /settings

Flash Message: "Notification preferences updated."
```

---

#### **POST /settings/password**

**Purpose:** Change user password

**Request:**
```http
POST /settings/password HTTP/1.1
Content-Type: application/x-www-form-urlencoded

current_password=OldPass123&new_password=NewPass456&confirm_password=NewPass456&csrf_token=abc123
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `current_password` | String | Yes | Must match existing password |
| `new_password` | String | Yes | Min 8 chars, 1 uppercase, 1 number |
| `confirm_password` | String | Yes | Must match `new_password` |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /settings

Flash Message: "Password changed successfully."
```

**Business Logic:**
1. Verify current password
2. Validate new password strength
3. Hash new password with bcrypt
4. Update User record
5. Optionally: Log out all other sessions

---

### 2.6 Category Management Routes

#### **POST /categories/add**

**Purpose:** Create custom category

**Request:**
```http
POST /categories/add HTTP/1.1
Content-Type: application/x-www-form-urlencoded

name=Subscriptions&csrf_token=abc123
```

**Form Fields:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | String | Yes | Max 50 chars, unique per user |

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /settings

Flash Message: "Category 'Subscriptions' created."
```

---

#### **POST /categories/delete/<id>**

**Purpose:** Delete custom category

**Request:**
```http
POST /categories/delete/10 HTTP/1.1
Content-Type: application/x-www-form-urlencoded

csrf_token=abc123
```

**Response (Success):**
```http
HTTP/1.1 302 Found
Location: /settings

Flash Message: "Category deleted."
```

**Response (Error - Has Transactions):**
```http
HTTP/1.1 400 Bad Request

Flash Message: "Cannot delete category with existing transactions."
```

**Business Logic:**
1. Check if category has transactions (ON DELETE RESTRICT)
2. Check if `is_default = TRUE` (prevent deletion)
3. Delete category if allowed

---

## 3. Error Handling

### 3.1 HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| **200 OK** | Success | Successful GET requests, form re-renders with errors |
| **302 Found** | Redirect | Successful POST requests (PRG pattern) |
| **400 Bad Request** | Client Error | Invalid form data, business rule violation |
| **401 Unauthorized** | Not Authenticated | User not logged in |
| **403 Forbidden** | Not Authorized | User trying to access another user's data |
| **404 Not Found** | Resource Missing | Transaction/category doesn't exist |
| **500 Internal Server Error** | Server Error | Unhandled exceptions |

### 3.2 Custom Error Pages

#### **404 Not Found**

**Template:** `errors/404.html`

```html
<!DOCTYPE html>
<html>
<body>
  <h1>Page Not Found</h1>
  <p>The page you're looking for doesn't exist.</p>
  <a href="/dashboard">Return to Dashboard</a>
</body>
</html>
```

#### **500 Internal Server Error**

**Template:** `errors/500.html`

```html
<!DOCTYPE html>
<html>
<body>
  <h1>Something Went Wrong</h1>
  <p>We're working to fix the issue. Please try again later.</p>
  <a href="/dashboard">Return to Dashboard</a>
</body>
</html>
```

**Error Handler:**
```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback failed transaction
    logger.error(f"500 error: {str(error)}")
    return render_template('errors/500.html'), 500
```

### 3.3 Flash Message Categories

| Category | CSS Class | Usage |
|----------|-----------|-------|
| `success` | `alert-success` | "Transaction added successfully!" |
| `error` | `alert-danger` | "Invalid username or password." |
| `warning` | `alert-warning` | "You have used 85% of your budget." |
| `info` | `alert-info` | "Your weekly summary has been sent." |

**Implementation:**
```python
from flask import flash

flash('Transaction added successfully!', 'success')
flash('Invalid credentials.', 'error')
```

---

## 4. Future REST API (v2.0)

### 4.1 Authentication (JWT)

#### **POST /api/v1/auth/login**

**Request:**
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**Response (Success):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**Response (Error):**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "invalid_credentials",
  "message": "Invalid username or password"
}
```

---

### 4.2 Transactions API

#### **GET /api/v1/transactions**

**Request:**
```http
GET /api/v1/transactions?page=1&limit=50&category=1 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": [
    {
      "id": 123,
      "amount": "45.50",
      "description": "Grocery shopping",
      "date": "2026-02-20",
      "type": "expense",
      "category": {
        "id": 1,
        "name": "Food & Dining"
      },
      "created_at": "2026-02-20T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 245,
    "pages": 5
  }
}
```

---

#### **POST /api/v1/transactions**

**Request:**
```http
POST /api/v1/transactions HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": 45.50,
  "description": "Lunch at Chipotle",
  "date": "2026-02-20",
  "category_id": 1,
  "type": "expense"
}
```

**Response (Success):**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 124,
  "amount": "45.50",
  "description": "Lunch at Chipotle",
  "date": "2026-02-20",
  "type": "expense",
  "category": {
    "id": 1,
    "name": "Food & Dining"
  },
  "created_at": "2026-02-20T15:00:00Z"
}
```

**Response (Error - Validation):**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "validation_error",
  "message": "Amount must be greater than 0",
  "field": "amount"
}
```

---

#### **PUT /api/v1/transactions/<id>**

**Request:**
```http
PUT /api/v1/transactions/124 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "amount": 50.00,
  "description": "Updated lunch"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 124,
  "amount": "50.00",
  "description": "Updated lunch",
  "date": "2026-02-20",
  "type": "expense",
  "category": {
    "id": 1,
    "name": "Food & Dining"
  },
  "updated_at": "2026-02-20T16:00:00Z"
}
```

---

#### **DELETE /api/v1/transactions/<id>**

**Request:**
```http
DELETE /api/v1/transactions/124 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```http
HTTP/1.1 204 No Content
```

---

### 4.3 Dashboard API

#### **GET /api/v1/dashboard**

**Request:**
```http
GET /api/v1/dashboard HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "balance": "2345.50",
  "monthly_income": "3500.00",
  "monthly_expenses": "1154.50",
  "recent_transactions": [
    {
      "id": 123,
      "amount": "45.50",
      "description": "Grocery shopping",
      "date": "2026-02-20",
      "type": "expense",
      "category": "Food & Dining"
    }
  ],
  "category_breakdown": {
    "Food & Dining": "320.00",
    "Transportation": "150.00",
    "Housing (Rent/Mortgage)": "1200.00"
  },
  "budget_alerts": [
    {
      "category": "Entertainment",
      "budget": "200.00",
      "spent": "170.00",
      "percent_used": 85
    }
  ]
}
```

---

### 4.4 Rate Limiting

**Implementation:** Flask-Limiter

**Limits:**
- **Authentication:** 5 requests/minute (prevent brute force)
- **General API:** 100 requests/hour per user
- **Transaction Creation:** 20 requests/minute (prevent spam)

**Response (Rate Limit Exceeded):**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again in 60 seconds."
}
```

---

## 5. AJAX Endpoints (v1.0 Enhancement)

### 5.1 Real-Time Balance Update

#### **GET /ajax/balance**

**Purpose:** Fetch current balance without page reload

**Request:**
```http
GET /ajax/balance HTTP/1.1
X-Requested-With: XMLHttpRequest
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "balance": "2345.50",
  "income": "3500.00",
  "expenses": "1154.50"
}
```

**JavaScript Usage:**
```javascript
fetch('/ajax/balance')
  .then(response => response.json())
  .then(data => {
    document.getElementById('balance').textContent = `$${data.balance}`;
  });
```

---

### 5.2 Category Spending Chart Data

#### **GET /ajax/category-breakdown**

**Request:**
```http
GET /ajax/category-breakdown?month=2&year=2026 HTTP/1.1
X-Requested-With: XMLHttpRequest
Cookie: session=xyz789...
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "labels": ["Food & Dining", "Transportation", "Housing"],
  "data": [320.00, 150.00, 1200.00],
  "colors": ["#FF6384", "#36A2EB", "#FFCE56"]
}
```

**Chart.js Usage:**
```javascript
fetch('/ajax/category-breakdown?month=2&year=2026')
  .then(response => response.json())
  .then(data => {
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.data,
          backgroundColor: data.colors
        }]
      }
    });
  });
```

---

## 6. Security Considerations

### 6.1 CSRF Protection

**All POST/PUT/DELETE requests require CSRF token:**

```html
<form method="POST" action="/transactions/add">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <!-- Other fields -->
</form>
```

**Flask-WTF Configuration:**
```python
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No expiration
```

### 6.2 Authorization Checks

**Every route verifies user ownership:**

```python
@app.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Authorization check
    if transaction.user_id != current_user.id:
        abort(403)  # Forbidden
    
    # Proceed with edit logic
```

### 6.3 Input Validation

**Server-side validation (never trust client):**

```python
class TransactionForm(FlaskForm):
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be positive')
    ])
    date = DateField('Date', validators=[
        DataRequired(),
        validate_not_future  # Custom validator
    ])
```

---

## 7. API Versioning Strategy (Future)

### 7.1 URL Versioning

**Format:** `/api/v{version}/resource`

**Example:**
- v1: `/api/v1/transactions`
- v2: `/api/v2/transactions` (breaking changes)

### 7.2 Deprecation Policy

1. **Announce:** 3 months before deprecation
2. **Warn:** Add `X-API-Deprecated: true` header
3. **Sunset:** Remove after 6 months

**Example Header:**
```http
X-API-Deprecated: true
X-API-Sunset-Date: 2026-08-20
X-API-Migration-Guide: https://docs.swiftbudget.com/api/v2-migration
```

---

## 8. Documentation & Testing

### 8.1 API Documentation (Future)

**Tool:** Swagger/OpenAPI 3.0

**Endpoint:** `/api/docs`

**Features:**
- Interactive API explorer
- Request/response examples
- Authentication testing

### 8.2 Postman Collection

**Export:** JSON collection for all endpoints

**Includes:**
- Pre-configured requests
- Environment variables (base_url, auth_token)
- Test scripts

---

## 9. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial API specification |

**Next Document:** Deployment & Infrastructure Document
