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

### Option 2: Render

1. **Create `render.yaml`** (already in repo)
2. **Connect GitHub repo** at https://render.com
3. **Set environment variables** in Render dashboard
4. **Deploy** - automatic on git push

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
