# SwiftBudget - Deployment & Infrastructure Document

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Deployment Strategy:** Free-Tier Cloud Hosting  
**Target:** Zero-Cost Production Deployment

---

## 1. Deployment Overview

### 1.1 Deployment Philosophy

SwiftBudget is designed for **immediate, zero-cost deployment** using free-tier cloud services. The architecture prioritizes:

- **Simplicity**: Minimal configuration, automated deployments
- **Cost**: $0/month infrastructure costs
- **Reliability**: 99.5% uptime (acceptable for free tier)
- **Scalability**: Support 10-100 users initially

### 1.2 Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│   GitHub Repo    │────────>│   Render.com     │
│  (Source Code)   │  Push   │  (Web Server)    │
└──────────────────┘         └────────┬─────────┘
                                      │
                                      │ HTTPS
                                      │
                             ┌────────▼─────────┐
                             │   End Users      │
                             │   (Browsers)     │
                             └──────────────────┘
                                      │
                                      │ PostgreSQL
                                      │ Connection
                             ┌────────▼─────────┐
                             │   Supabase       │
                             │  (PostgreSQL DB) │
                             └──────────────────┘

┌──────────────────┐
│   Gmail SMTP     │<──── Email Notifications
│  (Flask-Mail)    │
└──────────────────┘
```

---

## 2. Hosting Platform: Render.com

### 2.1 Why Render.com?

| Feature | Render.com | Heroku | Railway | Vercel |
|---------|-----------|--------|---------|--------|
| **Free Tier** | ✅ 512MB RAM | ❌ Deprecated | ✅ $5 credit | ❌ Serverless only |
| **Auto-Deploy** | ✅ GitHub integration | ✅ | ✅ | ✅ |
| **PostgreSQL** | ⚠️ Paid ($7/mo) | ⚠️ Paid | ✅ Free | ❌ |
| **Cold Starts** | ⚠️ Yes (15-30s) | ⚠️ Yes | ⚠️ Yes | N/A |
| **Custom Domain** | ✅ Free SSL | ✅ | ✅ | ✅ |
| **Ease of Use** | ✅ Excellent | ✅ | ✅ | ⚠️ Complex |

**Verdict:** Render.com offers the best balance of features and ease of use for Flask applications.

### 2.2 Free Tier Specifications

| Resource | Limit | Impact |
|----------|-------|--------|
| **RAM** | 512MB | ~100 concurrent users |
| **CPU** | Shared | Slower response times under load |
| **Bandwidth** | 100GB/month | ~50,000 page views |
| **Build Minutes** | 500/month | ~50 deployments |
| **Uptime** | 99.5% target | Occasional downtime acceptable |
| **Cold Start** | 15-30 seconds | First request after 15 min inactivity |

**Cold Start Mitigation:**
- Use external uptime monitor (UptimeRobot) to ping app every 10 minutes
- Display loading message to users during cold start

### 2.3 Render.com Configuration

**File:** `render.yaml` (Infrastructure as Code)

```yaml
services:
  - type: web
    name: swiftbudget
    env: python
    region: oregon  # Choose closest to users
    plan: free
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
      flask db upgrade
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: FLASK_APP
        value: app.py
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true  # Auto-generate secure key
      - key: DATABASE_URL
        fromDatabase:
          name: swiftbudget-db
          property: connectionString
      - key: MAIL_SERVER
        value: smtp.gmail.com
      - key: MAIL_PORT
        value: 587
      - key: MAIL_USE_TLS
        value: true
      - key: MAIL_USERNAME
        sync: false  # Set manually in dashboard
      - key: MAIL_PASSWORD
        sync: false  # Set manually (app password)
    healthCheckPath: /health
    autoDeploy: true  # Deploy on every push to main branch

databases:
  - name: swiftbudget-db
    databaseName: swiftbudget
    user: swiftbudget_user
    plan: free  # Note: Render DB is paid, use Supabase instead
```

**Note:** Since Render's PostgreSQL is paid, we'll use **Supabase** for the database (see section 3).

---

## 3. Database Hosting: Supabase

### 3.1 Why Supabase?

| Feature | Supabase | ElephantSQL | Render DB | Neon |
|---------|----------|-------------|-----------|------|
| **Free Tier** | ✅ 500MB | ✅ 20MB | ❌ Paid | ✅ 512MB |
| **Storage** | 500MB | 20MB | N/A | 512MB |
| **Bandwidth** | 2GB/month | 5 connections | N/A | Unlimited |
| **Backups** | ✅ Daily (7 days) | ❌ Manual only | ✅ | ✅ |
| **Dashboard** | ✅ Excellent | ⚠️ Basic | ✅ | ✅ |
| **Ease of Setup** | ✅ 2 minutes | ✅ | N/A | ✅ |

**Verdict:** Supabase offers the most generous free tier with excellent tooling.

### 3.2 Supabase Setup Steps

**Step 1: Create Project**
1. Sign up at https://supabase.com
2. Click "New Project"
3. Project Name: `swiftbudget`
4. Database Password: Generate strong password (save in password manager)
5. Region: Choose closest to Render.com region (e.g., `us-west-1`)
6. Click "Create Project" (takes ~2 minutes)

**Step 2: Get Connection String**
```
Settings → Database → Connection String → URI

Format:
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Step 3: Configure SSL (Required)**
```python
# config.py
import os

DATABASE_URL = os.getenv('DATABASE_URL')

# Supabase requires SSL
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
```

**Step 4: Run Migrations**
```bash
# Set environment variable
export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"

# Run migrations
flask db upgrade
```

### 3.3 Supabase Free Tier Limits

| Resource | Limit | Monitoring |
|----------|-------|------------|
| **Storage** | 500MB | Check dashboard weekly |
| **Bandwidth** | 2GB/month | ~10,000 queries/month |
| **Connections** | 60 concurrent | Use connection pooling |
| **Backups** | Daily (7-day retention) | Automatic |

**Capacity Planning:**
- Average transaction size: ~100 bytes
- 500MB = ~5,000,000 transactions
- For 100 users: 50,000 transactions/user (years of data)

---

## 4. Email Service: Gmail SMTP

### 4.1 Gmail SMTP Configuration

**Free Tier:** 500 emails/day (sufficient for budget alerts)

**Setup Steps:**

**Step 1: Enable 2-Factor Authentication**
1. Go to Google Account settings
2. Security → 2-Step Verification → Enable

**Step 2: Generate App Password**
1. Security → 2-Step Verification → App passwords
2. Select "Mail" and "Other (Custom name)"
3. Name: "SwiftBudget"
4. Copy 16-character password (e.g., `abcd efgh ijkl mnop`)

**Step 3: Configure Flask-Mail**
```python
# config.py
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # your-email@gmail.com
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # App password
MAIL_DEFAULT_SENDER = ('SwiftBudget', os.getenv('MAIL_USERNAME'))
```

**Step 4: Set Environment Variables (Render Dashboard)**
```
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = abcdefghijklmnop  # App password (no spaces)
```

### 4.2 Email Rate Limiting

**Daily Limits:**
- Gmail Free: 500 emails/day
- Budget alerts: ~10-20/day (100 users × 20% trigger rate)
- Weekly summaries: 100/week (sent on Sundays)

**Rate Limiting Strategy:**
```python
# app/services/email_service.py
from flask_limiter import Limiter

limiter = Limiter(
    key_func=lambda: 'email_service',
    default_limits=["400 per day"]  # Leave buffer for 500 limit
)

@limiter.limit("400 per day")
def send_budget_alert(user_email, category, percent_used):
    # Send email logic
    pass
```

### 4.3 Alternative: SendGrid (Backup)

**Free Tier:** 100 emails/day

**Setup:**
```python
# config.py
MAIL_SERVER = 'smtp.sendgrid.net'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'apikey'
MAIL_PASSWORD = os.getenv('SENDGRID_API_KEY')
```

---

## 5. Deployment Workflow

### 5.1 Git Repository Structure

```
swiftbudget/
├── .git/
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── migrations/
├── tests/
├── docs/
├── config.py
├── requirements.txt
├── render.yaml
├── .env.example
├── README.md
└── app.py  # Entry point
```

**.gitignore:**
```
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

### 5.2 Continuous Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT PIPELINE                       │
└─────────────────────────────────────────────────────────────┘

1. Developer commits code
   └─> git commit -m "Add budget alerts feature"

2. Push to GitHub
   └─> git push origin main

3. Render detects push (webhook)
   └─> Triggers automatic build

4. Build Process (Render)
   ├─> Install dependencies (pip install -r requirements.txt)
   ├─> Run database migrations (flask db upgrade)
   └─> Collect static files (if needed)

5. Deploy Process
   ├─> Start Gunicorn server (4 workers)
   ├─> Health check (/health endpoint)
   └─> Route traffic to new version

6. Rollback (if health check fails)
   └─> Revert to previous deployment

Total Time: 2-5 minutes
```

### 5.3 Deployment Commands

**Local Testing:**
```bash
# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export DATABASE_URL="postgresql://localhost/swiftbudget_dev"
export SECRET_KEY="dev-secret-key"

# Run migrations
flask db upgrade

# Start development server
flask run
```

**Production Deployment:**
```bash
# Commit changes
git add .
git commit -m "Feature: Add budget goal tracking"

# Push to GitHub (triggers auto-deploy)
git push origin main

# Monitor deployment
# Go to Render dashboard → Logs
```

**Manual Deployment (Render CLI):**
```bash
# Install Render CLI
npm install -g render-cli

# Login
render login

# Deploy
render deploy --service swiftbudget
```

---

## 6. Environment Variables

### 6.1 Required Environment Variables

| Variable | Description | Example | Where to Set |
|----------|-------------|---------|--------------|
| `SECRET_KEY` | Flask session encryption | `a1b2c3d4e5f6...` | Render dashboard (auto-generated) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` | Supabase dashboard |
| `FLASK_ENV` | Environment (production/development) | `production` | Render.yaml |
| `MAIL_USERNAME` | Gmail address | `your-email@gmail.com` | Render dashboard |
| `MAIL_PASSWORD` | Gmail app password | `abcdefghijklmnop` | Render dashboard |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` | Render.yaml |
| `MAIL_PORT` | SMTP port | `587` | Render.yaml |
| `MAIL_USE_TLS` | Enable TLS | `true` | Render.yaml |

### 6.2 Environment Variable Management

**Development (.env file):**
```bash
# .env (DO NOT COMMIT)
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://localhost/swiftbudget_dev
FLASK_ENV=development
MAIL_USERNAME=test@gmail.com
MAIL_PASSWORD=test-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

**Production (Render Dashboard):**
1. Go to Render dashboard → swiftbudget service
2. Environment → Add Environment Variable
3. Set each variable individually
4. Click "Save Changes" (triggers redeploy)

**Security Best Practices:**
- ✅ Never commit `.env` to Git
- ✅ Use different `SECRET_KEY` for dev/prod
- ✅ Rotate secrets every 90 days
- ✅ Use Render's "Generate Value" for `SECRET_KEY`
- ❌ Never hardcode secrets in code

---

## 7. Database Migrations

### 7.1 Flask-Migrate Setup

**Installation:**
```bash
pip install Flask-Migrate
```

**Initialization (one-time):**
```bash
flask db init
# Creates migrations/ folder
```

**Creating Migrations:**
```bash
# After modifying models
flask db migrate -m "Add budget_goals table"

# Review generated migration file
# migrations/versions/xxx_add_budget_goals_table.py
```

**Applying Migrations:**
```bash
# Development
flask db upgrade

# Production (automatic via render.yaml buildCommand)
# Runs on every deployment
```

### 7.2 Migration Strategy

**Development Workflow:**
1. Modify SQLAlchemy models
2. Run `flask db migrate -m "Description"`
3. Review generated migration file
4. Test migration: `flask db upgrade`
5. Test rollback: `flask db downgrade`
6. Commit migration file to Git

**Production Workflow:**
1. Push code to GitHub
2. Render auto-runs `flask db upgrade` during build
3. If migration fails, deployment fails (safe)
4. Rollback: `flask db downgrade` (manual via Render shell)

### 7.3 Rollback Procedure

**Scenario:** Migration breaks production

**Steps:**
```bash
# 1. SSH into Render container
render shell swiftbudget

# 2. Rollback last migration
flask db downgrade

# 3. Verify database state
flask shell
>>> from app import db
>>> db.session.execute('SELECT * FROM users LIMIT 1')

# 4. Revert Git commit
git revert HEAD
git push origin main

# 5. Render auto-deploys previous version
```

---

## 8. Monitoring & Logging

### 8.1 Application Logging

**Configuration:**
```python
# config.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    # Production logging
    file_handler = RotatingFileHandler('logs/swiftbudget.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('SwiftBudget startup')
```

**Log Levels:**
- **DEBUG**: Development only (SQL queries, variable values)
- **INFO**: Production events (user login, transaction created)
- **WARNING**: Potential issues (budget threshold reached)
- **ERROR**: Errors that don't crash app (email send failure)
- **CRITICAL**: App-breaking errors (database connection lost)

### 8.2 Render Logs

**Accessing Logs:**
1. Render Dashboard → swiftbudget service
2. Logs tab
3. Real-time streaming logs

**Log Retention:** 7 days on free tier

**Example Logs:**
```
2026-02-20 14:30:15 INFO: User john_doe logged in
2026-02-20 14:30:20 INFO: Transaction created: $45.50 (Food & Dining)
2026-02-20 14:30:25 WARNING: Budget alert triggered for user 1 (Entertainment: 85%)
2026-02-20 14:30:30 ERROR: Failed to send email to john@example.com: SMTP timeout
```

### 8.3 Uptime Monitoring

**Tool:** UptimeRobot (Free)

**Setup:**
1. Sign up at https://uptimerobot.com
2. Add Monitor:
   - Type: HTTP(s)
   - URL: `https://swiftbudget.onrender.com/health`
   - Interval: 5 minutes
   - Alert Contacts: Your email
3. Enable notifications for downtime

**Health Check Endpoint:**
```python
# app/routes/health.py
from flask import Blueprint, jsonify
from app import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
```

**Cold Start Prevention:**
- UptimeRobot pings every 5 minutes
- Keeps app warm (no cold starts for users)
- Free tier allows 50 monitors

---

## 9. SSL/TLS Configuration

### 9.1 Automatic SSL (Render)

**Features:**
- ✅ Free SSL certificate (Let's Encrypt)
- ✅ Auto-renewal every 90 days
- ✅ HTTPS enforced by default
- ✅ HTTP → HTTPS redirect

**No configuration needed!** Render handles everything.

**Custom Domain (Optional):**
1. Buy domain (e.g., swiftbudget.com from Namecheap)
2. Render Dashboard → Settings → Custom Domains
3. Add domain: `swiftbudget.com`
4. Update DNS records (A/CNAME)
5. SSL auto-provisioned in 5-10 minutes

### 9.2 Force HTTPS in Flask

```python
# app/__init__.py
from flask_talisman import Talisman

app = Flask(__name__)

if not app.debug:
    # Force HTTPS in production
    Talisman(app, content_security_policy=None)
```

---

## 10. Backup & Disaster Recovery

### 10.1 Database Backups

**Supabase Automatic Backups:**
- **Frequency:** Daily at 2 AM UTC
- **Retention:** 7 days (free tier)
- **Location:** Supabase infrastructure (encrypted)

**Manual Backup:**
```bash
# Backup to local file
pg_dump -h db.xxx.supabase.co -U postgres -d postgres > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h db.xxx.supabase.co -U postgres -d postgres < backup_20260220.sql
```

**Backup Schedule:**
- **Daily:** Automatic (Supabase)
- **Weekly:** Manual backup to local storage (Sundays)
- **Pre-deployment:** Manual backup before major releases

### 10.2 Code Backups

**GitHub as Source of Truth:**
- All code versioned in Git
- Push to GitHub after every feature
- GitHub retains full history

**Disaster Recovery:**
1. Code lost: Clone from GitHub
2. Database corrupted: Restore from Supabase backup
3. Render account compromised: Redeploy to new Render account (5 minutes)

### 10.3 Recovery Time Objectives (RTO)

| Scenario | RTO | Procedure |
|----------|-----|-----------|
| **App crash** | 2 minutes | Render auto-restarts |
| **Bad deployment** | 5 minutes | Rollback via Render dashboard |
| **Database corruption** | 30 minutes | Restore from Supabase backup |
| **Complete infrastructure loss** | 2 hours | Redeploy to new Render + Supabase |

---

## 11. Scaling Strategy

### 11.1 Current Capacity (Free Tier)

| Metric | Limit | Headroom |
|--------|-------|----------|
| **Users** | 100 active | 50% capacity |
| **Database** | 500MB | ~5,000 transactions/user |
| **Bandwidth** | 100GB/month | ~50,000 page views |
| **Concurrent Requests** | ~50 | Limited by 512MB RAM |

### 11.2 When to Upgrade

**Triggers:**
- Database size > 400MB (80% capacity)
- Frequent cold starts impacting UX
- >200 active users
- Page load times > 3 seconds

### 11.3 Upgrade Path

**Render Paid Tier ($7/month):**
- 512MB → 2GB RAM
- No cold starts
- Faster CPU
- Custom domain included

**Supabase Paid Tier ($25/month):**
- 500MB → 8GB storage
- 2GB → 50GB bandwidth
- Point-in-time recovery
- Daily backups → Continuous backups

**Total Cost:** $32/month for 500+ users

---

## 12. Performance Optimization

### 12.1 Gunicorn Configuration

**Workers:** 4 (optimal for 512MB RAM)

**Formula:** `workers = (2 × CPU cores) + 1`

**Configuration:**
```python
# gunicorn.conf.py
bind = "0.0.0.0:10000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
```

**Start Command:**
```bash
gunicorn -c gunicorn.conf.py app:app
```

### 12.2 Database Connection Pooling

**SQLAlchemy Configuration:**
```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,        # Max connections
    'pool_recycle': 3600,   # Recycle connections every hour
    'pool_pre_ping': True,  # Verify connections before use
    'max_overflow': 5       # Allow 5 extra connections if needed
}
```

### 12.3 Static File Optimization

**CDN for Bootstrap (reduce server load):**
```html
<!-- Use CDN instead of local files -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
```

**Minify CSS/JS:**
```bash
# Install minifier
pip install cssmin jsmin

# Minify files
python -m cssmin < static/css/style.css > static/css/style.min.css
```

---

## 13. Security Hardening

### 13.1 Production Checklist

- [x] `DEBUG = False` in production
- [x] Strong `SECRET_KEY` (auto-generated by Render)
- [x] HTTPS enforced (Render default)
- [x] CSRF protection enabled (Flask-WTF)
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS protection (Jinja2 auto-escaping)
- [x] Secure session cookies (`HttpOnly`, `Secure`, `SameSite`)
- [x] Rate limiting (Flask-Limiter)
- [x] Database SSL connection (Supabase)
- [x] Environment variables (no hardcoded secrets)

### 13.2 Security Headers

```python
# app/__init__.py
from flask_talisman import Talisman

Talisman(app,
    force_https=True,
    strict_transport_security=True,
    session_cookie_secure=True,
    session_cookie_http_only=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", 'cdn.jsdelivr.net'],
        'style-src': ["'self'", 'cdn.jsdelivr.net']
    }
)
```

---

## 14. Troubleshooting Guide

### 14.1 Common Issues

**Issue: App won't start after deployment**

**Symptoms:** Render logs show "Application failed to start"

**Solutions:**
```bash
# Check logs
render logs swiftbudget

# Common causes:
# 1. Missing dependency
pip freeze > requirements.txt  # Ensure all deps listed

# 2. Migration failed
flask db upgrade  # Test locally first

# 3. Environment variable missing
# Check Render dashboard → Environment
```

---

**Issue: Database connection timeout**

**Symptoms:** `OperationalError: could not connect to server`

**Solutions:**
```python
# 1. Verify DATABASE_URL
print(os.getenv('DATABASE_URL'))

# 2. Check SSL mode
SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'

# 3. Test connection
psql "postgresql://user:pass@host/db?sslmode=require"
```

---

**Issue: Cold starts too slow**

**Symptoms:** First request takes 30+ seconds

**Solutions:**
1. Set up UptimeRobot to ping every 5 minutes
2. Upgrade to Render paid tier (no cold starts)
3. Display loading message to users

---

**Issue: Email not sending**

**Symptoms:** No emails received, logs show SMTP error

**Solutions:**
```python
# 1. Verify Gmail app password
# Regenerate if needed (Google Account → Security → App passwords)

# 2. Check TLS settings
MAIL_USE_TLS = True
MAIL_PORT = 587  # Not 465

# 3. Test email manually
flask shell
>>> from app import mail
>>> from flask_mail import Message
>>> msg = Message('Test', recipients=['test@example.com'])
>>> mail.send(msg)
```

---

## 15. Deployment Checklist

### 15.1 Pre-Deployment

- [ ] All tests passing (`pytest`)
- [ ] Database migrations created and tested
- [ ] Environment variables documented
- [ ] `.env.example` updated
- [ ] `requirements.txt` updated (`pip freeze`)
- [ ] README.md updated with deployment steps
- [ ] Secrets rotated (if needed)

### 15.2 Deployment

- [ ] Push code to GitHub (`git push origin main`)
- [ ] Monitor Render build logs
- [ ] Verify health check passes (`/health`)
- [ ] Test critical user flows (signup, login, add transaction)
- [ ] Check database migrations applied
- [ ] Verify email notifications working

### 15.3 Post-Deployment

- [ ] Monitor error logs for 24 hours
- [ ] Check UptimeRobot status
- [ ] Verify database backups running
- [ ] Update documentation with any changes
- [ ] Notify users of new features (if applicable)

---

## 16. Cost Breakdown

### 16.1 Free Tier (Current)

| Service | Cost | Limits |
|---------|------|--------|
| **Render.com** | $0 | 512MB RAM, cold starts |
| **Supabase** | $0 | 500MB DB, 2GB bandwidth |
| **Gmail SMTP** | $0 | 500 emails/day |
| **GitHub** | $0 | Unlimited public repos |
| **UptimeRobot** | $0 | 50 monitors, 5-min interval |
| **Total** | **$0/month** | Supports 10-100 users |

### 16.2 Paid Tier (Future)

| Service | Cost | Benefits |
|---------|------|----------|
| **Render Starter** | $7/month | 2GB RAM, no cold starts |
| **Supabase Pro** | $25/month | 8GB DB, 50GB bandwidth |
| **SendGrid Essentials** | $20/month | 50,000 emails/month |
| **Total** | **$52/month** | Supports 500+ users |

---

## 17. Approval & Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial deployment documentation |

**Next Document:** Security & Authentication Document
