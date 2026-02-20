# Update Your .env File

## Issue
The tests are failing because the `.env` file has a PostgreSQL connection string, but SQLAlchemy is looking for the `psycopg2` driver (we installed `psycopg3`).

## Solution

Open your `.env` file and update the `DATABASE_URL` line:

### Option 1: Use SQLite for Local Development (RECOMMENDED - Easiest)

```env
DATABASE_URL=sqlite:///swiftbudget_dev.db
```

**Why SQLite for development?**
- No PostgreSQL installation needed
- Fast and simple
- Perfect for testing and development
- Production will still use PostgreSQL (Supabase)

### Option 2: Use PostgreSQL with psycopg3 Driver

If you have PostgreSQL installed locally and want to use it:

```env
DATABASE_URL=postgresql+psycopg://localhost/swiftbudget_dev
```

**Note:** The `+psycopg` tells SQLAlchemy to use psycopg3 instead of psycopg2.

## After Updating .env

Run the tests again:

```bash
pytest tests/test_app_factory.py -v
```

All tests should pass now.

## Why This Happened

- We installed `psycopg[binary]==3.1.18` (psycopg3)
- SQLAlchemy defaults to `psycopg2` driver for `postgresql://` URLs
- Need to specify `postgresql+psycopg://` to use psycopg3
- OR use SQLite for local development (simpler)
