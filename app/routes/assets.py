"""
app/routes/assets.py - IT Asset Management Routes
---------------------------------------------------
Full CRUD for IT assets. Admin-only for create/update/delete.
All users can view assets assigned to them.

OWASP coverage:
    A01 - Broken Access Control : @admin_required on mutating operations
    A03 - Injection             : SQLAlchemy ORM parameterised queries
    A09 - Logging               : All CRUD operations logged to AuditLog
"""

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort)
from flask_login import login_required, current_user

from app.models import db, Asset, User, AuditLog
from app.utils.forms import AssetForm, ConfirmDeleteForm, SearchForm
from app.utils.security import admin_required, log_event, log_event_no_commit, sanitize_input

assets_bp = Blueprint('assets', __name__)


# ======================================================================= #
#  List Assets                                                              #
# ======================================================================= #

@assets_bp.route('/')
@login_required
def list_assets():
    """
    Display asset list.

    Admins: all assets with search/filter.
    Users: only assets assigned to them.
    """
    search_form = SearchForm(request.args, meta={'csrf': False})
    query = Asset.query

    if not current_user.is_admin:
        # Regular users only see their own assets
        query = query.filter_by(assigned_to_id=current_user.id)

    # Search filter (uses ORM - safe from SQL injection)
    search_term = request.args.get('query', '').strip()
    if search_term:
        safe_term = sanitize_input(search_term)
        query = query.filter(
            db.or_(
                Asset.name.ilike(f'%{safe_term}%'),
                Asset.asset_tag.ilike(f'%{safe_term}%'),
                Asset.serial_number.ilike(f'%{safe_term}%'),
                Asset.manufacturer.ilike(f'%{safe_term}%'),
            )
        )

    # Status filter
    status_filter = request.args.get('status', '')
    if status_filter and status_filter in Asset.STATUS_CHOICES:
        query = query.filter_by(status=status_filter)

    # Type filter
    type_filter = request.args.get('type', '')
    if type_filter and type_filter in Asset.TYPE_CHOICES:
        query = query.filter_by(asset_type=type_filter)

    # Pagination
    page = request.args.get('page', 1, type=int)
    assets = query.order_by(Asset.asset_tag).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('assets/list.html',
                           assets=assets,
                           search_form=search_form,
                           status_choices=Asset.STATUS_CHOICES,
                           type_choices=Asset.TYPE_CHOICES,
                           current_status=status_filter,
                           current_type=type_filter,
                           search_term=search_term)


# ======================================================================= #
#  View Asset                                                               #
# ======================================================================= #

@assets_bp.route('/<int:asset_id>')
@login_required
def view_asset(asset_id):
    """View a single asset's full details."""
    asset = Asset.query.get_or_404(asset_id)

    # Non-admins can only view their own assets
    if not current_user.is_admin and asset.assigned_to_id != current_user.id:
        log_event(
            event_type=AuditLog.EVENT_ACCESS_DENIED,
            description=f'User {current_user.username} attempted to view '
                        f'asset {asset.asset_tag} not assigned to them.',
            resource_type='Asset', resource_id=asset_id,
        )
        abort(403)

    return render_template('assets/view.html', asset=asset)


# ======================================================================= #
#  Create Asset                                                             #
# ======================================================================= #

@assets_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_asset():
    """Create a new IT asset (admin only)."""
    form = AssetForm()

    if form.validate_on_submit():
        # Check asset tag uniqueness
        if Asset.query.filter_by(asset_tag=form.asset_tag.data).first():
            flash('An asset with that tag already exists.', 'danger')
            return render_template('assets/form.html', form=form, title='Add Asset')

        # Check serial number uniqueness (if provided)
        if form.serial_number.data:
            if Asset.query.filter_by(serial_number=form.serial_number.data).first():
                flash('An asset with that serial number already exists.', 'danger')
                return render_template('assets/form.html', form=form, title='Add Asset')

        asset = Asset(
            name=sanitize_input(form.name.data),
            asset_tag=sanitize_input(form.asset_tag.data),
            asset_type=form.asset_type.data,
            manufacturer=sanitize_input(form.manufacturer.data),
            model=sanitize_input(form.model.data),
            serial_number=sanitize_input(form.serial_number.data),
            status=form.status.data,
            location=sanitize_input(form.location.data),
            purchase_date=form.purchase_date.data,
            purchase_cost=form.purchase_cost.data,
            warranty_expiry=form.warranty_expiry.data,
            assigned_to_id=form.assigned_to_id.data if form.assigned_to_id.data != 0 else None,
            notes=sanitize_input(form.notes.data),
        )

        db.session.add(asset)
        db.session.flush()  # Get asset.id before committing

        log_event_no_commit(
            event_type=AuditLog.EVENT_CREATE,
            description=f'Asset created: {asset.asset_tag} - {asset.name}',
            resource_type='Asset', resource_id=asset.id,
        )
        db.session.commit()

        flash(f'Asset "{asset.name}" created successfully.', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset.id))

    return render_template('assets/form.html', form=form, title='Add Asset')


# ======================================================================= #
#  Edit Asset                                                               #
# ======================================================================= #

@assets_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_asset(asset_id):
    """Edit an existing asset (admin only)."""
    asset = Asset.query.get_or_404(asset_id)
    form = AssetForm(obj=asset)

    if form.validate_on_submit():
        # Check asset tag uniqueness (excluding this record)
        existing = Asset.query.filter(
            Asset.asset_tag == form.asset_tag.data,
            Asset.id != asset_id
        ).first()
        if existing:
            flash('Another asset already uses that asset tag.', 'danger')
            return render_template('assets/form.html', form=form,
                                   title='Edit Asset', asset=asset)

        # Record what changed for audit log
        changes = []
        fields_to_check = ['name', 'status', 'assigned_to_id', 'location']
        for field in fields_to_check:
            old_val = getattr(asset, field)
            new_val = getattr(form, field).data
            if str(old_val) != str(new_val):
                changes.append(f'{field}: "{old_val}" → "{new_val}"')

        # Apply updates
        asset.name = sanitize_input(form.name.data)
        asset.asset_tag = sanitize_input(form.asset_tag.data)
        asset.asset_type = form.asset_type.data
        asset.manufacturer = sanitize_input(form.manufacturer.data)
        asset.model = sanitize_input(form.model.data)
        asset.serial_number = sanitize_input(form.serial_number.data)
        asset.status = form.status.data
        asset.location = sanitize_input(form.location.data)
        asset.purchase_date = form.purchase_date.data
        asset.purchase_cost = form.purchase_cost.data
        asset.warranty_expiry = form.warranty_expiry.data
        asset.assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else None
        asset.notes = sanitize_input(form.notes.data)

        log_event_no_commit(
            event_type=AuditLog.EVENT_UPDATE,
            description=f'Asset updated: {asset.asset_tag}. '
                        f'Changes: {"; ".join(changes) if changes else "minor update"}',
            resource_type='Asset', resource_id=asset.id,
        )
        db.session.commit()

        flash(f'Asset "{asset.name}" updated successfully.', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset.id))

    # Pre-populate assigned_to field
    if asset.assigned_to_id:
        form.assigned_to_id.data = asset.assigned_to_id

    return render_template('assets/form.html', form=form, title='Edit Asset', asset=asset)


# ======================================================================= #
#  Delete Asset                                                             #
# ======================================================================= #

@assets_bp.route('/<int:asset_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_asset(asset_id):
    """
    Delete an asset with confirmation step (admin only).

    A confirmation form is shown before deletion to prevent
    accidental or CSRF-triggered deletions.
    """
    asset = Asset.query.get_or_404(asset_id)
    form = ConfirmDeleteForm()

    if form.validate_on_submit():
        asset_tag = asset.asset_tag
        asset_name = asset.name

        log_event_no_commit(
            event_type=AuditLog.EVENT_DELETE,
            description=f'Asset deleted: {asset_tag} - {asset_name}',
            resource_type='Asset', resource_id=asset_id,
        )
        db.session.delete(asset)
        db.session.commit()

        flash(f'Asset "{asset_name}" has been deleted.', 'success')
        return redirect(url_for('assets.list_assets'))

    return render_template('assets/confirm_delete.html',
                           form=form, asset=asset)
