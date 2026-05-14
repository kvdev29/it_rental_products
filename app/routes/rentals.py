"""
app/routes/rentals.py - Device Rental Routes
---------------------------------------------
Allows users to browse the rental catalog and borrow office devices
(headsets, keyboards, etc.) for the day. Rentals are auto-approved
when stock is available.
"""

from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db, RentalItem, Rental, AuditLog
from app.utils.forms import RentalRequestForm, RentalItemForm
from app.utils.security import log_event, admin_required

rentals_bp = Blueprint('rentals', __name__)


def _sync_overdue():
    """Mark any Active rentals past their return date as Overdue."""
    today = date.today()
    overdue = Rental.query.filter(
        Rental.status == Rental.STATUS_ACTIVE,
        Rental.return_by < today,
    ).all()
    for r in overdue:
        r.status = Rental.STATUS_OVERDUE
    if overdue:
        db.session.commit()


# ======================================================================= #
#  User-facing routes                                                       #
# ======================================================================= #

@rentals_bp.route('/')
@login_required
def catalog():
    """Browse devices available for rental."""
    _sync_overdue()
    items = (RentalItem.query
             .filter_by(is_active=True)
             .order_by(RentalItem.category, RentalItem.name)
             .all())
    return render_template('rentals/catalog.html', items=items)


@rentals_bp.route('/request/<int:item_id>', methods=['GET', 'POST'])
@login_required
def request_rental(item_id):
    """Request to rent a specific item."""
    item = RentalItem.query.get_or_404(item_id)

    if not item.is_available:
        flash(f'Sorry, {item.name} is not available right now.', 'warning')
        return redirect(url_for('rentals.catalog'))

    form = RentalRequestForm()
    if form.validate_on_submit():
        if form.return_by.data < date.today():
            flash('Return date cannot be in the past.', 'danger')
            return render_template('rentals/request.html', form=form, item=item)

        rental = Rental(
            item_id=item.id,
            user_id=current_user.id,
            return_by=form.return_by.data,
            notes=form.notes.data or '',
            status=Rental.STATUS_ACTIVE,
        )
        db.session.add(rental)
        db.session.commit()

        log_event(
            event_type=AuditLog.EVENT_CREATE,
            description=(f'{current_user.username} rented "{item.name}" '
                         f'(return by {form.return_by.data.strftime("%d %b %Y")})'),
            resource_type='Rental',
            resource_id=rental.id,
        )

        flash(
            f'{item.name} is yours! Please return it by '
            f'{form.return_by.data.strftime("%d %b %Y")}.',
            'success',
        )
        return redirect(url_for('rentals.my_rentals'))

    return render_template('rentals/request.html', form=form, item=item)


@rentals_bp.route('/my')
@login_required
def my_rentals():
    """View current user's active and past rentals."""
    _sync_overdue()
    active = (Rental.query
              .filter(Rental.user_id == current_user.id,
                      Rental.status.in_([Rental.STATUS_ACTIVE, Rental.STATUS_OVERDUE]))
              .order_by(Rental.return_by)
              .all())
    history = (Rental.query
               .filter_by(user_id=current_user.id, status=Rental.STATUS_RETURNED)
               .order_by(Rental.returned_at.desc())
               .limit(15)
               .all())
    return render_template('rentals/my_rentals.html', active=active, history=history)


@rentals_bp.route('/return/<int:rental_id>', methods=['POST'])
@login_required
def return_rental(rental_id):
    """Mark a rental as returned."""
    rental = Rental.query.get_or_404(rental_id)

    if rental.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('rentals.my_rentals'))

    if rental.status == Rental.STATUS_RETURNED:
        flash('This rental has already been returned.', 'info')
    else:
        rental.status = Rental.STATUS_RETURNED
        rental.returned_at = datetime.utcnow()
        db.session.commit()

        log_event(
            event_type=AuditLog.EVENT_UPDATE,
            description=(f'{current_user.username} returned '
                         f'"{rental.item.name}" (rental #{rental.id})'),
            resource_type='Rental',
            resource_id=rental.id,
        )
        flash(f'{rental.item.name} marked as returned. Thanks!', 'success')

    if current_user.is_admin:
        return redirect(url_for('rentals.admin_rentals'))
    return redirect(url_for('rentals.my_rentals'))


# ======================================================================= #
#  Admin routes                                                             #
# ======================================================================= #

@rentals_bp.route('/admin')
@login_required
@admin_required
def admin_rentals():
    """Admin view of all active and recent rentals."""
    _sync_overdue()
    active = (Rental.query
              .filter(Rental.status.in_([Rental.STATUS_ACTIVE, Rental.STATUS_OVERDUE]))
              .order_by(Rental.return_by)
              .all())
    recent_returned = (Rental.query
                       .filter_by(status=Rental.STATUS_RETURNED)
                       .order_by(Rental.returned_at.desc())
                       .limit(20)
                       .all())
    return render_template('rentals/admin_rentals.html',
                           active=active,
                           recent_returned=recent_returned)


@rentals_bp.route('/admin/items')
@login_required
@admin_required
def admin_items():
    """Manage the rental catalog."""
    items = (RentalItem.query
             .order_by(RentalItem.category, RentalItem.name)
             .all())
    return render_template('rentals/admin_items.html', items=items)


@rentals_bp.route('/admin/items/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_item():
    """Add a new item to the rental catalog."""
    form = RentalItemForm()
    form.is_active.data = True
    if form.validate_on_submit():
        item = RentalItem(
            name=form.name.data,
            category=form.category.data,
            description=form.description.data or '',
            quantity_total=form.quantity_total.data,
            is_active=form.is_active.data,
        )
        db.session.add(item)
        db.session.commit()
        log_event(
            event_type=AuditLog.EVENT_CREATE,
            description=f'Rental item added: {item.name} (qty: {item.quantity_total})',
            resource_type='RentalItem',
            resource_id=item.id,
        )
        flash(f'"{item.name}" added to the rental catalog.', 'success')
        return redirect(url_for('rentals.admin_items'))
    return render_template('rentals/item_form.html', form=form, title='Add Rental Item', item=None)


@rentals_bp.route('/admin/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_item(item_id):
    """Edit an existing rental catalog item."""
    item = RentalItem.query.get_or_404(item_id)
    form = RentalItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.category = form.category.data
        item.description = form.description.data or ''
        item.quantity_total = form.quantity_total.data
        item.is_active = form.is_active.data
        db.session.commit()
        log_event(
            event_type=AuditLog.EVENT_UPDATE,
            description=f'Rental item updated: {item.name}',
            resource_type='RentalItem',
            resource_id=item.id,
        )
        flash(f'"{item.name}" updated.', 'success')
        return redirect(url_for('rentals.admin_items'))
    return render_template('rentals/item_form.html', form=form, title='Edit Rental Item', item=item)
