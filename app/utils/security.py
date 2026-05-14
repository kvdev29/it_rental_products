"""
app/utils/security.py - Security Utilities
-------------------------------------------
Centralised security helpers used across the application.

OWASP Top 10 coverage:
    A01 - Broken Access Control    : role_required / admin_required decorators
    A02 - Cryptographic Failures   : handled in models (Werkzeug hashing)
    A03 - Injection                : sanitize_input using bleach
    A05 - Security Misconfiguration: apply_security_headers middleware
    A07 - Auth Failures            : rate limiting (Flask-Limiter, see __init__.py)
    A09 - Logging & Monitoring     : log_event audit function

Reference: OWASP Top 10 (2021)
https://owasp.org/Top10/
"""

import json
import bleach
from functools import wraps
from datetime import datetime
from flask import request, abort, current_app, g
from flask_login import current_user
from app.models import db, AuditLog


# ======================================================================= #
#  Access Control Decorators (OWASP A01)                                    #
# ======================================================================= #

def admin_required(f):
    """
    Decorator that restricts a route to admin users only.

    If a non-admin authenticated user attempts access, a 403 Forbidden
    response is returned and the attempt is logged to the audit trail.

    Usage:
        @app.route('/admin/users')
        @login_required
        @admin_required
        def manage_users():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            # Log the unauthorised access attempt
            log_event(
                event_type=AuditLog.EVENT_ACCESS_DENIED,
                description=(
                    f'Non-admin user "{current_user.username}" attempted to '
                    f'access admin-only resource: {request.path}'
                ),
                resource_type='Route',
            )
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def owner_or_admin_required(get_owner_id):
    """
    Decorator factory that allows access only to the resource owner or admins.

    Args:
        get_owner_id: callable that accepts (kwargs) and returns the owner's user_id

    Usage:
        @ticket_bp.route('/<int:ticket_id>/edit')
        @login_required
        @owner_or_admin_required(lambda kw: Ticket.query.get(kw['ticket_id']).raised_by_id)
        def edit_ticket(ticket_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            owner_id = get_owner_id(kwargs)
            if not current_user.is_admin and current_user.id != owner_id:
                log_event(
                    event_type=AuditLog.EVENT_ACCESS_DENIED,
                    description=(
                        f'User "{current_user.username}" attempted to access '
                        f'resource owned by user ID {owner_id}: {request.path}'
                    ),
                )
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ======================================================================= #
#  Input Sanitisation (OWASP A03 - XSS Prevention)                         #
# ======================================================================= #

# Allowed HTML tags for rich-text fields (ticket descriptions, comments)
ALLOWED_TAGS = []           # Plaintext only - strip ALL HTML
ALLOWED_ATTRIBUTES = {}

def sanitize_input(value):
    """
    Strip all HTML tags from a string to prevent XSS.

    Uses bleach to clean input before it reaches the database.
    Jinja2 auto-escaping provides a second layer of protection on output.

    Args:
        value (str): Raw user input

    Returns:
        str: Sanitised string with all HTML stripped
    """
    if value is None:
        return value
    # bleach.clean strips tags; linkify=False prevents URL conversion
    return bleach.clean(str(value), tags=ALLOWED_TAGS,
                        attributes=ALLOWED_ATTRIBUTES, strip=True)


def sanitize_form_data(form_data):
    """
    Sanitise all string fields in a dictionary (e.g. form.data).

    Args:
        form_data (dict): WTForms form.data dictionary

    Returns:
        dict: New dict with all string values sanitised
    """
    cleaned = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            cleaned[key] = sanitize_input(value)
        else:
            cleaned[key] = value
    return cleaned


# ======================================================================= #
#  Security Headers (OWASP A05 - Security Misconfiguration)                 #
# ======================================================================= #

def apply_security_headers(response):
    """
    Add HTTP security headers to every response.

    Headers applied:
        X-Content-Type-Options     : Prevents MIME sniffing
        X-Frame-Options            : Prevents clickjacking
        X-XSS-Protection           : Legacy XSS filter (belt-and-braces)
        Referrer-Policy            : Limits referrer information leakage
        Content-Security-Policy    : Restricts resource loading (OWASP A03)
        Strict-Transport-Security  : Forces HTTPS (production only)
        Permissions-Policy         : Disables sensitive browser APIs

    Reference: OWASP Secure Headers Project
    https://owasp.org/www-project-secure-headers/
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Deny framing (clickjacking protection)
    response.headers['X-Frame-Options'] = 'DENY'

    # Legacy XSS filter
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Limit referrer leakage
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Content Security Policy - restricts where resources can load from
    csp_directives = current_app.config.get('CSP_DIRECTIVES', {})
    if csp_directives:
        csp_string = '; '.join(
            f"{key} {value}" for key, value in csp_directives.items()
        )
        response.headers['Content-Security-Policy'] = csp_string

    # HSTS - only in production (requires HTTPS)
    if not current_app.debug:
        response.headers['Strict-Transport-Security'] = \
            'max-age=31536000; includeSubDomains'

    # Disable camera/microphone/geolocation
    response.headers['Permissions-Policy'] = \
        'camera=(), microphone=(), geolocation=()'

    return response


# ======================================================================= #
#  Audit Logging (OWASP A09 - Security Logging & Monitoring)               #
# ======================================================================= #

def log_event(event_type, description, resource_type=None,
              resource_id=None, user_id=None, extra_data=None):
    """
    Write an entry to the AuditLog table.

    Called throughout the application to maintain an immutable audit trail.
    Records: who did what, to which resource, from where, and when.

    Args:
        event_type   (str): AuditLog.EVENT_* constant
        description  (str): Human-readable description of the event
        resource_type(str): Model name affected ('Asset', 'Ticket', etc.)
        resource_id  (int): Primary key of the affected record
        user_id      (int): Override user; defaults to current_user.id
        extra_data   (dict): Additional structured context (stored as JSON)
    """
    # Determine actor
    if user_id is None:
        try:
            uid = current_user.id if current_user.is_authenticated else None
        except Exception:
            uid = None
    else:
        uid = user_id

    # Capture request context safely
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua = request.headers.get('User-Agent', '')[:255]
    except RuntimeError:
        ip = None
        ua = None

    entry = AuditLog(
        user_id=uid,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip,
        user_agent=ua,
        extra_data=json.dumps(extra_data) if extra_data else None,
    )

    try:
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:
        # Audit logging must never crash the application
        current_app.logger.error(f'AuditLog write failed: {exc}')
        db.session.rollback()


def log_event_no_commit(event_type, description, resource_type=None,
                         resource_id=None, user_id=None, extra_data=None):
    """
    Add an AuditLog entry to the current session without committing.

    Use this when the audit log entry should be committed atomically
    with another database change (e.g. creating a Ticket and logging it
    in one transaction).
    """
    if user_id is None:
        try:
            uid = current_user.id if current_user.is_authenticated else None
        except Exception:
            uid = None
    else:
        uid = user_id

    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua = request.headers.get('User-Agent', '')[:255]
    except RuntimeError:
        ip, ua = None, None

    entry = AuditLog(
        user_id=uid,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip,
        user_agent=ua,
        extra_data=json.dumps(extra_data) if extra_data else None,
    )
    db.session.add(entry)
