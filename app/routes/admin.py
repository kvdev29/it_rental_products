"""
app/routes/admin.py - Admin Management Routes
----------------------------------------------
User management and audit log review (admin-only).

All routes protected by @login_required AND @admin_required.
Access attempts by non-admins are logged to the AuditLog.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db, User, AuditLog, Asset, Ticket
from app.utils.forms import RegistrationForm, AdminEditUserForm, SearchForm
from app.utils.security import admin_required, log_event, log_event_no_commit, sanitize_input

admin_bp = Blueprint('admin', __name__)


# ======================================================================= #
#  User Management                                                          #
# ======================================================================= #

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """List all users (admin only)."""
    search_term = request.args.get('query', '').strip()
    query = User.query

    if search_term:
        safe = sanitize_input(search_term)
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{safe}%'),
                User.email.ilike(f'%{safe}%'),
                User.full_name.ilike(f'%{safe}%'),
            )
        )

    users = query.order_by(User.username).all()
    return render_template('admin/users_list.html', users=users, search_term=search_term)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user account (admin only)."""
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=sanitize_input(form.username.data),
            email=sanitize_input(form.email.data),
            full_name=sanitize_input(form.full_name.data),
            department=sanitize_input(form.department.data),
            phone=sanitize_input(form.phone.data),
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        log_event_no_commit(
            event_type=AuditLog.EVENT_CREATE,
            description=f'User account created by admin {current_user.username}: '
                        f'{user.username} (role: {user.role})',
            resource_type='User', resource_id=user.id,
        )
        db.session.commit()

        flash(f'User "{user.username}" created successfully.', 'success')
        return redirect(url_for('admin.list_users'))

    return render_template('admin/user_form.html', form=form, title='Create User')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit a user's profile and role (admin only)."""
    user = User.query.get_or_404(user_id)
    form = AdminEditUserForm(obj=user)

    if form.validate_on_submit():
        old_role = user.role
        old_active = user.is_active

        user.full_name = sanitize_input(form.full_name.data)
        user.email = sanitize_input(form.email.data)
        user.department = sanitize_input(form.department.data)
        user.phone = sanitize_input(form.phone.data)
        user.role = form.role.data
        user.is_active = form.is_active.data

        changes = []
        if old_role != user.role:
            changes.append(f'role: {old_role} → {user.role}')
        if old_active != user.is_active:
            changes.append(f'active: {old_active} → {user.is_active}')
            event = AuditLog.EVENT_USER_ACTIVATED if user.is_active else AuditLog.EVENT_USER_DEACTIVATED
            log_event_no_commit(
                event_type=event,
                description=f'User {"activated" if user.is_active else "deactivated"}: '
                            f'{user.username} by {current_user.username}',
                resource_type='User', resource_id=user_id,
            )

        log_event_no_commit(
            event_type=AuditLog.EVENT_UPDATE,
            description=f'User {user.username} updated by admin {current_user.username}. '
                        f'Changes: {"; ".join(changes) if changes else "profile update"}',
            resource_type='User', resource_id=user_id,
        )
        db.session.commit()

        flash(f'User "{user.username}" updated.', 'success')
        return redirect(url_for('admin.list_users'))

    return render_template('admin/user_form.html', form=form,
                           title=f'Edit User: {user.username}', user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """
    Admin resets a user's password to a temporary value.
    The user must change it on next login.
    """
    from app.utils.forms import RegistrationForm
    user = User.query.get_or_404(user_id)

    # Generate a temporary password
    import secrets, string
    alphabet = string.ascii_letters + string.digits + '!@#$'
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    user.set_password(temp_password)
    db.session.commit()

    log_event(
        event_type=AuditLog.EVENT_PASSWORD_CHANGE,
        description=f'Admin {current_user.username} reset password for user {user.username}',
        resource_type='User', resource_id=user_id,
    )

    flash(f'Password for "{user.username}" reset. Temporary password: {temp_password}', 'warning')
    return redirect(url_for('admin.edit_user', user_id=user_id))


# ======================================================================= #
#  Audit Log                                                                #
# ======================================================================= #

@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    """
    View the security audit log (admin only).

    Supports filtering by event type, user, and date range.
    Paginated to avoid loading thousands of records at once.
    """
    event_filter = request.args.get('event_type', '')
    user_filter = request.args.get('user_id', '', type=str)
    page = request.args.get('page', 1, type=int)

    query = AuditLog.query

    if event_filter:
        query = query.filter_by(event_type=event_filter)

    if user_filter.isdigit():
        query = query.filter_by(user_id=int(user_filter))

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=25, error_out=False
    )

    # Available event types for filter dropdown
    event_types = [
        AuditLog.EVENT_LOGIN_SUCCESS, AuditLog.EVENT_LOGIN_FAIL,
        AuditLog.EVENT_LOGOUT, AuditLog.EVENT_ACCOUNT_LOCKED,
        AuditLog.EVENT_ACCESS_DENIED, AuditLog.EVENT_CREATE,
        AuditLog.EVENT_UPDATE, AuditLog.EVENT_DELETE,
        AuditLog.EVENT_PASSWORD_CHANGE,
    ]

    users = User.query.order_by(User.username).all()

    return render_template('admin/audit_log.html',
                           logs=logs,
                           event_types=event_types,
                           users=users,
                           current_event=event_filter,
                           current_user_id=user_filter)
