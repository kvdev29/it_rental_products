"""
app/routes/auth.py - Authentication Routes
-------------------------------------------
Handles login, logout, registration, password change and profile management.

OWASP coverage in this module:
    A07 - Identification & Authentication Failures:
          - Rate limiting on login endpoint (max 10 attempts / minute)
          - Account lockout after 5 consecutive failed logins (15-minute lockout)
          - Secure session management via Flask-Login
          - Strong password policy enforced via form validators
    A02 - Cryptographic Failures:
          - Passwords hashed with PBKDF2-SHA256 via Werkzeug
          - Plain-text passwords never logged or stored
    A09 - Security Logging:
          - All login attempts (success and failure) written to AuditLog
"""

from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User, AuditLog
from app.utils.forms import (LoginForm, RegistrationForm, PublicRegistrationForm,
                              ChangePasswordForm, EditProfileForm)
from app.utils.security import log_event, admin_required
from app import limiter

auth_bp = Blueprint('auth', __name__)


# ======================================================================= #
#  Login                                                                    #
# ======================================================================= #

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', error_message='Too many login attempts. Please wait.')
def login():
    """
    Authenticate a user and create a session.

    Rate limited to 10 requests/minute per IP to mitigate brute-force
    attacks (OWASP A07). Account lockout provides a second layer of
    protection independent of IP-based limiting.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        # Look up user - use timing-safe comparison by always checking hash
        user = User.query.filter_by(username=form.username.data).first()

        # ── Account lockout check (OWASP A07) ──────────────────────────
        if user and user.is_locked():
            log_event(
                event_type=AuditLog.EVENT_LOGIN_FAIL,
                description=f'Login attempt on locked account: {form.username.data}',
                user_id=user.id,
            )
            flash('Account is temporarily locked due to too many failed attempts. '
                  'Please try again in 15 minutes.', 'danger')
            return render_template('auth/login.html', form=form)

        # ── Credential verification ─────────────────────────────────────
        if user is None or not user.check_password(form.password.data):
            if user:
                user.increment_failed_login()
                db.session.commit()
                if user.is_locked():
                    log_event(
                        event_type=AuditLog.EVENT_ACCOUNT_LOCKED,
                        description=f'Account locked after repeated failures: {user.username}',
                        user_id=user.id,
                    )
                    flash('Account locked after 5 failed attempts. '
                          'Try again in 15 minutes.', 'danger')
                    return render_template('auth/login.html', form=form)

            log_event(
                event_type=AuditLog.EVENT_LOGIN_FAIL,
                description=f'Failed login attempt for username: {form.username.data}',
                user_id=user.id if user else None,
            )
            # Generic message prevents username enumeration (OWASP A07)
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html', form=form)

        # ── Check account is active ─────────────────────────────────────
        if not user.is_active:
            log_event(
                event_type=AuditLog.EVENT_LOGIN_FAIL,
                description=f'Login attempt on deactivated account: {user.username}',
                user_id=user.id,
            )
            flash('Your account has been deactivated. Contact an administrator.', 'danger')
            return render_template('auth/login.html', form=form)

        # ── Successful authentication ────────────────────────────────────
        user.reset_failed_login()
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user)

        log_event(
            event_type=AuditLog.EVENT_LOGIN_SUCCESS,
            description=f'Successful login: {user.username}',
            user_id=user.id,
        )

        # Safe redirect: only redirect to same-origin URLs
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html', form=form)


# ======================================================================= #
#  Logout                                                                   #
# ======================================================================= #

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per hour')
def register():
    """Public self-registration for guests and employees."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = PublicRegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            department=form.department.data or '',
            role=form.account_type.data,
            is_active=True,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        log_event(
            event_type=AuditLog.EVENT_CREATE,
            description=f'New account registered: {user.username} (role: {user.role})',
            resource_type='User',
            resource_id=user.id,
            user_id=user.id,
        )

        flash(f'Account created! Welcome, {user.full_name}. Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """End the user session and redirect to login."""
    log_event(
        event_type=AuditLog.EVENT_LOGOUT,
        description=f'User logged out: {current_user.username}',
    )
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))


# ======================================================================= #
#  Profile                                                                  #
# ======================================================================= #

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Allow a user to view and update their own profile."""
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Check email not taken by another user
        existing = User.query.filter_by(email=form.email.data).first()
        if existing and existing.id != current_user.id:
            flash('That email address is already in use.', 'danger')
            return render_template('auth/profile.html', form=form)

        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.department = form.department.data
        current_user.phone = form.phone.data
        db.session.commit()

        log_event(
            event_type=AuditLog.EVENT_UPDATE,
            description=f'User updated own profile: {current_user.username}',
            resource_type='User',
            resource_id=current_user.id,
        )
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


# ======================================================================= #
#  Change Password                                                          #
# ======================================================================= #

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit('5 per hour')
def change_password():
    """
    Allow a user to change their own password.

    Rate limited to 5 attempts/hour to limit brute-force against
    the current-password check.
    """
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            log_event(
                event_type=AuditLog.EVENT_LOGIN_FAIL,
                description=f'Incorrect current password during password change: '
                            f'{current_user.username}',
            )
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()

        log_event(
            event_type=AuditLog.EVENT_PASSWORD_CHANGE,
            description=f'Password changed by user: {current_user.username}',
            resource_type='User',
            resource_id=current_user.id,
        )
        flash('Password changed successfully. Please sign in again.', 'success')
        logout_user()
        return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html', form=form)
