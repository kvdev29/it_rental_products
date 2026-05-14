# 🛡️ SecureITSM — IT Service Management System

![CI](https://github.com/YOUR_USERNAME/secureit-itsm/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0.3-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A secure, full-stack IT Asset and Helpdesk Ticket Management System built with Flask. Developed as a Final Year project for BSc Digital & Technology Solutions, demonstrating secure application development principles aligned with the OWASP Top 10.

---

## 📋 Table of Contents

- [Features](#features)
- [Security Features (OWASP)](#security-features-owasp)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Test Accounts](#test-accounts)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Project Structure](#project-structure)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Features

### Admin Users Can:
- Full CRUD on IT assets (laptops, servers, software licences, etc.)
- Full CRUD on helpdesk tickets + assignment to staff
- Manage all user accounts (create, edit, deactivate, reset passwords)
- Post internal notes on tickets (hidden from regular users)
- View the immutable security audit log
- Filter/search/paginate all records

### Regular Users Can:
- Raise and track their own helpdesk tickets
- Add comments to their own tickets
- View IT assets assigned to them
- Update their own profile and password

---

## Security Features (OWASP)

| OWASP 2021 | Risk | Implementation |
|---|---|---|
| **A01** Broken Access Control | Admin routes protected by `@admin_required` decorator; users can only access their own records; 403 logged to AuditLog | ✅ |
| **A02** Cryptographic Failures | Passwords hashed with PBKDF2-SHA256 (Werkzeug); HTTPS-only session cookies in production; no sensitive data in logs | ✅ |
| **A03** Injection / XSS | SQLAlchemy ORM parameterised queries prevent SQL injection; `bleach.clean()` strips all HTML on input; Jinja2 auto-escaping on output | ✅ |
| **A05** Security Misconfiguration | 7 security headers on every response: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy | ✅ |
| **A07** Auth Failures | Rate limiting (10 req/min on login, 5/hr on password change); account lockout after 5 fails (15 min); generic error messages prevent enumeration | ✅ |
| **A09** Logging & Monitoring | `AuditLog` table records every auth event, CRUD action, access denial; INSERT-only; includes IP address and user agent | ✅ |

### Security Headers Applied
```
X-Content-Type-Options:  nosniff
X-Frame-Options:         DENY
X-XSS-Protection:        1; mode=block
Referrer-Policy:         strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
Permissions-Policy:      camera=(), microphone=(), geolocation=()
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.0.3 |
| ORM | Flask-SQLAlchemy + SQLAlchemy 2.0 |
| Authentication | Flask-Login |
| Forms & CSRF | Flask-WTF + WTForms |
| Rate Limiting | Flask-Limiter |
| Database Migrations | Flask-Migrate |
| Input Sanitisation | bleach |
| Password Hashing | Werkzeug (PBKDF2-SHA256) |
| Testing | pytest + pytest-flask + coverage |
| Database | SQLite (dev) |
| CI/CD | GitHub Actions |
| Containerisation | Docker + Docker Compose |

---

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/secureit-itsm.git
cd secureit-itsm

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and set a strong SECRET_KEY

# 5. Seed the database with sample data
python seed.py

# 6. Start the development server
python run.py
```

The app will be available at **http://localhost:5000**

---

## Test Accounts

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `Admin@12345` | Administrator | Full access |
| `alice.jones` | `Alice@12345` | Standard User | Finance dept |
| `bob.smith` | `Bob@123456` | Standard User | Engineering dept |
| `carol.white` | `Carol@1234` | Standard User | HR dept |
| `dave.brown` | `Dave@12345` | Standard User | **Deactivated** — tests A07 |

> ⚠️ Change all passwords immediately in any non-demo deployment.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Run a specific test class
pytest tests/ -v -k TestAccessControl
```

### Test Coverage Areas

| Test Class | OWASP | What's Tested |
|---|---|---|
| `TestAuthentication` | A07 | Login, logout, inactive accounts, session clearing |
| `TestAccessControl` | A01 | Admin vs user role enforcement, 403 responses, audit logging |
| `TestSQLInjection` | A03 | OR 1=1, UNION SELECT, comment attacks, DROP TABLE in search |
| `TestXSSPrevention` | A03 | Script tags, img onerror, Jinja2 encoding in responses |
| `TestSecurityHeaders` | A05 | All 6 headers present and correct |
| `TestAccountLockout` | A07 | Lockout after 5 fails, audit log entry created |
| `TestAssetCRUD` | A01, A09 | Admin CRUD, user denied create, duplicate tag rejected |
| `TestTicketCRUD` | A01 | Raise ticket, denied others' tickets, admin views all |
| `TestPasswordPolicy` | A07 | Weak password rejected, mismatched confirmation rejected |
| `TestCSRFProtection` | A01 | CSRF token present in forms |

---

## Docker

```bash
# Build and run with Docker Compose
docker compose up --build

# Seed database inside container
docker compose exec web python seed.py

# Stop
docker compose down
```

---

## Project Structure

```
secureit-itsm/
├── .github/workflows/ci.yml     # GitHub Actions CI pipeline
├── app/
│   ├── __init__.py              # App factory + extension init
│   ├── models/__init__.py       # SQLAlchemy models (User, Asset, Ticket, AuditLog)
│   ├── routes/
│   │   ├── auth.py              # Login, logout, profile, change password
│   │   ├── main.py              # Dashboard
│   │   ├── assets.py            # Asset CRUD
│   │   ├── tickets.py           # Ticket CRUD + comments
│   │   └── admin.py             # User management + audit log
│   ├── utils/
│   │   ├── security.py          # OWASP decorators, headers, sanitisation, audit log
│   │   └── forms.py             # WTForms with CSRF + validators
│   ├── templates/               # Jinja2 HTML templates
│   └── static/css/main.css      # Stylesheet
├── tests/test_app.py            # Comprehensive pytest test suite
├── config.py                    # Dev / Test / Production configuration
├── run.py                       # Entry point + CLI commands
├── seed.py                      # Database seeder
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Local development stack
└── requirements.txt
```

---

## CI/CD Pipeline

Every push to `main` or `dev` automatically:

1. **Installs** all dependencies
2. **Runs pytest** across Python 3.11 and 3.12
3. **Generates** a coverage report (uploaded as a build artifact)
4. **Enforces** a minimum 70% code coverage threshold
5. **Lints** with flake8

See `.github/workflows/ci.yml` for the full pipeline definition.

---

## Academic References

- OWASP Foundation (2021) *OWASP Top Ten*. Available at: https://owasp.org/Top10/
- Grinberg, M. (2018) *Flask Web Development*. 2nd edn. O'Reilly Media.
- OWASP (2023) *OWASP Secure Headers Project*. Available at: https://owasp.org/www-project-secure-headers/
- Werkzeug (2024) *Security Helpers*. Available at: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#module-werkzeug.security
