"""
Shared security helpers — access control decorators, input sanitisation,
HTTP headers, and the audit log writer.
"""

import json
import bleach
from functools import wraps
from datetime import datetime
from flask import request, abort, current_app, g
from flask_login import current_user
from app.models import db, AuditLog


# access control

def admin_required(f):
    """Restrict route to admin users; logs and 403s everyone else."""
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
    """Allow access only to the resource owner or an admin."""
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


# input sanitisation

# Allowed HTML tags for rich-text fields (ticket descriptions, comments)
ALLOWED_TAGS = []           # Plaintext only - strip ALL HTML
ALLOWED_ATTRIBUTES = {}

def sanitize_input(value):
    """Strip HTML from a string using bleach."""
    if value is None:
        return value
    # bleach.clean strips tags; linkify=False prevents URL conversion
    return bleach.clean(str(value), tags=ALLOWED_TAGS,
                        attributes=ALLOWED_ATTRIBUTES, strip=True)


def sanitize_form_data(form_data):
    """Run sanitize_input on every string value in a form.data dict."""
    cleaned = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            cleaned[key] = sanitize_input(value)
        else:
            cleaned[key] = value
    return cleaned


# HTTP security headers

def apply_security_headers(response):
    """Attach security headers to every outgoing response."""
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


# audit logging

def log_event(event_type, description, resource_type=None,
              resource_id=None, user_id=None, extra_data=None):
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
    # same as log_event but doesn't commit — use when bundled with another db write
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
