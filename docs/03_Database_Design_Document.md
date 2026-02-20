# SwiftBudget - Database Design Document (DDD)

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Database:** PostgreSQL 14+  
**Hosting:** Supabase / ElephantSQL (Free Tier)

---

## 1. Database Overview

### 1.1 Purpose
This document defines the complete database schema for SwiftBudget, including tables, relationships, constraints, indexes, and data types. The design prioritizes **data integrity**, **ACID compliance**, and **query performance** for financial transactions.

### 1.2 Database Selection Rationale

**PostgreSQL vs. NoSQL Comparison:**

| Criteria | PostgreSQL | MongoDB | Decision |
|----------|-----------|---------|----------|
| **ACID Compliance** | ✅ Full (critical for money) | ⚠️ Partial | PostgreSQL |
| **Data Integrity** | ✅ Foreign keys, constraints | ❌ App-level only | PostgreSQL |
| **Numeric Precision** | ✅ NUMERIC type (exact) | ❌ Double (rounding errors) | PostgreSQL |
| **Complex Queries** | ✅ JOINs, aggregations | ⚠️ Requires denormalization | PostgreSQL |
| **Transaction Support** | ✅ Multi-table transactions | ⚠️ Limited | PostgreSQL |
| **Free Tier** | ✅ 500MB (Supabase) | ✅ 512MB (Atlas) | Tie |

**Verdict:** PostgreSQL is non-negotiable for financial applications where losing or corrupting a transaction is unacceptable.

### 1.3 Normalization Strategy

**Target:** Third Normal Form (3NF)

**Benefits:**
- Eliminate data redundancy (e.g., category name stored once)
- Ensure update anomalies don't occur (changing category name updates one row)
- Maintain referential integrity via foreign keys

**Trade-offs:**
- Requires JOINs for queries (acceptable for <10,000 transactions/user)
- Slightly more complex queries (mitigated by SQLAlchemy ORM)

---

## 2. Entity-Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS TABLE                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ PK: id (SERIAL)                                        │     │
│  │ username (VARCHAR(80), UNIQUE, NOT NULL)               │     │
│  │ email (VARCHAR(120), UNIQUE, NOT NULL)                 │     │
│  │ password_hash (VARCHAR(255), NOT NULL)                 │     │
│  │ created_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  │ updated_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  └────────────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ 1:N (One user has many categories)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CATEGORIES TABLE                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ PK: id (SERIAL)                                        │     │
│  │ FK: user_id (INTEGER, REFERENCES users.id)             │     │
│  │ name (VARCHAR(50), NOT NULL)                           │     │
│  │ is_default (BOOLEAN, DEFAULT FALSE)                    │     │
│  │ created_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  │ UNIQUE(user_id, name) -- No duplicate category names   │     │
│  └────────────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ 1:N (One category has many transactions)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTIONS TABLE                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ PK: id (SERIAL)                                        │     │
│  │ FK: user_id (INTEGER, REFERENCES users.id)             │     │
│  │ FK: category_id (INTEGER, REFERENCES categories.id)    │     │
│  │ amount (NUMERIC(10,2), NOT NULL, CHECK > 0)            │     │
│  │ description (VARCHAR(200))                             │     │
│  │ transaction_date (DATE, NOT NULL)                      │     │
│  │ type (VARCHAR(10), CHECK IN ('income', 'expense'))     │     │
│  │ is_deleted (BOOLEAN, DEFAULT FALSE) -- Soft delete     │     │
│  │ created_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  │ updated_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    BUDGET_GOALS TABLE (Should Have)              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ PK: id (SERIAL)                                        │     │
│  │ FK: user_id (INTEGER, REFERENCES users.id)             │     │
│  │ FK: category_id (INTEGER, REFERENCES categories.id)    │     │
│  │ amount (NUMERIC(10,2), NOT NULL, CHECK > 0)            │     │
│  │ period (VARCHAR(20), DEFAULT 'monthly')                │     │
│  │ start_date (DATE, NOT NULL)                            │     │
│  │ end_date (DATE)                                        │     │
│  │ is_active (BOOLEAN, DEFAULT TRUE)                      │     │
│  │ created_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  │ UNIQUE(user_id, category_id, period) -- One goal/cat   │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              NOTIFICATION_PREFERENCES TABLE (Should Have)        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ PK: id (SERIAL)                                        │     │
│  │ FK: user_id (INTEGER, REFERENCES users.id, UNIQUE)     │     │
│  │ email_enabled (BOOLEAN, DEFAULT TRUE)                  │     │
│  │ budget_alerts (BOOLEAN, DEFAULT TRUE)                  │     │
│  │ weekly_summary (BOOLEAN, DEFAULT TRUE)                 │     │
│  │ alert_threshold (INTEGER, DEFAULT 80) -- % of budget   │     │
│  │ created_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  │ updated_at (TIMESTAMP, DEFAULT NOW())                  │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

**Relationship Summary:**
- **Users ↔ Categories**: 1:N (One user owns many categories)
- **Users ↔ Transactions**: 1:N (One user has many transactions)
- **Categories ↔ Transactions**: 1:N (One category contains many transactions)
- **Users ↔ BudgetGoals**: 1:N (One user sets many budget goals)
- **Categories ↔ BudgetGoals**: 1:N (One category can have multiple goals for different periods)

---

## 3. Table Specifications

### 3.1 USERS Table

**Purpose:** Store user account information and authentication credentials.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing user ID |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL | Unique username (3-80 chars) |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Email address (validated format) |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
```

**Sample Data:**
```sql
INSERT INTO users (username, email, password_hash) VALUES
('john_doe', 'john@example.com', '$2b$12$KIXxLhashed...'),
('jane_smith', 'jane@example.com', '$2b$12$ABCxLhashed...');
```

**Business Rules:**
- Username must be 3-80 characters (enforced at application level)
- Email must match regex pattern (enforced by Flask-WTF)
- Password must be hashed with bcrypt (cost factor 12)
- Soft delete: Add `is_active` column if user deactivation needed (future)

---

### 3.2 CATEGORIES Table

**Purpose:** Store expense/income categories (both default and user-created).

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing category ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id), NOT NULL | Owner of the category |
| `name` | VARCHAR(50) | NOT NULL | Category name (e.g., "Food") |
| `is_default` | BOOLEAN | DEFAULT FALSE | System category vs. user-created |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Indexes:**
```sql
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE UNIQUE INDEX idx_categories_user_name ON categories(user_id, name);
```

**Constraints:**
```sql
ALTER TABLE categories 
ADD CONSTRAINT fk_categories_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE categories
ADD CONSTRAINT unique_user_category UNIQUE(user_id, name);
```

**Default Categories (Seeded on User Registration):**
```sql
-- Inserted automatically when user signs up
INSERT INTO categories (user_id, name, is_default) VALUES
(1, 'Food & Dining', TRUE),
(1, 'Transportation', TRUE),
(1, 'Housing (Rent/Mortgage)', TRUE),
(1, 'Utilities', TRUE),
(1, 'Entertainment', TRUE),
(1, 'Healthcare', TRUE),
(1, 'Shopping', TRUE),
(1, 'Income', TRUE),
(1, 'Other', TRUE);
```

**Business Rules:**
- Each user must have at least one category (enforced at app level)
- Default categories cannot be deleted (check `is_default = TRUE`)
- Category names are case-insensitive unique per user

---

### 3.3 TRANSACTIONS Table

**Purpose:** Store all income and expense transactions.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing transaction ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id), NOT NULL | Transaction owner |
| `category_id` | INTEGER | FOREIGN KEY (categories.id), NOT NULL | Associated category |
| `amount` | NUMERIC(10,2) | NOT NULL, CHECK (amount > 0) | Transaction amount (2 decimal places) |
| `description` | VARCHAR(200) | NULL | Optional description |
| `transaction_date` | DATE | NOT NULL | Date of transaction |
| `type` | VARCHAR(10) | CHECK IN ('income', 'expense') | Transaction type |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | Soft delete flag |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update time |

**Indexes:**
```sql
-- Composite index for common query (user's transactions by date)
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);

-- Index for category filtering
CREATE INDEX idx_transactions_category ON transactions(category_id);

-- Index for soft delete queries
CREATE INDEX idx_transactions_active ON transactions(user_id, is_deleted) WHERE is_deleted = FALSE;
```

**Constraints:**
```sql
ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE transactions 
ADD CONSTRAINT fk_transactions_category 
FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;

ALTER TABLE transactions
ADD CONSTRAINT chk_amount_positive CHECK (amount > 0);

ALTER TABLE transactions
ADD CONSTRAINT chk_type_valid CHECK (type IN ('income', 'expense'));

ALTER TABLE transactions
ADD CONSTRAINT chk_date_not_future CHECK (transaction_date <= CURRENT_DATE);
```

**Sample Data:**
```sql
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, type) VALUES
(1, 1, 45.50, 'Grocery shopping at Walmart', '2026-02-15', 'expense'),
(1, 8, 3500.00, 'Monthly salary', '2026-02-01', 'income'),
(1, 3, 1200.00, 'Rent payment', '2026-02-01', 'expense');
```

**Business Rules:**
- Amount must be positive (negative values not allowed; type determines income/expense)
- Transaction date cannot be in the future (enforced at DB level)
- Soft delete: Set `is_deleted = TRUE` instead of DELETE (audit trail)
- ON DELETE CASCADE for user (if user deleted, remove all transactions)
- ON DELETE RESTRICT for category (prevent deleting category with transactions)

**Why NUMERIC(10,2) instead of FLOAT?**
```sql
-- FLOAT has rounding errors (BAD for money)
SELECT 0.1 + 0.2;  -- Returns 0.30000000000000004

-- NUMERIC is exact (GOOD for money)
SELECT 0.1::NUMERIC + 0.2::NUMERIC;  -- Returns 0.3
```

---

### 3.4 BUDGET_GOALS Table (Should Have)

**Purpose:** Store user-defined spending limits per category.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing goal ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id), NOT NULL | Goal owner |
| `category_id` | INTEGER | FOREIGN KEY (categories.id), NOT NULL | Target category |
| `amount` | NUMERIC(10,2) | NOT NULL, CHECK (amount > 0) | Budget limit |
| `period` | VARCHAR(20) | DEFAULT 'monthly' | Budget period (monthly/weekly/yearly) |
| `start_date` | DATE | NOT NULL | Budget start date |
| `end_date` | DATE | NULL | Budget end date (NULL = ongoing) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active/inactive flag |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Indexes:**
```sql
CREATE INDEX idx_budget_goals_user ON budget_goals(user_id);
CREATE UNIQUE INDEX idx_budget_goals_unique ON budget_goals(user_id, category_id, period) 
WHERE is_active = TRUE;
```

**Constraints:**
```sql
ALTER TABLE budget_goals
ADD CONSTRAINT fk_budget_goals_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE budget_goals
ADD CONSTRAINT fk_budget_goals_category 
FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE;

ALTER TABLE budget_goals
ADD CONSTRAINT chk_budget_amount_positive CHECK (amount > 0);

ALTER TABLE budget_goals
ADD CONSTRAINT chk_budget_period CHECK (period IN ('weekly', 'monthly', 'yearly'));
```

**Sample Data:**
```sql
INSERT INTO budget_goals (user_id, category_id, amount, period, start_date) VALUES
(1, 1, 500.00, 'monthly', '2026-02-01'),  -- $500/month for Food
(1, 5, 200.00, 'monthly', '2026-02-01');  -- $200/month for Entertainment
```

**Business Rules:**
- Only one active budget goal per (user, category, period) combination
- If `end_date` is NULL, budget is ongoing
- Alerts triggered when spending reaches `alert_threshold` (from notification_preferences)

---

### 3.5 NOTIFICATION_PREFERENCES Table (Should Have)

**Purpose:** Store user preferences for email notifications.

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing preference ID |
| `user_id` | INTEGER | FOREIGN KEY (users.id), UNIQUE, NOT NULL | User reference |
| `email_enabled` | BOOLEAN | DEFAULT TRUE | Master email toggle |
| `budget_alerts` | BOOLEAN | DEFAULT TRUE | Budget threshold alerts |
| `weekly_summary` | BOOLEAN | DEFAULT TRUE | Weekly spending summary |
| `alert_threshold` | INTEGER | DEFAULT 80 | % of budget to trigger alert (0-100) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_notification_prefs_user ON notification_preferences(user_id);
```

**Constraints:**
```sql
ALTER TABLE notification_preferences
ADD CONSTRAINT fk_notification_prefs_user 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE notification_preferences
ADD CONSTRAINT chk_alert_threshold CHECK (alert_threshold BETWEEN 0 AND 100);
```

**Sample Data:**
```sql
-- Automatically created when user registers
INSERT INTO notification_preferences (user_id, email_enabled, budget_alerts, weekly_summary, alert_threshold) 
VALUES (1, TRUE, TRUE, TRUE, 80);
```

**Business Rules:**
- Created automatically on user registration with default values
- If `email_enabled = FALSE`, no emails sent regardless of other settings
- `alert_threshold` determines when budget alerts fire (e.g., 80% = alert at $400 of $500 budget)

---

## 4. Data Types & Precision

### 4.1 Numeric Types for Currency

**DO NOT USE:**
```sql
-- FLOAT/REAL - Subject to rounding errors
amount FLOAT  -- BAD: 0.1 + 0.2 = 0.30000000000000004
```

**USE:**
```sql
-- NUMERIC(precision, scale) - Exact decimal arithmetic
amount NUMERIC(10, 2)  -- GOOD: Stores up to 99,999,999.99
```

**Precision Breakdown:**
- `NUMERIC(10, 2)` = 10 total digits, 2 after decimal
- Max value: 99,999,999.99 (sufficient for personal budgets)
- Storage: 8 bytes (efficient)

### 4.2 String Types

| Use Case | Type | Reason |
|----------|------|--------|
| **Username** | VARCHAR(80) | Variable length, max 80 chars |
| **Email** | VARCHAR(120) | Standard email max length |
| **Password Hash** | VARCHAR(255) | Bcrypt output is 60 chars, but allow buffer |
| **Description** | VARCHAR(200) | Short text, indexed |
| **Category Name** | VARCHAR(50) | Short labels |

**Why VARCHAR over TEXT?**
- VARCHAR can be indexed more efficiently
- Enforces max length at DB level
- TEXT is for long-form content (not needed here)

### 4.3 Date/Time Types

| Column | Type | Reason |
|--------|------|--------|
| `transaction_date` | DATE | No time component needed (day-level precision) |
| `created_at` | TIMESTAMP | Full date + time for audit trail |
| `updated_at` | TIMESTAMP | Track last modification time |

**Timezone Handling:**
- Store all timestamps in UTC (PostgreSQL default)
- Convert to user's timezone in application layer (Flask)

---

## 5. Constraints & Validation

### 5.1 Primary Keys

**Strategy:** Use `SERIAL` (auto-incrementing integers)

```sql
id SERIAL PRIMARY KEY
-- Equivalent to:
id INTEGER NOT NULL DEFAULT nextval('table_name_id_seq') PRIMARY KEY
```

**Why SERIAL over UUID?**
- Smaller storage (4 bytes vs. 16 bytes)
- Better index performance (sequential integers)
- Simpler for debugging (id=1, id=2 vs. random UUIDs)
- UUID only needed for distributed systems (not applicable here)

### 5.2 Foreign Keys

**Cascade Rules:**

| Relationship | ON DELETE | Reason |
|--------------|-----------|--------|
| `transactions.user_id` | CASCADE | Delete user → delete all transactions |
| `transactions.category_id` | RESTRICT | Prevent deleting category with transactions |
| `categories.user_id` | CASCADE | Delete user → delete all categories |
| `budget_goals.user_id` | CASCADE | Delete user → delete all goals |

**Example:**
```sql
ALTER TABLE transactions
ADD CONSTRAINT fk_transactions_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### 5.3 Check Constraints

**Purpose:** Enforce business rules at database level.

```sql
-- Amount must be positive
ALTER TABLE transactions
ADD CONSTRAINT chk_amount_positive CHECK (amount > 0);

-- Transaction type must be valid
ALTER TABLE transactions
ADD CONSTRAINT chk_type_valid CHECK (type IN ('income', 'expense'));

-- Date cannot be in future
ALTER TABLE transactions
ADD CONSTRAINT chk_date_not_future CHECK (transaction_date <= CURRENT_DATE);

-- Alert threshold must be 0-100
ALTER TABLE notification_preferences
ADD CONSTRAINT chk_alert_threshold CHECK (alert_threshold BETWEEN 0 AND 100);
```

### 5.4 Unique Constraints

```sql
-- Username must be unique
ALTER TABLE users ADD CONSTRAINT unique_username UNIQUE(username);

-- Email must be unique
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE(email);

-- Category name unique per user
ALTER TABLE categories ADD CONSTRAINT unique_user_category UNIQUE(user_id, name);

-- One active budget goal per (user, category, period)
CREATE UNIQUE INDEX idx_budget_goals_unique 
ON budget_goals(user_id, category_id, period) 
WHERE is_active = TRUE;
```

---

## 6. Indexes & Query Optimization

### 6.1 Index Strategy

**Principle:** Index columns used in WHERE, JOIN, and ORDER BY clauses.

**Primary Indexes:**
```sql
-- Users table
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Categories table
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE UNIQUE INDEX idx_categories_user_name ON categories(user_id, name);

-- Transactions table (MOST IMPORTANT)
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_active ON transactions(user_id, is_deleted) WHERE is_deleted = FALSE;

-- Budget goals table
CREATE INDEX idx_budget_goals_user ON budget_goals(user_id);
CREATE UNIQUE INDEX idx_budget_goals_unique ON budget_goals(user_id, category_id, period) WHERE is_active = TRUE;
```

### 6.2 Composite Index Rationale

**Query Pattern:**
```sql
-- Common query: Get user's transactions for current month
SELECT * FROM transactions
WHERE user_id = 1
  AND transaction_date BETWEEN '2026-02-01' AND '2026-02-28'
  AND is_deleted = FALSE
ORDER BY transaction_date DESC;
```

**Optimal Index:**
```sql
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
```

**Why this order?**
1. Filter by `user_id` first (high selectivity)
2. Then filter by `transaction_date` (range scan)
3. DESC order matches ORDER BY clause (no sort needed)

### 6.3 Partial Indexes

**Use Case:** Soft deletes (most queries exclude deleted records)

```sql
CREATE INDEX idx_transactions_active 
ON transactions(user_id, is_deleted) 
WHERE is_deleted = FALSE;
```

**Benefit:** Smaller index (only active transactions), faster queries.

### 6.4 Index Maintenance

**Monitoring:**
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

**Unused indexes:** If `idx_scan = 0` after 1 month, consider dropping.

---

## 7. Sample Queries

### 7.1 User Registration

```sql
-- Insert new user
INSERT INTO users (username, email, password_hash)
VALUES ('alice', 'alice@example.com', '$2b$12$hashed...')
RETURNING id;

-- Create default categories for new user (user_id = 3)
INSERT INTO categories (user_id, name, is_default)
VALUES 
  (3, 'Food & Dining', TRUE),
  (3, 'Transportation', TRUE),
  (3, 'Housing (Rent/Mortgage)', TRUE),
  (3, 'Utilities', TRUE),
  (3, 'Entertainment', TRUE),
  (3, 'Healthcare', TRUE),
  (3, 'Shopping', TRUE),
  (3, 'Income', TRUE),
  (3, 'Other', TRUE);

-- Create default notification preferences
INSERT INTO notification_preferences (user_id)
VALUES (3);
```

### 7.2 Add Transaction

```sql
INSERT INTO transactions (user_id, category_id, amount, description, transaction_date, type)
VALUES (1, 1, 45.50, 'Lunch at Chipotle', '2026-02-20', 'expense')
RETURNING id, amount, description;
```

### 7.3 Calculate Current Balance

```sql
-- Total balance (income - expenses)
SELECT 
  COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS total_income,
  COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS total_expenses,
  COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0) AS balance
FROM transactions
WHERE user_id = 1 AND is_deleted = FALSE;
```

### 7.4 Monthly Category Breakdown

```sql
-- Spending by category for February 2026
SELECT 
  c.name AS category,
  SUM(t.amount) AS total_spent,
  COUNT(t.id) AS transaction_count
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1
  AND t.type = 'expense'
  AND t.is_deleted = FALSE
  AND t.transaction_date >= '2026-02-01'
  AND t.transaction_date < '2026-03-01'
GROUP BY c.name
ORDER BY total_spent DESC;
```

### 7.5 Budget Alert Check

```sql
-- Find categories exceeding 80% of budget
SELECT 
  c.name AS category,
  bg.amount AS budget_limit,
  COALESCE(SUM(t.amount), 0) AS current_spending,
  ROUND((COALESCE(SUM(t.amount), 0) / bg.amount) * 100, 2) AS percent_used
FROM budget_goals bg
JOIN categories c ON bg.category_id = c.id
LEFT JOIN transactions t ON t.category_id = c.id
  AND t.type = 'expense'
  AND t.is_deleted = FALSE
  AND t.transaction_date >= bg.start_date
  AND (bg.end_date IS NULL OR t.transaction_date <= bg.end_date)
WHERE bg.user_id = 1
  AND bg.is_active = TRUE
  AND bg.period = 'monthly'
  AND t.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY c.name, bg.amount
HAVING (COALESCE(SUM(t.amount), 0) / bg.amount) >= 0.80
ORDER BY percent_used DESC;
```

### 7.6 Recent Transactions (Dashboard)

```sql
-- Last 10 transactions for user
SELECT 
  t.id,
  t.amount,
  t.description,
  t.transaction_date,
  t.type,
  c.name AS category
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.user_id = 1 AND t.is_deleted = FALSE
ORDER BY t.transaction_date DESC, t.created_at DESC
LIMIT 10;
```

---

## 8. Data Migration & Seeding

### 8.1 Initial Schema Creation (via Flask-Migrate)

```bash
# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial schema: users, categories, transactions"

# Apply migration
flask db upgrade
```

**Generated Migration File:**
```python
# migrations/versions/001_initial_schema.py
def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(80), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='unique_user_category')
    )
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('type', sa.String(10), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='chk_amount_positive'),
        sa.CheckConstraint("type IN ('income', 'expense')", name='chk_type_valid'),
        sa.CheckConstraint('transaction_date <= CURRENT_DATE', name='chk_date_not_future')
    )
    
    # Create indexes
    op.create_index('idx_transactions_user_date', 'transactions', ['user_id', 'transaction_date'], postgresql_ops={'transaction_date': 'DESC'})
```

### 8.2 Seed Data (Default Categories)

```python
# app/seeds.py
def seed_default_categories(user_id):
    """Create default categories for a new user."""
    default_categories = [
        'Food & Dining',
        'Transportation',
        'Housing (Rent/Mortgage)',
        'Utilities',
        'Entertainment',
        'Healthcare',
        'Shopping',
        'Income',
        'Other'
    ]
    
    for category_name in default_categories:
        category = Category(
            user_id=user_id,
            name=category_name,
            is_default=True
        )
        db.session.add(category)
    
    db.session.commit()
```

---

## 9. Backup & Recovery Strategy

### 9.1 Supabase Automatic Backups

**Free Tier:**
- Daily backups (retained for 7 days)
- Point-in-time recovery (PITR) not available on free tier

**Backup Schedule:**
- Automatic daily backups at 2 AM UTC
- Manual backups via Supabase dashboard

### 9.2 Manual Backup (pg_dump)

```bash
# Backup entire database
pg_dump -h db.supabase.co -U postgres -d swiftbudget > backup_2026-02-20.sql

# Backup specific tables
pg_dump -h db.supabase.co -U postgres -d swiftbudget -t users -t transactions > backup_critical.sql

# Restore from backup
psql -h db.supabase.co -U postgres -d swiftbudget < backup_2026-02-20.sql
```

### 9.3 Data Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| **Active Transactions** | Indefinite | User's financial history |
| **Deleted Transactions** | 90 days | Soft delete recovery window |
| **User Accounts** | Until user requests deletion | GDPR compliance |
| **Audit Logs** | 1 year (future) | Security monitoring |

---

## 10. Performance Benchmarks

### 10.1 Expected Query Performance

| Query | Expected Time | Optimization |
|-------|---------------|--------------|
| User login | < 50ms | Index on `username` |
| Dashboard load (10 transactions) | < 100ms | Composite index on `(user_id, date)` |
| Monthly category breakdown | < 200ms | Aggregation with index |
| Add transaction | < 50ms | Single INSERT with index update |
| Budget alert check | < 300ms | JOINs with indexes |

### 10.2 Scalability Limits (Free Tier)

| Metric | Limit | Mitigation |
|--------|-------|------------|
| **Database Size** | 500MB | ~5,000 transactions/user (100 users) |
| **Concurrent Connections** | 60 | **CRITICAL: See section 10.3** |
| **Query Timeout** | 30 seconds | Pagination, query optimization |

**When to Upgrade:**
- Database size > 400MB (80% capacity)
- Frequent connection errors
- Query times > 1 second

### 10.3 Connection Pooling (CRITICAL for Free Tier)

**The Problem:**
Supabase and ElephantSQL free tiers have a **strict 60 concurrent connection limit**. Flask creates a new database connection for **every request** by default, which can quickly exhaust this limit, especially with:
- Multiple users browsing simultaneously
- Background workers (APScheduler for recurring transactions)
- Long-running requests
- Connection leaks

**Symptom:**
```
OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections
```

**Solution: Configure SQLAlchemy Connection Pooling**

**Option 1: NullPool (Recommended for Free Tier)**
```python
# config.py
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # CRITICAL: Use NullPool to avoid connection exhaustion
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool,  # No connection pooling
        'pool_pre_ping': True,  # Verify connections before use
    }
```

**Why NullPool?**
- Opens connection only when needed
- Closes connection immediately after request
- Prevents connection leaks
- Ideal for free-tier limits (60 connections)

**Trade-off:** Slightly slower (reconnects every request), but avoids "too many connections" errors.

---

**Option 2: Small Pool Size (Alternative)**
```python
# config.py
from sqlalchemy.pool import QueuePool

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Small pool for free tier
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': QueuePool,
        'pool_size': 5,          # Max 5 persistent connections
        'max_overflow': 10,      # Allow 10 extra connections if needed
        'pool_recycle': 3600,    # Recycle connections every hour
        'pool_pre_ping': True,   # Verify connections before use
        'pool_timeout': 30,      # Wait 30s for available connection
    }
```

**Calculation:**
- Web server (Gunicorn): 4 workers × 5 connections = 20 connections
- Background worker (APScheduler): 2 connections
- Buffer: 10 connections
- **Total: 32 connections** (well under 60 limit)

---

**Option 3: PgBouncer (Advanced - Paid Tier)**
```python
# For production with higher traffic
# Use PgBouncer as connection pooler
DATABASE_URL = "postgresql://user:pass@pgbouncer-host:6432/db"

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 0,  # PgBouncer handles overflow
    'pool_pre_ping': False,  # PgBouncer handles health checks
}
```

---

**Monitoring Connection Usage**

**Query to Check Active Connections:**
```sql
-- Run in Supabase SQL Editor
SELECT 
  count(*) AS total_connections,
  count(*) FILTER (WHERE state = 'active') AS active_connections,
  count(*) FILTER (WHERE state = 'idle') AS idle_connections
FROM pg_stat_activity
WHERE datname = 'postgres';
```

**Flask Logging:**
```python
# app/__init__.py
import logging

logger = logging.getLogger('sqlalchemy.pool')
logger.setLevel(logging.DEBUG)

# Logs will show:
# - Connection pool checkout
# - Connection pool checkin
# - Connection pool overflow
```

---

**Best Practices for Free Tier:**

1. **Use NullPool in Production** (until you upgrade)
2. **Close Sessions Explicitly** (Flask-SQLAlchemy handles this, but verify)
3. **Limit Background Workers** (1-2 APScheduler threads max)
4. **Monitor Connection Count** (set up alerts at 50/60 connections)
5. **Use Connection Timeouts** (prevent hung connections)

**Example: Explicit Session Management**
```python
# app/routes/transactions.py
from app import db

@transactions_bp.route('/add', methods=['POST'])
def add_transaction():
    try:
        # ... transaction logic ...
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Transaction failed: {str(e)}")
    finally:
        db.session.remove()  # Ensure connection released
```

---

**When You Hit Connection Limits:**

**Immediate Fix:**
```bash
# Restart Render service to clear connections
render services restart swiftbudget
```

**Long-Term Fix:**
1. Switch to NullPool
2. Reduce Gunicorn workers (4 → 2)
3. Optimize long-running queries
4. Upgrade to paid tier ($25/month for 200 connections)

---

## 11. Security Considerations

### 11.1 SQL Injection Prevention

**NEVER:**
```python
# BAD: String concatenation (vulnerable)
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)
```

**ALWAYS:**
```python
# GOOD: Parameterized queries (SQLAlchemy ORM)
user = User.query.filter_by(username=username).first()
```

### 11.2 Data Encryption

| Layer | Encryption | Status |
|-------|-----------|--------|
| **In Transit** | TLS 1.3 (HTTPS) | ✅ Enforced |
| **At Rest** | AES-256 (Supabase default) | ✅ Enabled |
| **Passwords** | Bcrypt (cost 12) | ✅ Application-level |

### 11.3 Access Control

**Database User Permissions:**
```sql
-- Application user (limited permissions)
CREATE USER swiftbudget_app WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO swiftbudget_app;
REVOKE DROP, TRUNCATE ON ALL TABLES IN SCHEMA public FROM swiftbudget_app;

-- Admin user (full permissions)
CREATE USER swiftbudget_admin WITH PASSWORD 'admin_password';
GRANT ALL PRIVILEGES ON DATABASE swiftbudget TO swiftbudget_admin;
```

---

## 12. Future Enhancements

### 12.1 Recurring Transactions (Could Have)

**New Table:**
```sql
CREATE TABLE recurring_transactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  description VARCHAR(200),
  frequency VARCHAR(20) CHECK (frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
  start_date DATE NOT NULL,
  end_date DATE,
  is_active BOOLEAN DEFAULT TRUE,
  last_executed DATE,
  next_execution DATE NOT NULL,  -- Calculated field for efficiency
  created_at TIMESTAMP DEFAULT NOW()
);

-- Index for background worker queries
CREATE INDEX idx_recurring_next_execution ON recurring_transactions(next_execution, is_active) 
WHERE is_active = TRUE;
```

**CRITICAL: Update Transactions Table to Track Parent Recurring Transaction**
```sql
-- Add column to transactions table
ALTER TABLE transactions 
ADD COLUMN recurring_transaction_id INTEGER REFERENCES recurring_transactions(id) ON DELETE SET NULL;

-- Index for tracking generated transactions
CREATE INDEX idx_transactions_recurring_parent ON transactions(recurring_transaction_id);
```

**Background Worker Implementation (APScheduler or Cron)**

**Option 1: APScheduler (Recommended for Render.com)**
```python
# app/tasks/recurring_transactions.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.recurring_transaction_service import RecurringTransactionService
import logging

logger = logging.getLogger(__name__)

def process_recurring_transactions():
    """
    Background job to check and spawn recurring transactions.
    Runs daily at 2 AM UTC.
    """
    try:
        logger.info("Starting recurring transaction processing")
        
        # Get all recurring transactions due today
        due_transactions = RecurringTransactionService.get_due_transactions()
        
        for recurring in due_transactions:
            # Spawn new transaction
            transaction = RecurringTransactionService.spawn_transaction(recurring.id)
            
            if transaction:
                logger.info(f"Spawned transaction {transaction.id} from recurring {recurring.id}")
            else:
                logger.error(f"Failed to spawn transaction from recurring {recurring.id}")
        
        logger.info(f"Processed {len(due_transactions)} recurring transactions")
    
    except Exception as e:
        logger.error(f"Error processing recurring transactions: {str(e)}")

# Initialize scheduler
def init_scheduler(app):
    """Initialize APScheduler with Flask app context"""
    scheduler = BackgroundScheduler()
    
    # Run daily at 2 AM UTC
    scheduler.add_job(
        func=lambda: app.app_context().push() or process_recurring_transactions(),
        trigger='cron',
        hour=2,
        minute=0,
        id='process_recurring_transactions',
        name='Process recurring transactions daily',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler started for recurring transactions")
    
    return scheduler
```

**Service Layer Implementation**
```python
# app/services/recurring_transaction_service.py
from datetime import date, timedelta
from app.models import RecurringTransaction, Transaction, db
import logging

logger = logging.getLogger(__name__)

class RecurringTransactionService:
    @staticmethod
    def get_due_transactions():
        """Get all recurring transactions due for execution today"""
        today = date.today()
        
        return RecurringTransaction.query.filter(
            RecurringTransaction.is_active == True,
            RecurringTransaction.next_execution <= today,
            db.or_(
                RecurringTransaction.end_date.is_(None),
                RecurringTransaction.end_date >= today
            )
        ).all()
    
    @staticmethod
    def spawn_transaction(recurring_id):
        """
        Create a new transaction from a recurring transaction.
        Links child to parent via recurring_transaction_id.
        """
        recurring = RecurringTransaction.query.get(recurring_id)
        
        if not recurring or not recurring.is_active:
            return None
        
        try:
            # Create new transaction with parent reference
            transaction = Transaction(
                user_id=recurring.user_id,
                category_id=recurring.category_id,
                amount=recurring.amount,
                description=f"{recurring.description} (Auto-generated)",
                transaction_date=date.today(),
                type='expense',  # Assuming recurring expenses; adjust as needed
                recurring_transaction_id=recurring.id  # CRITICAL: Track parent
            )
            
            db.session.add(transaction)
            
            # Update recurring transaction
            recurring.last_executed = date.today()
            recurring.next_execution = RecurringTransactionService._calculate_next_execution(
                recurring.frequency,
                date.today()
            )
            
            db.session.commit()
            
            logger.info(f"Spawned transaction {transaction.id} from recurring {recurring.id}")
            return transaction
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to spawn transaction: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_next_execution(frequency, current_date):
        """Calculate next execution date based on frequency"""
        if frequency == 'daily':
            return current_date + timedelta(days=1)
        elif frequency == 'weekly':
            return current_date + timedelta(weeks=1)
        elif frequency == 'monthly':
            # Handle month-end edge cases
            next_month = current_date.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=min(current_date.day, 28))
        elif frequency == 'yearly':
            return current_date.replace(year=current_date.year + 1)
        else:
            return current_date + timedelta(days=30)  # Default to monthly
    
    @staticmethod
    def get_generated_transactions(recurring_id):
        """Get all transactions generated from a specific recurring transaction"""
        return Transaction.query.filter_by(
            recurring_transaction_id=recurring_id,
            is_deleted=False
        ).order_by(Transaction.transaction_date.desc()).all()
```

**Option 2: Render Cron Job (Alternative)**
```yaml
# render.yaml
services:
  - type: web
    name: swiftbudget
    # ... existing config ...

  - type: cron
    name: recurring-transactions-cron
    env: python
    schedule: "0 2 * * *"  # Daily at 2 AM UTC
    buildCommand: pip install -r requirements.txt
    startCommand: python -c "from app.tasks.recurring_transactions import process_recurring_transactions; process_recurring_transactions()"
```

**Benefits of Parent Tracking (`recurring_transaction_id`):**
1. **Audit Trail**: See which transactions were auto-generated
2. **Bulk Operations**: Delete all generated transactions if recurring rule changes
3. **Reporting**: Separate manual vs. auto-generated transactions
4. **Debugging**: Track down issues with specific recurring rules

**Example Query: View All Auto-Generated Transactions**
```sql
SELECT 
  t.id,
  t.amount,
  t.description,
  t.transaction_date,
  rt.frequency,
  rt.description AS recurring_rule
FROM transactions t
JOIN recurring_transactions rt ON t.recurring_transaction_id = rt.id
WHERE t.user_id = 1
ORDER BY t.transaction_date DESC;
```

### 12.2 Shared Budgets (PayJungle Integration)

**New Tables:**
```sql
CREATE TABLE households (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE household_members (
  id SERIAL PRIMARY KEY,
  household_id INTEGER REFERENCES households(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(20) CHECK (role IN ('owner', 'member')),
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(household_id, user_id)
);

CREATE TABLE shared_transactions (
  id SERIAL PRIMARY KEY,
  household_id INTEGER REFERENCES households(id) ON DELETE CASCADE,
  payer_user_id INTEGER REFERENCES users(id),
  amount NUMERIC(10,2) NOT NULL,
  description VARCHAR(200),
  transaction_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 12.3 Audit Trail (Compliance)

**New Table:**
```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  table_name VARCHAR(50) NOT NULL,
  record_id INTEGER NOT NULL,
  action VARCHAR(20) CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_values JSONB,
  new_values JSONB,
  ip_address INET,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Trigger:**
```sql
-- Auto-log all transaction changes
CREATE TRIGGER audit_transactions
AFTER INSERT OR UPDATE OR DELETE ON transactions
FOR EACH ROW EXECUTE FUNCTION log_audit();
```

---

## 13. Database Diagram (Visual)

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE SCHEMA OVERVIEW                      │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │    USERS     │
                         │──────────────│
                         │ PK: id       │
                         │ username     │
                         │ email        │
                         │ password_hash│
                         └──────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ CATEGORIES │  │TRANSACTIONS│  │BUDGET_GOALS│
       │────────────│  │────────────│  │────────────│
       │ PK: id     │  │ PK: id     │  │ PK: id     │
       │ FK: user_id│  │ FK: user_id│  │ FK: user_id│
       │ name       │  │ FK: cat_id │  │ FK: cat_id │
       │ is_default │  │ amount     │  │ amount     │
       └────────────┘  │ description│  │ period     │
                       │ date       │  └────────────┘
                       │ type       │
                       └────────────┘

                         ┌──────────────┐
                         │NOTIFICATION_ │
                         │ PREFERENCES  │
                         │──────────────│
                         │ PK: id       │
                         │ FK: user_id  │
                         │ email_enabled│
                         │ budget_alerts│
                         └──────────────┘
```

---

## 14. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial DDD creation |

**Next Document:** API Specification Document
