# SwiftBudget Migration Guide: Python/Flask → Next.js/Supabase

**Created:** March 7, 2026  
**Purpose:** Complete guide for rebuilding SwiftBudget as a Next.js application deployable on Netlify  
**Target User:** Developer learning JavaScript/React while building

---

## 📋 Current Application Overview

### Python/Flask Application (v1.0)
- **Live URL:** https://swiftbudget.onrender.com
- **Status:** Deployed but experiencing performance issues on Render free tier
- **Repository:** https://github.com/Keithpaul98/SwiftBudget

### Current Tech Stack
- **Backend:** Python 3.14, Flask 3.0.2
- **Database:** PostgreSQL (Render)
- **ORM:** SQLAlchemy 2.0+
- **Authentication:** Flask-Login + Bcrypt
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js
- **CDN:** Cloudinary (profile images)
- **Email:** Gmail SMTP
- **Deployment:** Render.com (free tier - 512MB RAM)

### Current Features (All Working)
1. ✅ User Authentication (signup, login, logout)
2. ✅ User Profiles (username, email, password, profile picture)
3. ✅ Transaction Management (CRUD for income/expenses)
4. ✅ Categories (default + custom user categories)
5. ✅ Budget Goals (monthly/weekly/yearly with alerts)
6. ✅ Projects/Tags (group transactions)
7. ✅ Interactive Dashboard (balance, charts, trends)
8. ✅ Email Notifications (budget alerts, welcome emails)
9. ✅ Advanced Features (quantity, unit price, soft deletes, audit logs)
10. ✅ Auto-dismissing flash alerts
11. ✅ Malawi Kwacha (MK) currency support

### Database Schema (PostgreSQL)

**Users Table:**
```sql
- id (UUID, primary key)
- username (unique, max 50 chars)
- email (unique, max 120 chars)
- password_hash (bcrypt)
- profile_image (text, Cloudinary URL)
- is_active (boolean, default true)
- email_notifications (boolean, default true)
- created_at (timestamp)
- last_login (timestamp)
- failed_login_attempts (integer)
- account_locked_until (timestamp)
```

**Categories Table:**
```sql
- id (integer, primary key)
- name (max 50 chars)
- type (enum: 'income' or 'expense')
- is_default (boolean)
- user_id (foreign key to users, nullable for defaults)
- created_at (timestamp)
```

**Transactions Table:**
```sql
- id (integer, primary key)
- user_id (foreign key to users)
- category_id (foreign key to categories)
- project_id (foreign key to projects, nullable)
- type (enum: 'income' or 'expense')
- amount (numeric 10,2)
- description (text)
- date (date)
- quantity (numeric 10,2, nullable)
- unit_price (numeric 10,2, nullable)
- is_deleted (boolean, default false)
- created_at (timestamp)
- updated_at (timestamp)
```

**Budget Goals Table:**
```sql
- id (integer, primary key)
- user_id (foreign key to users)
- category_id (foreign key to categories, nullable)
- amount (numeric 10,2)
- period (enum: 'weekly', 'monthly', 'yearly')
- start_date (date)
- end_date (date)
- alert_threshold (integer, default 80)
- is_active (boolean, default true)
- created_at (timestamp)
```

**Projects Table:**
```sql
- id (integer, primary key)
- user_id (foreign key to users)
- name (max 100 chars)
- description (text, nullable)
- color (max 7 chars, hex color)
- is_active (boolean, default true)
- created_at (timestamp)
```

**Recurring Transactions Table:**
```sql
- id (integer, primary key)
- user_id (foreign key to users)
- category_id (foreign key to categories)
- type (enum: 'income' or 'expense')
- amount (numeric 10,2)
- description (text)
- frequency (enum: 'daily', 'weekly', 'monthly', 'yearly')
- start_date (date)
- end_date (date, nullable)
- next_occurrence (date)
- is_active (boolean, default true)
- created_at (timestamp)
```

**Audit Logs Table:**
```sql
- id (integer, primary key)
- user_id (foreign key to users)
- action (max 50 chars)
- entity_type (max 50 chars)
- entity_id (integer)
- old_values (jsonb, nullable)
- new_values (jsonb, nullable)
- ip_address (max 45 chars, nullable)
- created_at (timestamp)
```

---

## 🎯 New Tech Stack (Next.js + Supabase)

### Recommended Stack
- **Framework:** Next.js 14+ (React 18+)
- **Language:** TypeScript (strongly recommended)
- **Database:** Supabase PostgreSQL (free tier: 500MB)
- **Authentication:** Supabase Auth (built-in)
- **Storage:** Supabase Storage (profile images)
- **Styling:** Tailwind CSS + shadcn/ui components
- **Charts:** Recharts or Chart.js
- **Email:** Supabase Edge Functions + Resend
- **Deployment:** Netlify or Vercel (both free, unlimited)

### Why This Stack?
1. ✅ **Netlify-compatible** - deploys in seconds
2. ✅ **No backend server needed** - serverless architecture
3. ✅ **Free hosting** - Netlify/Vercel free tier is generous
4. ✅ **Free database** - Supabase free tier: 500MB, 2GB bandwidth
5. ✅ **Built-in auth** - no need to code login/signup from scratch
6. ✅ **Type safety** - TypeScript prevents bugs
7. ✅ **Modern UI** - Tailwind + shadcn/ui = beautiful, accessible components
8. ✅ **Fast performance** - static generation + server-side rendering
9. ✅ **Great DX** - hot reload, easy debugging

---

## 🗺️ Migration Roadmap

### Phase 1: Project Setup (Day 1)
**Goal:** Get Next.js project running with Supabase connected

**Tasks:**
1. Create new Next.js project with TypeScript
2. Set up Supabase project
3. Migrate database schema to Supabase
4. Configure Supabase client in Next.js
5. Set up Tailwind CSS + shadcn/ui
6. Create basic layout and navigation

**Deliverables:**
- Next.js app running on localhost:3000
- Supabase project with database tables
- Basic UI layout with navigation

---

### Phase 2: Authentication (Day 2)
**Goal:** User signup, login, logout working

**Tasks:**
1. Set up Supabase Auth
2. Create signup page with form validation
3. Create login page
4. Implement logout functionality
5. Create protected routes middleware
6. Add session management

**Deliverables:**
- Users can sign up, log in, log out
- Protected routes redirect to login
- Session persists on page reload

---

### Phase 3: User Profile (Day 3)
**Goal:** Profile management with image upload

**Tasks:**
1. Create profile page UI
2. Implement profile image upload to Supabase Storage
3. Add edit profile form (username, email)
4. Add change password functionality
5. Display user info in navigation

**Deliverables:**
- Profile page showing user details
- Profile image upload working
- Edit profile functionality

---

### Phase 4: Categories & Transactions (Days 4-5)
**Goal:** Core budgeting features working

**Tasks:**
1. Create categories management page
2. Implement add/edit/delete categories
3. Create transactions page with list view
4. Implement add transaction form
5. Add edit/delete transaction functionality
6. Implement filtering by date, category, type
7. Add search functionality

**Deliverables:**
- Categories CRUD working
- Transactions CRUD working
- Filtering and search functional

---

### Phase 5: Dashboard & Charts (Day 6)
**Goal:** Visual dashboard with statistics

**Tasks:**
1. Create dashboard layout
2. Calculate current balance
3. Show income vs expenses
4. Add spending by category chart (pie/donut)
5. Add spending trends chart (line/bar)
6. Display recent transactions
7. Add quick stats cards

**Deliverables:**
- Dashboard with balance and stats
- Interactive charts
- Recent transactions list

---

### Phase 6: Budget Goals & Projects (Day 7)
**Goal:** Advanced features

**Tasks:**
1. Create budget goals page
2. Implement add/edit/delete budget goals
3. Add budget progress tracking
4. Create projects page
5. Implement add/edit/delete projects
6. Link transactions to projects

**Deliverables:**
- Budget goals CRUD working
- Budget alerts/warnings
- Projects CRUD working

---

### Phase 7: Email Notifications (Day 8)
**Goal:** Email alerts for budget thresholds

**Tasks:**
1. Set up Supabase Edge Functions
2. Create email templates
3. Implement budget threshold checking
4. Send welcome email on signup
5. Send budget alert emails

**Deliverables:**
- Welcome emails sent on signup
- Budget alert emails working

---

### Phase 8: Polish & Deploy (Day 9)
**Goal:** Production-ready app on Netlify

**Tasks:**
1. Add loading states
2. Improve error handling
3. Add toast notifications
4. Optimize performance
5. Test all features
6. Deploy to Netlify
7. Configure environment variables
8. Test production deployment

**Deliverables:**
- Polished UI with loading states
- App deployed to Netlify
- All features tested and working

---

## 📚 Learning Resources for Next.js

### Essential Concepts to Learn
1. **React Basics**
   - Components (functional components)
   - Props and state (useState hook)
   - Effects (useEffect hook)
   - Event handling

2. **Next.js Specifics**
   - File-based routing
   - Server components vs client components
   - API routes
   - Server actions
   - Metadata and SEO

3. **TypeScript Basics**
   - Type annotations
   - Interfaces
   - Type inference
   - Generic types

4. **Supabase**
   - Database queries
   - Authentication
   - Storage
   - Real-time subscriptions

### Recommended Learning Path
1. **Next.js Official Tutorial** (2-3 hours)
   - https://nextjs.org/learn

2. **React Docs** (reference as needed)
   - https://react.dev/learn

3. **Supabase Docs** (reference as needed)
   - https://supabase.com/docs

4. **Tailwind CSS Docs** (reference as needed)
   - https://tailwindcss.com/docs

---

## 🔄 Feature Mapping: Flask → Next.js

### Authentication
**Flask (current):**
```python
# routes/auth.py
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.dashboard'))
    return render_template('auth/signup.html', form=form)
```

**Next.js (target):**
```typescript
// app/signup/page.tsx
'use client'
import { useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (!error) {
      // Redirect to dashboard
    }
  }
  
  return (
    <form onSubmit={handleSignup}>
      {/* Form fields */}
    </form>
  )
}
```

### Database Queries
**Flask (current):**
```python
# Get user's transactions
transactions = Transaction.query.filter_by(
    user_id=current_user.id,
    is_deleted=False
).order_by(Transaction.date.desc()).all()
```

**Next.js (target):**
```typescript
// Get user's transactions
const { data: transactions, error } = await supabase
  .from('transactions')
  .select('*')
  .eq('user_id', user.id)
  .eq('is_deleted', false)
  .order('date', { ascending: false })
```

---

## 🚀 Quick Start Commands for New Chat

### 1. Create Next.js Project
```bash
cd "C:\Users\nkeit\OneDrive\Desktop\budgeting app"
npx create-next-app@latest swiftbudget-nextjs --typescript --tailwind --app --use-npm
cd swiftbudget-nextjs
```

### 2. Install Dependencies
```bash
npm install @supabase/supabase-js
npm install @supabase/auth-helpers-nextjs
npm install recharts
npm install date-fns
npm install lucide-react
npx shadcn-ui@latest init
```

### 3. Set Up Supabase
1. Go to https://supabase.com
2. Create new project: `swiftbudget`
3. Copy Project URL and anon key
4. Create `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Run Development Server
```bash
npm run dev
# Open http://localhost:3000
```

---

## 📝 Key Differences: Flask vs Next.js

### Routing
- **Flask:** Decorator-based routes (`@app.route('/dashboard')`)
- **Next.js:** File-based routing (`app/dashboard/page.tsx`)

### Templates
- **Flask:** Jinja2 templates (`.html` files)
- **Next.js:** React components (`.tsx` files with JSX)

### Database
- **Flask:** SQLAlchemy ORM with Python classes
- **Next.js:** Supabase client with JavaScript/TypeScript

### Forms
- **Flask:** Flask-WTF with server-side validation
- **Next.js:** React Hook Form or native forms with client-side validation

### Authentication
- **Flask:** Flask-Login with sessions
- **Next.js:** Supabase Auth with JWT tokens

---

## 🎨 UI Component Mapping

### Flask → Next.js Component Equivalents

**Flask Template:**
```html
<!-- templates/dashboard.html -->
{% extends "base.html" %}
{% block content %}
<div class="container">
  <h1>Dashboard</h1>
  <p>Balance: {{ balance }}</p>
</div>
{% endblock %}
```

**Next.js Component:**
```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  const [balance, setBalance] = useState(0)
  
  return (
    <div className="container">
      <h1>Dashboard</h1>
      <p>Balance: {balance}</p>
    </div>
  )
}
```

---

## 🔐 Environment Variables

### Current (Flask - Render)
```env
FLASK_ENV=production
SECRET_KEY=db75e12de95a62b3c7d99b0153dd44efc7948134d4f9e88b1f0b2c71363116c8
DATABASE_URL=postgresql+psycopg://...
CLOUDINARY_CLOUD_NAME=dszhg6iac
CLOUDINARY_API_KEY=735764651149642
CLOUDINARY_API_SECRET=WSZLcfIVfzmrO1ICundQ7B-5kh8
MAIL_USERNAME=nkeithpaul@gmail.com
MAIL_PASSWORD=xttvvmyderzkwbdv
SESSION_COOKIE_SECURE=True
CURRENCY_SYMBOL=MK
CURRENCY_CODE=MWK
```

### New (Next.js - Netlify)
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
NEXT_PUBLIC_CURRENCY_SYMBOL=MK
NEXT_PUBLIC_CURRENCY_CODE=MWK
```

---

## 📊 Success Criteria

### Must-Have Features (MVP)
- [ ] User signup/login/logout
- [ ] Profile management with image upload
- [ ] Add/edit/delete transactions
- [ ] Add/edit/delete categories
- [ ] Dashboard with balance and charts
- [ ] Filter transactions by date/category
- [ ] Budget goals with progress tracking
- [ ] Projects/tags for transactions
- [ ] Responsive design (mobile-friendly)
- [ ] Deployed to Netlify

### Nice-to-Have Features (v1.1)
- [ ] Email notifications
- [ ] Recurring transactions
- [ ] Data export (CSV)
- [ ] Advanced filtering
- [ ] Receipt OCR scanner
- [ ] Dark mode

---

## 🐛 Common Pitfalls to Avoid

1. **Don't mix server and client components incorrectly**
   - Use `'use client'` directive when needed
   - Keep server components for data fetching

2. **Don't forget to handle loading states**
   - Always show loading indicators
   - Handle errors gracefully

3. **Don't expose sensitive keys**
   - Use `NEXT_PUBLIC_` prefix only for public keys
   - Never commit `.env.local` to git

4. **Don't skip TypeScript types**
   - Define interfaces for all data structures
   - Use type inference when possible

5. **Don't forget Supabase Row Level Security (RLS)**
   - Enable RLS on all tables
   - Users should only access their own data

---

## 📞 Support & Resources

### When Starting New Chat
**Say this to Cascade:**
> "I'm rebuilding SwiftBudget from Python/Flask to Next.js/Supabase for Netlify deployment. I have the NEXTJS_MIGRATION_GUIDE.md file that explains everything. I'm a beginner in JavaScript/React and need help learning as we build. Let's start with Phase 1: Project Setup."

### Key Files to Reference
- `NEXTJS_MIGRATION_GUIDE.md` (this file)
- `README.md` (current Python app documentation)
- `DEPLOYMENT.md` (current deployment guide)
- Database schema (see above)

### GitHub Repositories
- **Current Python App:** https://github.com/Keithpaul98/SwiftBudget
- **New Next.js App:** Create new repo or use same repo with different branch

---

## 🎯 Next Steps

1. **Open new chat with Cascade**
2. **Share this guide** (NEXTJS_MIGRATION_GUIDE.md)
3. **Start with Phase 1:** Project setup
4. **Learn as you build:** Cascade will teach you React/Next.js concepts
5. **Deploy to Netlify:** Once MVP is complete

---

**Good luck with the migration! The new stack will be much easier to deploy and maintain.** 🚀

---

**Last Updated:** March 7, 2026  
**Created by:** Cascade AI Assistant  
**For:** Keith Paul (@Keithpaul98)
