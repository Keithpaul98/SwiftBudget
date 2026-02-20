# SwiftBudget - System Requirements Document (SRD)

**Version:** 1.0  
**Date:** February 20, 2026  
**Project:** SwiftBudget - Personal & Household Budgeting Web Application  
**Framework:** Flask (Python)  
**Status:** Pre-Development Documentation Phase

---

## 1. Executive Summary

SwiftBudget is a lightweight, responsive web application designed for personal and peer-to-peer household budgeting. The application enables users to track income, categorize expenses, and visualize their financial health with minimal friction. Built on Flask and PostgreSQL, it prioritizes simplicity, security, and immediate deployment on free-tier hosting platforms.

### 1.1 Project Vision
To provide individuals and small households with an intuitive, zero-cost budgeting tool that requires no technical expertise while maintaining professional-grade data integrity and security.

### 1.2 Success Criteria
- User can sign up and start tracking transactions within 2 minutes
- 99.9% data accuracy for financial calculations
- Mobile-responsive interface (works on phones, tablets, desktops)
- Deployable on free-tier platforms (Render, Supabase)
- Email notifications for budget alerts

---

## 2. Stakeholders

| Role | Responsibility | Contact Priority |
|------|---------------|------------------|
| **End Users** | Primary users tracking personal/household budgets | High |
| **Developer** | Full-stack development, deployment, maintenance | Critical |
| **Future Contributors** | Potential open-source contributors (if applicable) | Low |

---

## 3. Functional Requirements

### 3.1 MoSCoW Prioritization

#### **MUST HAVE** (Critical for MVP)

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|---------------------|
| FR-001 | User Registration | Users can create accounts with email/username and password | - Email validation<br>- Password strength requirements (min 8 chars)<br>- Unique username/email enforcement |
| FR-002 | User Login/Logout | Secure authentication with session management | - Bcrypt password hashing<br>- Session cookies with expiration<br>- "Remember Me" option |
| FR-003 | Add Transaction | Users can record income/expense transactions | - Amount (decimal, 2 places)<br>- Description (text, max 200 chars)<br>- Date (past or present only)<br>- Category selection |
| FR-004 | Edit Transaction | Users can modify existing transactions | - All fields editable except user_id<br>- Audit trail (optional for v1) |
| FR-005 | Delete Transaction | Users can remove transactions | - Soft delete with confirmation prompt<br>- Recalculate balance after deletion |
| FR-006 | Dashboard | Display total balance and recent transactions | - Current balance (income - expenses)<br>- Last 10 transactions<br>- Quick stats (monthly spending) |

#### **SHOULD HAVE** (High Priority for v1.1)

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|---------------------|
| FR-007 | Expense Categorization | Predefined categories (Food, Rent, Utilities, etc.) | - Minimum 8 default categories<br>- User can create custom categories |
| FR-008 | Monthly Budget Goals | Set spending limits per category | - Alert when 80% of budget reached<br>- Visual progress bars |
| FR-009 | Email Notifications | Alerts for budget thresholds and summaries | - Weekly summary emails<br>- Budget limit warnings<br>- Configurable preferences |
| FR-010 | Transaction Filtering | Filter by date range, category, amount | - Date picker integration<br>- Multi-select categories<br>- Min/max amount filters |

#### **COULD HAVE** (Nice-to-Have for v2.0)

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|---------------------|
| FR-011 | PayJungle Integration | Group expense splitting for households | - API integration<br>- Shared "kitty" tracking |
| FR-012 | Data Export | Download transactions as CSV/PDF | - All transactions or filtered subset<br>- Formatted PDF reports |
| FR-013 | Recurring Transactions | Auto-add monthly bills (rent, subscriptions) | - Frequency settings (weekly/monthly)<br>- End date option |
| FR-014 | Charts & Visualizations | Pie charts for category breakdown | - Chart.js or similar library<br>- Monthly/yearly views |

#### **WON'T HAVE** (Out of Scope for v1.x)

| ID | Feature | Reason for Exclusion |
|----|---------|---------------------|
| FR-015 | Direct Bank API Syncing (Plaid) | Requires paid API, complex security compliance |
| FR-016 | Multi-Currency Real-Time Conversion | Adds unnecessary complexity for target users |
| FR-017 | Mobile Native Apps (iOS/Android) | Web-responsive design sufficient for MVP |
| FR-018 | AI-Powered Spending Insights | Requires ML infrastructure beyond scope |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target Metric |
|----|-------------|---------------|
| NFR-001 | Page Load Time | < 2 seconds on 3G connection |
| NFR-002 | Database Query Response | < 500ms for transaction retrieval |
| NFR-003 | Concurrent Users | Support 100 simultaneous users (free tier) |
| NFR-004 | Transaction Processing | < 1 second to save/update transaction |

### 4.2 Security

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-005 | Password Storage | Bcrypt hashing with salt (cost factor 12) |
| NFR-006 | SQL Injection Prevention | SQLAlchemy ORM with parameterized queries |
| NFR-007 | XSS Protection | Jinja2 auto-escaping enabled |
| NFR-008 | CSRF Protection | Flask-WTF CSRF tokens on all forms |
| NFR-009 | HTTPS Enforcement | SSL/TLS for all production traffic |
| NFR-010 | Session Security | HTTP-only, secure cookies with 24-hour expiration |

### 4.3 Usability

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-011 | Responsive Design | Bootstrap 5 grid system, mobile-first approach |
| NFR-012 | Accessibility | WCAG 2.1 Level AA compliance (color contrast, keyboard navigation) |
| NFR-013 | Browser Compatibility | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| NFR-014 | Error Messaging | User-friendly error messages (no stack traces) |

### 4.4 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-015 | Uptime | 99.5% (acceptable for free tier) |
| NFR-016 | Data Backup | Daily automated backups (Supabase feature) |
| NFR-017 | Error Logging | Centralized logging with Flask-Logging |

### 4.5 Maintainability

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-018 | Code Documentation | Docstrings for all functions/classes |
| NFR-019 | Modular Architecture | Service layer separation for business logic |
| NFR-020 | Version Control | Git with semantic versioning (v1.0.0) |
| NFR-021 | Framework Migration Path | Service layer design to ease Flask → Django transition |

---

## 5. System Constraints

### 5.1 Technical Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **Free Tier Hosting** | Render.com free tier (512MB RAM, sleeps after inactivity) | Cold start delays (10-30s), limited concurrent users |
| **Database Limits** | Supabase free tier (500MB storage, 2GB bandwidth/month) | ~5,000 transactions max per user initially |
| **Email Service** | Free SMTP limits (e.g., Gmail 500/day) | Batch notifications, rate limiting required |
| **No Paid APIs** | Zero external API costs | Manual transaction entry only (no bank sync) |

### 5.2 Business Constraints

| Constraint | Description |
|------------|-------------|
| **Development Timeline** | Solo developer, part-time work |
| **Budget** | $0 for infrastructure (free tiers only) |
| **User Base** | Initial target: 10-50 users (personal/friends) |

---

## 6. User Stories

### 6.1 Core User Flows

**US-001: New User Registration**
```
AS A new user
I WANT TO create an account with my email and password
SO THAT I can securely track my budget
```
**Acceptance Criteria:**
- Email format validation
- Password minimum 8 characters, 1 uppercase, 1 number
- Confirmation email sent (optional for MVP)
- Redirect to dashboard after signup

---

**US-002: Logging a Daily Expense**
```
AS A logged-in user
I WANT TO quickly add an expense (e.g., $4.50 for coffee)
SO THAT my balance updates immediately
```
**Acceptance Criteria:**
- Form accessible from dashboard
- Amount accepts decimals (e.g., 4.50)
- Category dropdown with "Food & Drink" option
- Success message: "Transaction added!"
- Dashboard balance updates without page refresh (AJAX)

---

**US-003: Viewing Monthly Spending**
```
AS A user
I WANT TO see how much I spent this month in each category
SO THAT I can identify where my money goes
```
**Acceptance Criteria:**
- Dashboard shows current month by default
- Category breakdown (e.g., Food: $320, Rent: $1200)
- Option to view previous months

---

**US-004: Setting a Budget Goal**
```
AS A user
I WANT TO set a $500/month limit for "Dining Out"
SO THAT I receive an alert when I approach the limit
```
**Acceptance Criteria:**
- Budget settings page
- Input field for amount per category
- Email alert at 80% and 100% of budget
- Visual indicator (progress bar) on dashboard

---

## 7. Assumptions & Dependencies

### 7.1 Assumptions
- Users have basic internet access (3G minimum)
- Users have a valid email address
- Users understand basic budgeting concepts (income, expense, categories)
- Single currency (USD) for MVP

### 7.2 Dependencies

| Dependency | Version | Purpose | Risk Level |
|------------|---------|---------|------------|
| Python | 3.9+ | Runtime environment | Low (stable) |
| Flask | 2.3+ | Web framework | Low |
| SQLAlchemy | 2.0+ | ORM for database | Low |
| PostgreSQL | 14+ | Relational database | Low |
| Bootstrap | 5.3+ | Frontend framework | Low |
| Flask-Mail | 0.9+ | Email notifications | Medium (SMTP config) |
| python-dotenv | 1.0+ | Environment variables | Low |

---

## 8. Out of Scope (Explicit Exclusions)

1. **Mobile Native Apps**: Web-responsive design only
2. **Real-Time Collaboration**: No simultaneous multi-user editing
3. **Investment Tracking**: Stocks, crypto, etc.
4. **Bill Payment Processing**: No payment gateway integration
5. **Advanced Analytics**: No predictive modeling or AI insights
6. **Multi-Tenancy**: Each user has isolated data (no shared accounts in v1)

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Transaction** | A single income or expense entry with amount, date, category |
| **Category** | A classification for transactions (e.g., Food, Rent, Utilities) |
| **Balance** | Total income minus total expenses |
| **Budget Goal** | A spending limit set for a specific category over a time period |
| **Dashboard** | The main user interface showing balance and recent activity |
| **ACID Compliance** | Atomicity, Consistency, Isolation, Durability (database properties) |
| **MVC** | Model-View-Controller architectural pattern |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |

---

## 10. Approval & Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Product Owner** | [Developer Name] | _________ | ______ |
| **Technical Lead** | [Developer Name] | _________ | ______ |

---

## 11. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | Developer | Initial SRD creation |

---

**Next Steps:**
1. Review and approve this SRD
2. Proceed to Software Architecture Document (SAD)
3. Create Database Design Document (DDD)
4. Begin implementation after all documentation is complete
