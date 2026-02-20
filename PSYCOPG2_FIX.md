# Fixing psycopg2-binary Installation on Windows

## Problem
`psycopg2-binary` requires Microsoft Visual C++ 14.0+ to compile on Windows, which causes installation to fail.

## Solution Options

### Option 1: Install Pre-Compiled Wheel (RECOMMENDED - Fastest)

The error occurs because pip is trying to build from source. Use a pre-compiled wheel instead:

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install psycopg2-binary from a pre-compiled wheel
pip install psycopg2-binary --only-binary psycopg2-binary
```

If that doesn't work, try installing a specific version known to have Windows wheels:

```bash
pip install psycopg2-binary==2.9.9
```

### Option 2: Use psycopg2 (not psycopg2-binary)

Install the regular `psycopg2` package which has better Windows wheel support:

```bash
pip install psycopg2==2.9.9
```

Then update `requirements.txt` to use `psycopg2` instead of `psycopg2-binary`.

### Option 3: Install Microsoft C++ Build Tools (If you need latest version)

If you specifically need `psycopg2-binary==2.9.7` and pre-compiled wheels aren't available:

1. Download Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run the installer
3. Select "Desktop development with C++"
4. Install (requires ~6GB disk space)
5. Restart your terminal
6. Run: `pip install psycopg2-binary==2.9.7`

**Note:** This is overkill for development. Use Option 1 or 2 instead.

## Recommended Action

Run these commands in your activated virtual environment:

```bash
# 1. Upgrade pip
python -m pip install --upgrade pip

# 2. Try installing newer version with pre-compiled wheel
pip install psycopg2-binary==2.9.9

# 3. If that works, install the rest of requirements
pip install -r requirements.txt
```

The newer version (2.9.9) has better Windows wheel support and will install without compilation.

## Why This Happens

- `psycopg2-binary` is a PostgreSQL adapter for Python
- On Windows, it needs to compile C extensions
- Compilation requires Visual C++ compiler
- Pre-compiled wheels avoid this requirement
- Newer versions have better wheel availability

## After Fix

Once psycopg2 installs successfully, continue with Module 1 setup:

```bash
# Copy environment file
copy .env.example .env

# Create logs directory
mkdir logs

# Run tests
pytest tests/test_config.py -v
pytest tests/test_app_factory.py -v

# Start Flask app
python run.py
```
