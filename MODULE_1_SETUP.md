# Module 1: Project Structure & Configuration Setup

## ✅ Completed Tasks

- [x] Created project directory structure
- [x] Set up `.gitignore` for Python/Flask projects
- [x] Created `.env.example` template
- [x] Created `requirements.txt` with all dependencies
- [x] Created `config.py` with development/testing/production configs
- [x] Created Flask application factory (`app/__init__.py`)
- [x] Created application entry point (`run.py`)
- [x] Created placeholder packages (models, routes, services)
- [x] Created base HTML template
- [x] Created test configuration and fixtures
- [x] Created initial tests for config and app factory

## 📁 Project Structure

```
Budgeting Application/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── models/
│   │   └── __init__.py      # Models package (empty for now)
│   ├── routes/
│   │   └── __init__.py      # Routes package (empty for now)
│   ├── services/
│   │   └── __init__.py      # Services package (empty for now)
│   └── templates/
│       └── base.html        # Base HTML template
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_config.py       # Configuration tests
│   └── test_app_factory.py # App factory tests
├── docs/                    # System documentation (already created)
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── config.py                # Configuration classes
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── DEVELOPMENT_LOG.md       # Development progress tracker
└── README.md                # Project README
```

## 🚀 Setup Instructions

### Step 1: Create Virtual Environment

```bash
# Navigate to project directory
cd "C:\Users\nkeit\OneDrive\Desktop\Python\Budgeting Application"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
# source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Expected output:** All packages should install without errors.

### Step 3: Create Environment File

```bash
# Copy .env.example to .env
copy .env.example .env

# Edit .env with your settings
# For now, you can use the default values for local development
```

**Minimum required changes in `.env`:**
- `SECRET_KEY`: Change to a random string (for development, any string works)
- `DATABASE_URL`: If you have PostgreSQL installed locally, update this. Otherwise, we'll use SQLite for testing.

**For local development without PostgreSQL:**
```
DATABASE_URL=sqlite:///swiftbudget_dev.db
```

### Step 4: Create Logs Directory

```bash
# Create logs directory
mkdir logs
```

### Step 5: Test the Application

#### Test 1: Run Configuration Tests

```bash
# Run configuration tests
pytest tests/test_config.py -v
```

**Expected output:**
```
tests/test_config.py::TestDevelopmentConfig::test_debug_enabled PASSED
tests/test_config.py::TestDevelopmentConfig::test_testing_disabled PASSED
tests/test_config.py::TestDevelopmentConfig::test_sql_echo_enabled PASSED
tests/test_config.py::TestTestingConfig::test_testing_enabled PASSED
tests/test_config.py::TestTestingConfig::test_debug_disabled PASSED
tests/test_config.py::TestTestingConfig::test_sqlite_database PASSED
tests/test_config.py::TestTestingConfig::test_csrf_disabled PASSED
tests/test_config.py::TestProductionConfig::test_debug_disabled PASSED
tests/test_config.py::TestProductionConfig::test_testing_disabled PASSED
tests/test_config.py::TestProductionConfig::test_session_cookie_secure PASSED
tests/test_config.py::TestProductionConfig::test_nullpool_configured PASSED

11 passed
```

#### Test 2: Run App Factory Tests

```bash
# Run app factory tests
pytest tests/test_app_factory.py -v
```

**Expected output:**
```
tests/test_app_factory.py::TestAppFactory::test_create_app_development PASSED
tests/test_app_factory.py::TestAppFactory::test_create_app_testing PASSED
tests/test_app_factory.py::TestAppFactory::test_create_app_production PASSED
tests/test_app_factory.py::TestAppFactory::test_extensions_initialized PASSED
tests/test_app_factory.py::TestAppFactory::test_error_handlers_registered PASSED
tests/test_app_factory.py::TestAppFactory::test_logging_configured PASSED

6 passed
```

#### Test 3: Run All Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term
```

**Expected output:**
```
17 passed

---------- coverage: platform win32, python 3.x.x -----------
Name                     Stmts   Miss  Cover
--------------------------------------------
app/__init__.py             XX     XX    XX%
config.py                   XX     XX    XX%
--------------------------------------------
TOTAL                       XX     XX    XX%
```

#### Test 4: Start Flask Application

```bash
# Set Flask app environment variable (Windows)
set FLASK_APP=run.py
set FLASK_ENV=development

# On macOS/Linux:
# export FLASK_APP=run.py
# export FLASK_ENV=development

# Run Flask development server
python run.py
```

**Expected output:**
```
 * Serving Flask app 'run.py'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

#### Test 5: Verify Flask App Running

Open browser and navigate to: `http://localhost:5000`

**Expected result:** You should see a 404 error page (this is correct - we haven't created any routes yet).

The error should be logged in `logs/swiftbudget.log`.

## ✅ Module 1 Completion Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] `.env` file created with basic configuration
- [ ] Logs directory created
- [ ] Configuration tests pass (11/11)
- [ ] App factory tests pass (6/6)
- [ ] Flask application starts without errors
- [ ] Logging works (check `logs/swiftbudget.log`)
- [ ] 404 error handler works (visit non-existent route)

## 🎯 Success Criteria

**Module 1 is complete when:**
1. ✅ All tests pass (17/17)
2. ✅ Flask application starts without errors
3. ✅ Configuration loads correctly for all environments
4. ✅ Extensions (SQLAlchemy, Flask-Login, etc.) initialize properly
5. ✅ Logging system works
6. ✅ Error handlers registered

## 📝 Key Design Decisions Explained

### 1. Application Factory Pattern
**Why?** Allows creating multiple app instances (dev, test, prod) with different configs. Essential for testing.

### 2. Separate Configuration Classes
**Why?** Different settings for development (debug on, SQL logging) vs production (debug off, HTTPS required).

### 3. NullPool for Production
**Why?** Supabase free tier has 60 connection limit. NullPool opens/closes connections per request, preventing exhaustion.

### 4. Environment Variables
**Why?** Secrets (database URL, email password) should never be committed to Git. `.env` file is gitignored.

### 5. Rotating File Handler for Logs
**Why?** Prevents log files from growing infinitely. Max 10MB per file, 10 backup files = 100MB total.

### 6. Blueprint Architecture (Future)
**Why?** Modular routes. Each feature (auth, transactions, dashboard) has its own blueprint for organization.

### 7. Service Layer (Future)
**Why?** Business logic separate from routes. Enables Flask → Django migration without rewriting logic.

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'flask'`
**Solution:** Activate virtual environment and install dependencies:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: `ImportError: cannot import name 'db' from 'app'`
**Solution:** This is expected in Module 1. Database models will be created in Module 2.

### Issue: Tests fail with database errors
**Solution:** Ensure you're using testing config (in-memory SQLite). Check `conftest.py` is in `tests/` directory.

### Issue: Flask app won't start
**Solution:** Check logs in `logs/swiftbudget.log` for detailed error messages.

## 📊 Module 1 Metrics

- **Files Created:** 15
- **Lines of Code:** ~600
- **Tests Written:** 17
- **Test Coverage:** ~85% (config and app factory)
- **Time to Complete:** ~30 minutes

## ➡️ Next Module

**Module 2: Database Models (User, Category, Transaction)**

In the next module, we will:
- Create SQLAlchemy models for User, Category, Transaction
- Set up Flask-Migrate for database migrations
- Write unit tests for models
- Test database relationships and constraints

**Prerequisites for Module 2:**
- Module 1 completed successfully
- PostgreSQL installed (or use SQLite for development)
- All Module 1 tests passing
