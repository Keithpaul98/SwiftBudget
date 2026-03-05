# SwiftBudget Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git
- A server (VPS, cloud instance, or PaaS like Heroku/Render)

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/Keithpaul98/SwiftBudget.git
cd SwiftBudget
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file with production settings:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=production

# Database (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/swiftbudget_prod

# Email Configuration (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Currency
CURRENCY_SYMBOL=MK
CURRENCY_CODE=MWK

# Cloudinary (Image CDN for profile pictures)
# Sign up at https://cloudinary.com (free tier: 25GB storage/bandwidth per month)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

**Important Security Notes:**
- Generate a strong SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- Use environment-specific database URLs
- Never commit `.env` to version control
- Use Gmail App Passwords, not regular passwords

### 5. Database Setup

```bash
# Create production database
createdb swiftbudget_prod

# Run migrations
flask db upgrade
```

### 6. Test the Application

```bash
# Run tests
pytest tests/ -v

# Test locally before deployment
python run.py
```

## Deployment Options

### Option 1: Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   heroku create swiftbudget-app
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_ENV=production
   heroku config:set MAIL_USERNAME=your-email@gmail.com
   heroku config:set MAIL_PASSWORD=your-app-password
   # ... set all other variables
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku run flask db upgrade
   heroku open
   ```

### Option 2: Render (Recommended - Currently Deployed)

**Live Application:** https://swiftbudget.onrender.com

#### Step 1: Create PostgreSQL Database

1. Sign up at https://render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `swiftbudget-db`
   - **Database:** `swiftbudget` (auto-filled)
   - **Region:** Oregon (US West) or closest to you
   - **Plan:** Free
4. Click **"Create Database"**
5. Wait for provisioning (~1-2 minutes)
6. Copy the **Internal Database URL** from the Connections section
7. **IMPORTANT:** Modify the URL scheme from `postgresql://` to `postgresql+psycopg://`
   - Example: `postgresql+psycopg://user:pass@host/db`

#### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `swiftbudget`
   - **Region:** Same as database
   - **Branch:** `main`
   - **Root Directory:** Leave blank
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app` ⚠️ **CRITICAL - Must be exactly this**
   - **Plan:** Free

#### Step 3: Set Environment Variables

In the **Environment** tab, add these variables:

```env
FLASK_ENV=production
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=postgresql+psycopg://user:pass@host/db  # From Step 1
CLOUDINARY_CLOUD_NAME=<from cloudinary.com console>
CLOUDINARY_API_KEY=<from cloudinary.com console>
CLOUDINARY_API_SECRET=<from cloudinary.com console>
MAIL_USERNAME=<your-gmail@gmail.com>
MAIL_PASSWORD=<gmail-app-password>
SESSION_COOKIE_SECURE=True
CURRENCY_SYMBOL=MK
CURRENCY_CODE=MWK
LOG_LEVEL=INFO
```

#### Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy
3. Watch the **Logs** tab for build progress
4. Wait for `==> Your service is live 🎉`

#### Step 5: Run Database Migrations

Since Shell is a paid feature on Render, run migrations locally:

```bash
# Set production DATABASE_URL temporarily
export DATABASE_URL="postgresql+psycopg://user:pass@host/db"  # Linux/Mac
# OR
$env:DATABASE_URL="postgresql+psycopg://user:pass@host/db"  # Windows PowerShell

# Run migration
flask db upgrade
```

#### Common Issues & Solutions

**Issue 1: `No matching distribution found for Authlib==1.3.0.post1`**
- **Fix:** Update `requirements.txt` to `Authlib==1.3.2`

**Issue 2: `No matching distribution found for psycopg[binary]==3.1.18`**
- **Fix:** Update to `psycopg[binary]==3.3.3` (compatible with Python 3.14)

**Issue 3: `Failed to find attribute 'app' in 'app'`**
- **Fix:** Set Start Command to `gunicorn run:app` (not `gunicorn app:app`)

**Issue 4: `ModuleNotFoundError: No module named 'psycopg2'`**
- **Fix:** Ensure DATABASE_URL uses `postgresql+psycopg://` scheme (not `postgresql://`)

**Issue 5: CSP violations for CDN source maps**
- **Fix:** Add `cdn.jsdelivr.net` to `connect-src` in CSP (already in `app/__init__.py`)

**Issue 6: Worker timeout / Out of memory during signup/login**
- **Fix:** Reduce `BCRYPT_LOG_ROUNDS` to 10 in `config.py` (already configured)
- **Cause:** Free tier has 512MB RAM, bcrypt with 12 rounds is too intensive

**Issue 7: Slow first load (30-50 seconds)**
- **Expected:** Free tier sleeps after 15 minutes of inactivity
- **Solution:** Upgrade to paid tier ($7/month) or accept wake time

#### Auto-Deploy Setup

Render automatically deploys on every push to `main` branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Render will auto-deploy in ~2-3 minutes
```

### Option 3: VPS (Ubuntu/Debian)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv postgresql nginx
   ```

2. **Set up PostgreSQL**
   ```bash
   sudo -u postgres createuser swiftbudget
   sudo -u postgres createdb swiftbudget_prod
   sudo -u postgres psql
   ALTER USER swiftbudget WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE swiftbudget_prod TO swiftbudget;
   \q
   ```

3. **Configure Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

4. **Set up Nginx** (reverse proxy)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Set up Systemd Service**
   Create `/etc/systemd/system/swiftbudget.service`:
   ```ini
   [Unit]
   Description=SwiftBudget Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/swiftbudget
   Environment="PATH=/var/www/swiftbudget/venv/bin"
   ExecStart=/var/www/swiftbudget/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable swiftbudget
   sudo systemctl start swiftbudget
   ```

## Post-Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables set correctly
- [ ] HTTPS/SSL certificate configured
- [ ] Email sending tested
- [ ] Google OAuth tested (if enabled)
- [ ] Rate limiting configured
- [ ] Backup strategy in place
- [ ] Monitoring/logging set up
- [ ] Domain name configured
- [ ] Firewall rules configured

## Monitoring & Maintenance

### Database Backups

```bash
# Backup
pg_dump swiftbudget_prod > backup_$(date +%Y%m%d).sql

# Restore
psql swiftbudget_prod < backup_20260220.sql
```

### Application Logs

```bash
# View logs (systemd)
sudo journalctl -u swiftbudget -f

# View logs (Heroku)
heroku logs --tail
```

### Updates

```bash
git pull origin main
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart swiftbudget
```

## Troubleshooting

### Database Connection Issues
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check firewall rules

### Email Not Sending
- Verify Gmail App Password
- Check MAIL_* environment variables
- Test with a simple email first

### 500 Errors
- Check application logs
- Verify all environment variables are set
- Check database migrations are up to date

## Security Best Practices

1. **Use HTTPS** - Always use SSL/TLS in production
2. **Strong Passwords** - Generate strong SECRET_KEY
3. **Database Security** - Use strong database passwords
4. **Regular Updates** - Keep dependencies updated
5. **Backups** - Regular database backups
6. **Monitoring** - Set up error monitoring (Sentry, etc.)
7. **Rate Limiting** - Configure Redis for production rate limiting

## Support

For issues or questions:
- GitHub: https://github.com/Keithpaul98/SwiftBudget
- Email: nkeithpaul@gmail.com
