# SwiftBudget - Personal & Household Budgeting Application

**Version:** 1.0.0  
**Status:** ✅ **LIVE IN PRODUCTION**  
**Framework:** Flask (Python)  
**Database:** PostgreSQL  
**Deployment:** Render.com (Free Tier)  
**Live URL:** https://swiftbudget.onrender.com

---

## 📋 Project Overview

SwiftBudget is a lightweight, responsive web application designed for personal and peer-to-peer household budgeting. Track income, categorize expenses, set budget goals, and visualize your financial health with zero friction.

### Key Features

✅ **Completed (v1.0)**
- **User Authentication** - Secure signup/login/logout with bcrypt password hashing
- **User Profiles** - Profile picture uploads via Cloudinary CDN, username/email/password management
- **Transaction Management** - Full CRUD operations for income and expenses
- **Smart Categorization** - Default categories + custom user categories
- **Budget Goals** - Monthly/weekly/yearly budget limits with threshold alerts
- **Projects/Tags** - Group related transactions for better organization
- **Interactive Dashboard** - Real-time balance, spending trends, and visual charts
- **Email Notifications** - Budget alerts and welcome emails via Gmail SMTP
- **Advanced Features** - Quantity/unit price tracking, soft deletes, audit trails
- **Beautiful UI** - Modern, responsive design with Bootstrap 5 and Chart.js
- **Auto-dismissing Alerts** - Flash messages automatically fade after 4 seconds
- **Malawi Kwacha Support** - Full MK currency integration

🎯 **Future Enhancements (v1.1+)**
- Receipt OCR scanner - Upload receipts and auto-extract transaction details
- Recurring transactions automation
- Data export (CSV/PDF reports)
- Advanced filtering and search
- Multi-currency support
- Mobile app (React Native)
- REST API for third-party integrations

---

## 🏗️ Architecture

**Pattern:** MVC + Service Layer

```
┌─────────────┐
│   Client    │ (Browser)
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────┐
│ Presentation│ (Flask Routes + Jinja2 Templates)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Service    │ (Business Logic - Framework Agnostic)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Data     │ (SQLAlchemy ORM Models)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │ (PostgreSQL on Render)
└─────────────┘
```

**Why Service Layer?**
- Enables future Flask → Django migration with minimal refactoring
- Business logic remains framework-agnostic
- Easier testing and maintenance

---

## 📚 Documentation

All system documentation is located in the `docs/` folder:

| Document | Description | Status |
|----------|-------------|--------|
| **[01_System_Requirements_Document.md](docs/01_System_Requirements_Document.md)** | Functional/non-functional requirements, MoSCoW prioritization, user stories | ✅ Complete |
| **[02_Software_Architecture_Document.md](docs/02_Software_Architecture_Document.md)** | MVC architecture, component diagrams, design patterns, technology stack | ✅ Complete |
| **[03_Database_Design_Document.md](docs/03_Database_Design_Document.md)** | ERD, table schemas, indexes, sample queries, migration strategy | ✅ Complete |
| **[04_API_Specification_Document.md](docs/04_API_Specification_Document.md)** | Route specifications, request/response formats, error handling | ✅ Complete |
| **[05_Deployment_Infrastructure_Document.md](docs/05_Deployment_Infrastructure_Document.md)** | Render.com setup, Supabase configuration, CI/CD pipeline, monitoring | ✅ Complete |
| **[06_Security_Authentication_Document.md](docs/06_Security_Authentication_Document.md)** | Authentication flows, OWASP Top 10 mitigations, encryption, GDPR compliance | ✅ Complete |
| **[07_Testing_Strategy_Document.md](docs/07_Testing_Strategy_Document.md)** | Unit/integration/E2E tests, coverage targets, CI/CD integration | ✅ Complete |

---

## 🚀 Quick Start (Development)

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ (or Supabase account)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/Keithpaul98/SwiftBudget.git
cd SwiftBudget

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
flask db upgrade

# Run development server
flask run
```

Visit `http://localhost:5000` in your browser.

---

## 🗄️ Database Schema

**Core Tables:**
- `users` - User accounts and authentication
- `categories` - Expense/income categories (default + custom)
- `transactions` - Financial transactions (income/expense)
- `budget_goals` - Monthly/weekly/yearly budget limits
- `notification_preferences` - Email notification settings

**Key Design Decisions:**
- PostgreSQL for ACID compliance (critical for financial data)
- `NUMERIC(10,2)` for currency (no floating-point errors)
- Soft deletes for transactions (audit trail)
- Composite indexes on `(user_id, date)` for performance

See [Database Design Document](docs/03_Database_Design_Document.md) for full schema.

---

## 🔒 Security

**Authentication:**
- Bcrypt password hashing (cost factor 12)
- Session-based authentication (Flask-Login)
- CSRF protection on all forms (Flask-WTF)

**Authorization:**
- Data isolation (users can only access their own data)
- Role-based access control (future: admin role)

**OWASP Top 10 Mitigations:**
- ✅ SQL Injection: SQLAlchemy ORM (parameterized queries)
- ✅ XSS: Jinja2 auto-escaping
- ✅ CSRF: Flask-WTF tokens
- ✅ Sensitive Data Exposure: HTTPS, bcrypt hashing
- ✅ Broken Authentication: Strong password policies, rate limiting

See [Security Document](docs/06_Security_Authentication_Document.md) for details.

---

## 🧪 Testing

**Testing Pyramid:**
- 50% Unit Tests (services, models, utilities)
- 30% Integration Tests (routes, database)
- 15% E2E Tests (Playwright)
- 5% Manual Testing

**Coverage Targets:**
- Overall: 80%+
- Service Layer: 90%+
- Critical Paths (auth, transactions): 95%+

**Run Tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test suite
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

See [Testing Strategy Document](docs/07_Testing_Strategy_Document.md) for details.

---

## 📦 Deployment

**Production Stack:**
- **Hosting:** Render.com (512MB RAM, auto-deploy from GitHub)
- **Database:** Render PostgreSQL (Free tier)
- **CDN:** Cloudinary (25GB storage/bandwidth per month)
- **Email:** Gmail SMTP (500 emails/day)
- **Total Cost:** $0/month

**Live Application:** https://swiftbudget.onrender.com

**Note:** Free tier sleeps after 15 minutes of inactivity (30-50 second wake time on first request)

**Deployment Steps:**

1. **Create Render PostgreSQL Database**
   - Sign up at https://render.com
   - Create new PostgreSQL database (free tier)
   - Copy Internal Database URL and modify scheme to `postgresql+psycopg://`

2. **Create Render Web Service**
   - Connect GitHub repository
   - Set Start Command: `gunicorn run:app`
   - Set environment variables (DATABASE_URL, SECRET_KEY, CLOUDINARY credentials, etc.)
   - Deploy automatically on push to `main` branch

3. **Configure Cloudinary CDN**
   - Sign up at https://cloudinary.com (free tier)
   - Get credentials from console
   - Add to Render environment variables

4. **Configure Email**
   - Enable 2FA on Gmail
   - Generate app password
   - Add to Render environment variables

5. **Run Database Migrations**
   - Run `flask db upgrade` locally pointing to production DATABASE_URL
   - Or use Render Shell (paid feature)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guide with troubleshooting.

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11** - Core language
- **Flask 2.3+** - Web framework
- **SQLAlchemy 2.0+** - ORM
- **Flask-Login** - Session management
- **Flask-WTF** - Forms and CSRF protection
- **Bcrypt** - Password hashing
- **Flask-Mail** - Email notifications
- **Flask-Migrate** - Database migrations

### Frontend
- **Jinja2** - Template engine
- **Bootstrap 5** - CSS framework
- **Chart.js** - Interactive data visualizations
- **Vanilla JavaScript** - Client-side interactivity

### Infrastructure
- **PostgreSQL 14+** - Database
- **Gunicorn** - WSGI server
- **Render.com** - Application & database hosting
- **Cloudinary** - Image CDN for profile pictures
- **GitHub** - Version control & auto-deploy trigger

---

## 📊 Project Status

### ✅ Completed Modules
- [x] **Module 1:** User Authentication & Authorization
- [x] **Module 2:** Category Management (Default + Custom)
- [x] **Module 3:** Transaction CRUD Operations
- [x] **Module 4:** Dashboard with Real-time Statistics
- [x] **Module 5:** Advanced Transaction Features (Quantity, Unit Price)
- [x] **Module 6A:** Budget Goals with Alerts
- [x] **Module 6B:** Projects/Tags for Transaction Grouping
- [x] **Module 7:** Email Notifications (Budget Alerts, Welcome Emails)
- [x] **Module 8:** Testing & Deployment Preparation

### 🧪 Testing Status
- [x] 66 Unit Tests - All Passing ✅
- [x] Service Layer Tests - 100% Coverage
- [x] Model Tests - 100% Coverage
- [x] Integration Tests - Ready
- [x] Test Coverage: 80%+ Overall

### 🚀 Deployment Status
- [x] **DEPLOYED TO PRODUCTION** ✅
- [x] Live at https://swiftbudget.onrender.com
- [x] PostgreSQL database configured on Render
- [x] Cloudinary CDN integrated for profile images
- [x] All database migrations applied
- [x] Environment variables configured
- [x] Auto-deploy from GitHub enabled
- [x] Security best practices implemented (HTTPS, CSP, bcrypt)

---

## 🤝 Contributing

This is currently a personal project, but contributions are welcome!

**Development Workflow:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**Code Standards:**
- Follow PEP 8 style guide
- Write docstrings for all functions/classes
- Maintain 80%+ test coverage
- No hardcoded secrets (use environment variables)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Flask** - Excellent web framework
- **Bootstrap** - Responsive CSS framework
- **Supabase** - Generous free-tier PostgreSQL hosting
- **Render.com** - Simple, free deployment platform

---

## 📞 Contact

**Developer:** Keith Paul  
**Email:** nkeithpaul@gmail.com  
**GitHub:** [@Keithpaul98](https://github.com/Keithpaul98)

---

## 🗺️ Roadmap

### v1.0 (MVP) - Target: March 2026
- User authentication
- Transaction CRUD
- Dashboard with balance
- Basic categorization
- Email notifications

### v1.1 - Target: April 2026
- Budget goals with alerts
- Advanced filtering
- Data export (CSV/PDF)
- Recurring transactions

### v2.0 - Target: June 2026
- REST API
- Charts and visualizations
- PayJungle integration
- Mobile-responsive improvements

### v3.0 - Target: Q4 2026
- Multi-user households
- Shared budgets
- Real-time collaboration
- Mobile apps (iOS/Android)

---

## 📖 Additional Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Bootstrap Documentation:** https://getbootstrap.com/docs/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/

---

**Last Updated:** March 5, 2026  
**Application Version:** 1.0.0  
**Project Phase:** ✅ **LIVE IN PRODUCTION**  
**Deployment Date:** March 5, 2026

---

## 🎯 Next Steps (v1.1 Development)

1. **Receipt OCR Scanner** - Upload receipts and auto-extract transaction details
2. **Recurring Transactions** - Automate monthly/weekly recurring expenses
3. **Data Export** - CSV/PDF reports for financial records
4. **Advanced Filtering** - Search and filter transactions by multiple criteria
5. **Performance Optimization** - Reduce wake time, optimize queries
6. **Mobile Responsiveness** - Improve mobile UX
7. **Multi-currency Support** - Support additional currencies beyond MWK

---

**🎉 Application is LIVE! Visit https://swiftbudget.onrender.com to try it out!**
