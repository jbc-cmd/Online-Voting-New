# Univote - Secure Online Voting System for Schools and Universities

**Univote** is a fully functional, secure online voting system built with Python Django and PostgreSQL. Admins manage elections through a custom admin panel, and students vote through a public Google Form-style voting page — no student login or dashboard required.

---

## Features

- ✅ Custom admin dashboard (not Django's default `/admin/`)
- ✅ Election CRUD with status management (Draft, Active, Paused, Closed, Archived)
- ✅ AJAX voting toggle switch per election
- ✅ Unique voting link generation per election
- ✅ Google Form-style public voting page (no student login)
- ✅ Student ID + official email verification
- ✅ OTP email verification (hashed, expirable, limited attempts)
- ✅ Eligibility checking (USC, Department, Program, Class, Organization)
- ✅ Duplicate vote prevention with DB constraints + `transaction.atomic()`
- ✅ Anonymous ballot storage (no student name linked to vote choice)
- ✅ Ballot number receipt system
- ✅ Analytics dashboard with Chart.js
- ✅ Export: CSV, Excel (openpyxl), PDF (reportlab)
- ✅ Audit logs + verification logs
- ✅ System evaluation report
- ✅ Student CSV/Excel import
- ✅ Department, Program, Class, Organization management
- ✅ Candidate photo uploads
- ✅ Mobile-friendly responsive design

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Django 5.x |
| Database | PostgreSQL |
| Frontend | Django Templates + Bootstrap 5 + JavaScript |
| Charts | Chart.js |
| Email/OTP | Django Email (SMTP or console) |
| Excel Export | openpyxl |
| PDF Export | reportlab |
| Environment | python-decouple |

---

## Installation Guide

### 1. Prerequisites

- Python 3.10+ installed
- PostgreSQL installed and running
- Git (optional)

### 2. Clone / Download the Project

```bash
cd "c:\ONLINE VOTING NEW"
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 4. Install Dependencies

```bash
cd univote
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
copy .env.example .env
```

Edit `.env` and fill in your values:

```env
SECRET_KEY=your-random-secret-key-here
DEBUG=True
DB_NAME=univote_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
SITE_URL=http://localhost:8000
```

> **Note:** With `EMAIL_BACKEND=console`, OTPs will print to your terminal instead of being sent by email. This is perfect for local development.

### 6. Create PostgreSQL Database

Open pgAdmin or psql and run:

```sql
CREATE DATABASE univote_db;
```

### 7. Run Migrations

```bash
python manage.py makemigrations accounts
python manage.py makemigrations students
python manage.py makemigrations elections
python manage.py makemigrations voting
python manage.py makemigrations audit
python manage.py migrate
```

### 8. Create Cache Table (for rate limiting)

```bash
python manage.py createcachetable
```

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 10. Load Seed Data

```bash
python seed/seed_data.py
```

This creates:
- 3 admin accounts
- 3 departments, 4 programs, 6 classes, 2 organizations
- 20 sample students
- 5 elections (USC, Department, Program, Organization, Class)
- Positions and candidates for each election

### 11. Run the Development Server

```bash
python manage.py runserver
```

Open your browser at: **http://localhost:8000**

---

## Default Credentials (after seeding)

| Role | Username | Password |
|---|---|---|
| Super Admin | `superadmin` | `Admin@1234` |
| CCS Admin | `admin_ccs` | `Admin@1234` |
| CBA Admin | `admin_cba` | `Admin@1234` |

**Admin Panel:** http://localhost:8000/admin-panel/login/

---

## Sample Voting Links (after seeding)

| Election | URL |
|---|---|
| USC Election 2026 (Active) | http://localhost:8000/vote/usc-election-2026/ |
| CCS Department Election (Active) | http://localhost:8000/vote/ccs-department-election-2026/ |
| BSIT Program Election (Draft) | http://localhost:8000/vote/bsit-program-election-2026/ |

---

## Sample Student Credentials (for testing voting)

| Student ID | Official School Email |
|---|---|
| 2024-0001 | juan.delacruz@ccs.edu |
| 2024-0002 | maria.santos@ccs.edu |
| 2024-0003 | jose.reyes@ccs.edu |
| 2024-0008 | marco.torres@ccs.edu |
| 2024-0010 | antonio.ramos@cba.edu |

> When using console email backend, the OTP will appear in your terminal after submitting credentials.

---

## URL Structure

### Admin Panel

| Route | Description |
|---|---|
| `/admin-panel/login/` | Admin login |
| `/admin-panel/dashboard/` | Main dashboard |
| `/admin-panel/elections/` | Election list |
| `/admin-panel/elections/create/` | Create election |
| `/admin-panel/elections/<id>/edit/` | Edit election + toggle |
| `/admin-panel/elections/<id>/positions/` | Manage positions |
| `/admin-panel/elections/<id>/candidates/` | Manage candidates |
| `/admin-panel/elections/<id>/results/` | View results |
| `/admin-panel/elections/<id>/export/csv/` | Export CSV |
| `/admin-panel/elections/<id>/export/excel/` | Export Excel |
| `/admin-panel/elections/<id>/export/pdf/` | Export PDF |
| `/admin-panel/students/` | Student management |
| `/admin-panel/students/import/` | Import CSV/Excel |
| `/admin-panel/departments/` | Department management |
| `/admin-panel/programs/` | Program management |
| `/admin-panel/classes/` | Class management |
| `/admin-panel/organizations/` | Organization management |
| `/admin-panel/analytics/` | Analytics & charts |
| `/admin-panel/audit-logs/` | Audit logs |
| `/admin-panel/verification-logs/` | Verification logs |
| `/admin-panel/evaluation/` | System evaluation |

### Voting (Public)

| Route | Description |
|---|---|
| `/vote/<slug>/` | Credential form (Step 1) |
| `/vote/<slug>/send-otp/` | Send OTP (Step 2) |
| `/vote/<slug>/verify-otp/` | OTP entry (Step 3) |
| `/vote/<slug>/ballot/` | Ballot form (Step 4) |
| `/vote/<slug>/review/` | Review selections (Step 5) |
| `/vote/<slug>/submit/` | Submit ballot (Step 6) |
| `/vote/<slug>/receipt/<ballot_number>/` | Ballot receipt (Step 7) |

---

## Security Features

- OTP: 6-digit, SHA-256 hashed, 10-min expiry, max 5 attempts
- No plain OTP stored in database
- Session-based verification state (not URL-based)
- CSRF protection on all forms
- Server-side validation of all election rules
- `transaction.atomic()` on ballot submission
- DB-level `unique_together` on VoterParticipation (one vote per student per election)
- Vote anonymity: `Vote` model stores only `ballot_id` + `candidate_id`
- Audit logging on all admin actions
- Verification logging on all student attempts

---

## Django Apps Structure

```
univote/
├── accounts/     — Admin auth, login, dashboard
├── students/     — Student records, departments, programs, classes, organizations
├── elections/    — Election CRUD, positions, candidates, eligibility rules
├── voting/       — Public voting flow (7-step process), OTP, ballot, receipt
├── analytics/    — Charts and statistics
├── exports/      — CSV, Excel, PDF generation
├── audit/        — Audit logs, verification logs, system evaluation
├── templates/
│   ├── base/           — admin_base.html, voting_base.html
│   ├── admin_panel/    — All admin page templates
│   └── voting/         — All voting page templates
├── static/
│   ├── css/admin.css
│   ├── css/voting.css
│   ├── js/admin.js
│   └── js/voting.js
├── seed/seed_data.py
├── requirements.txt
└── .env.example
```

---

## Student CSV Import Format

Create a `.csv` file with these columns:

```csv
student_id_number,official_school_email,first_name,last_name,department_code,program_code,year_level,section
2024-0101,student@school.edu,John,Doe,CCS,BSIT,2,A
```

---

## System Evaluation

Access the system evaluation page at `/admin-panel/evaluation/` to review:

- Vote count accuracy
- Successful vote submission rate
- Failed attempt rate
- Duplicate vote prevention count
- OTP success/failure rates
- Voter turnout
- Admin-editable notes for usability, reliability, security, and performance

---

## License

This project is for educational use. Built for school and university election management.
