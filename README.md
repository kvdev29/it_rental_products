# Office Device Rental Portal

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0.3-green)
![Tests](https://img.shields.io/badge/tests-46%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A web application that lets office staff borrow equipment — headsets, keyboards, mice, webcams and more — without any paperwork or waiting for approval. Staff log in, pick what they need from the catalog, confirm a return date, and the item is theirs for the day. Admins manage the catalog and keep an eye on what's out and what's overdue.

Built with Flask as a university project demonstrating secure web application development aligned with the OWASP Top 10.

---

## Table of Contents

- [What it does](#what-it-does)
- [Screenshots](#screenshots)
- [Tech Stack](#tech-stack)
- [Security (OWASP Top 10)](#security-owasp-top-10)
- [Quick Start](#quick-start)
- [Test Accounts](#test-accounts)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Docker](#docker)
- [SDLC Summary](#sdlc-summary)

---

## What it does

### For Staff (Employee & Guest accounts)
- Browse a catalog of available devices, grouped by category
- Rent a device instantly — no approval queue
- View everything currently checked out with its return date
- Mark a device returned with one click
- Full rental history on the dashboard

### For Admins
- Add, edit and enable/disable items in the rental catalog
- See all active and overdue rentals across every user
- Manage user accounts (create, edit, deactivate)
- View the full immutable audit log (every login, rental, return and access denial)
- Standard IT helpdesk features: asset tracking, support tickets

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
| Testing | pytest + pytest-flask |
| Database | SQLite |
| Containerisation | Docker + Docker Compose |

---

## Security (OWASP Top 10)

| OWASP 2021 | Risk | How GearDesk defends against it |
|---|---|---|
| **A01** Broken Access Control | Admin-only routes are protected by an `@admin_required` decorator that returns 403 and writes to the audit log when a regular user attempts access. Users can only see their own rentals. | ✅ |
| **A02** Cryptographic Failures | Passwords are hashed with PBKDF2-SHA256 via Werkzeug. Plain-text passwords are never logged or stored anywhere. Session cookies are marked `HttpOnly` and `Secure` in production. | ✅ |
| **A03** Injection & XSS | SQLAlchemy ORM uses parameterised queries throughout — SQL injection attempts in login or search fields are treated as literal strings. `bleach.clean()` strips HTML tags on input; Jinja2 auto-escaping encodes any remaining HTML on output. | ✅ |
| **A05** Security Misconfiguration | Seven HTTP security headers are applied to every response via an `after_request` hook. A strict Content Security Policy limits which resources the browser will load. | ✅ |
| **A07** Authentication Failures | Login is rate-limited to 10 requests per minute per IP. Accounts are locked for 15 minutes after 5 consecutive failed attempts. Error messages are deliberately generic to prevent username enumeration. | ✅ |
| **A09** Logging & Monitoring | Every significant event is written to an `AuditLog` table: logins, logouts, failed attempts, lockouts, access denials, and all create/update/delete actions. Records include timestamp, user, IP address and description. The table is INSERT-only — no updates or deletes are performed on it. | ✅ |

### Security headers on every response

```
X-Content-Type-Options:  nosniff
X-Frame-Options:         DENY
X-XSS-Protection:        1; mode=block
Referrer-Policy:         strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; ...
Permissions-Policy:      camera=(), microphone=(), geolocation=()
```

---

## Quick Start

### Requirements
- Python 3.11 or later
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/geardesk.git
cd geardesk

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database with sample data
python seed.py

# 5. Start the development server
python run.py
```

The app runs at **http://localhost:5001**

---

## Test Accounts

Seeded automatically by `seed.py`:

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `Admin@12345` | Administrator | Full access — admin dashboard, catalog management, audit log |
| `alice.jones` | `Alice@12345` | Employee | Has an active sample rental on the dashboard |
| `bob.smith` | `Bob@123456` | Employee | Engineering department |
| `carol.white` | `Carol@1234` | Employee | HR department |
| `dave.brown` | `Dave@12345` | Employee | **Deactivated account** — use to test A07 defence |

> Change all passwords before any non-demo deployment.

---

## Running Tests

The test suite covers authentication, role-based access control, SQL injection, XSS, security headers, account lockout, CRUD operations, and password policy — 46 tests in total.

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific group
pytest tests/ -v -k TestAccessControl
pytest tests/ -v -k TestSQLInjection
pytest tests/ -v -k TestSecurityHeaders
```

### What the tests cover

| Test Class | OWASP | What is tested |
|---|---|---|
| `TestAuthentication` | A07 | Login, logout, wrong password, inactive account, session clearing |
| `TestAccessControl` | A01 | Admin vs user role enforcement, 403 responses, access denials written to audit log |
| `TestSQLInjection` | A03 | `OR 1=1`, UNION SELECT, comment-based attacks, DROP TABLE in search |
| `TestXSSPrevention` | A03 | Script tags stripped, img onerror stripped, Jinja2 encoding in response body |
| `TestSecurityHeaders` | A05 | All six headers present and correct values |
| `TestAccountLockout` | A07 | Account locked after 5 failures, lockout message shown, event written to audit log |
| `TestAssetCRUD` | A01, A09 | Admin can create/edit, regular user denied, duplicate tag rejected, audit log entry created |
| `TestTicketCRUD` | A01 | Raise ticket, denied access to another user's ticket, admin can view all |
| `TestPasswordPolicy` | A07 | Weak password rejected at registration, mismatched confirmation rejected |
| `TestCSRFProtection` | A01 | CSRF meta tag present confirming Flask-WTF is active |

---

## Project Structure

```
geardesk/
├── app/
│   ├── __init__.py              # App factory — extensions, blueprints, error handlers
│   ├── models/__init__.py       # SQLAlchemy models: User, RentalItem, Rental,
│   │                            #   Asset, Ticket, Comment, AuditLog
│   ├── routes/
│   │   ├── auth.py              # Login, logout, register, profile, change password
│   │   ├── main.py              # Dashboard (admin and user views)
│   │   ├── rentals.py           # Rental catalog, request, return, admin management
│   │   ├── assets.py            # IT asset CRUD (admin)
│   │   ├── tickets.py           # Helpdesk ticket CRUD + comments
│   │   └── admin.py             # User management + audit log
│   ├── utils/
│   │   ├── security.py          # @admin_required, security headers, bleach sanitisation,
│   │   │                        #   log_event() audit helper
│   │   └── forms.py             # WTForms definitions with CSRF + server-side validators
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Navbar, flash messages, footer
│   │   ├── auth/                # Login, register, profile, change password
│   │   ├── rentals/             # Catalog, request form, my rentals, admin views
│   │   ├── main/                # Dashboard (admin + user)
│   │   ├── assets/              # Asset list, detail, create/edit
│   │   ├── tickets/             # Ticket list, detail, create/edit
│   │   ├── admin/               # User management
│   │   └── errors/              # 400, 403, 404, 429, 500 pages
│   └── static/css/main.css      # Full application stylesheet
├── tests/
│   └── test_app.py              # 46-test pytest suite
├── config.py                    # Development / Testing / Production config classes
├── run.py                       # Entry point
├── seed.py                      # Creates tables and populates sample data
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Docker

```bash
# Build and start
docker compose up --build

# Seed the database inside the container
docker compose exec web python seed.py

# Stop
docker compose down
```

---

## SDLC Summary

### Planning
Identified the problem: staff borrowing office equipment informally with no tracking, no record of who has what, and no way to see availability. Defined three user roles (admin, employee, guest), core features (rental catalog, instant checkout, return flow, overdue tracking, admin oversight), and security requirements mapped to OWASP Top 10.

### Design
Designed the relational data model (`User`, `RentalItem`, `Rental`, `Asset`, `Ticket`, `AuditLog`). Chose Flask for the backend, SQLite for the database, and WTForms for server-side validated forms. Planned role-based access control enforced at the route level and a split-panel authentication UI.

### Development
Implemented using Flask's Blueprint pattern to separate concerns (auth, rentals, assets, tickets, admin). Applied security controls at every layer: parameterised queries via SQLAlchemy, input sanitisation with bleach, output escaping via Jinja2, CSRF tokens on all forms, rate limiting and account lockout on authentication endpoints, and seven HTTP security headers on all responses.

### Testing
46 automated unit and integration tests written with pytest, covering authentication flows, role enforcement (OWASP A01), SQL injection attempts (OWASP A03), XSS payloads (OWASP A03), security header verification (OWASP A05), account lockout (OWASP A07), audit log integrity (OWASP A09), and full CRUD lifecycle tests for assets and tickets.

---

## Academic References

- OWASP Foundation (2021) *OWASP Top Ten*. Available at: https://owasp.org/Top10/
- Grinberg, M. (2018) *Flask Web Development*. 2nd edn. O'Reilly Media.
- OWASP (2023) *OWASP Secure Headers Project*. Available at: https://owasp.org/www-project-secure-headers/
- Werkzeug (2024) *Security Helpers*. Available at: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#module-werkzeug.security
- Python Software Foundation (2024) *SQLite3 — DB-API 2.0 interface*. Available at: https://docs.python.org/3/library/sqlite3.html
