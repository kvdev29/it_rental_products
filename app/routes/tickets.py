"""
app/routes/tickets.py - Helpdesk Ticket Routes
------------------------------------------------
Ticket creation, viewing, updating and commenting.

Access control:
    - Any authenticated user can raise a ticket
    - Users can only view/edit their own tickets
    - Admins can view, edit, assign and close all tickets
    - Internal comments are only visible to admins
"""

from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort)
from flask_login import login_required, current_user

from app.models import db, Ticket, Comment, AuditLog
from app.utils.forms import TicketForm, AdminTicketForm, CommentForm, ConfirmDeleteForm, SearchForm
from app.utils.security import admin_required, log_event, log_event_no_commit, sanitize_input

tickets_bp = Blueprint('tickets', __name__)


# ======================================================================= #
#  List Tickets                                                             #
# ======================================================================= #

@tickets_bp.route('/')
@login_required
def list_tickets():
    """
    List tickets.
    - Admins: all tickets with full filter options.
    - Users: only their own tickets.
    """
    search_form = SearchForm(request.args, meta={'csrf': False})
    query = Ticket.query

    if not current_user.is_admin:
        query = query.filter_by(raised_by_id=current_user.id)

    # Filters
    status_filter = request.args.get('status', '')
    if status_filter and status_filter in Ticket.STATUS_CHOICES:
        query = query.filter_by(status=status_filter)

    priority_filter = request.args.get('priority', '')
    if priority_filter and priority_filter in Ticket.PRIORITY_CHOICES:
        query = query.filter_by(priority=priority_filter)

    search_term = request.args.get('query', '').strip()
    if search_term:
        safe = sanitize_input(search_term)
        query = query.filter(
            db.or_(
                Ticket.title.ilike(f'%{safe}%'),
                Ticket.description.ilike(f'%{safe}%'),
            )
        )

    page = request.args.get('page', 1, type=int)
    tickets = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('tickets/list.html',
                           tickets=tickets,
                           search_form=search_form,
                           status_choices=Ticket.STATUS_CHOICES,
                           priority_choices=Ticket.PRIORITY_CHOICES,
                           current_status=status_filter,
                           current_priority=priority_filter,
                           search_term=search_term)


# ======================================================================= #
#  View Ticket                                                              #
# ======================================================================= #

@tickets_bp.route('/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    """View a single ticket and its comments."""
    ticket = Ticket.query.get_or_404(ticket_id)

    # Access control: users can only view their own tickets
    if not current_user.is_admin and ticket.raised_by_id != current_user.id:
        log_event(
            event_type=AuditLog.EVENT_ACCESS_DENIED,
            description=f'User {current_user.username} attempted to view '
                        f'ticket #{ticket_id} (not owner).',
            resource_type='Ticket', resource_id=ticket_id,
        )
        abort(403)

    comment_form = CommentForm()

    # Filter internal comments for non-admins
    comments_query = ticket.comments.order_by(Comment.created_at.asc())
    if not current_user.is_admin:
        comments_query = comments_query.filter_by(is_internal=False)
    comments = comments_query.all()

    return render_template('tickets/view.html',
                           ticket=ticket,
                           comments=comments,
                           comment_form=comment_form)


# ======================================================================= #
#  Create Ticket                                                            #
# ======================================================================= #

@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    """Raise a new helpdesk ticket (any authenticated user)."""
    form = TicketForm()

    if form.validate_on_submit():
        ticket = Ticket(
            title=sanitize_input(form.title.data),
            description=sanitize_input(form.description.data),
            priority=form.priority.data,
            category=form.category.data,
            raised_by_id=current_user.id,
            related_asset_id=form.related_asset_id.data if form.related_asset_id.data != 0 else None,
        )
        db.session.add(ticket)
        db.session.flush()

        log_event_no_commit(
            event_type=AuditLog.EVENT_CREATE,
            description=f'Ticket raised by {current_user.username}: "{ticket.title}"',
            resource_type='Ticket', resource_id=ticket.id,
        )
        db.session.commit()

        flash(f'Ticket #{ticket.id} submitted successfully.', 'success')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket.id))

    return render_template('tickets/form.html', form=form, title='Raise Ticket')


# ======================================================================= #
#  Edit Ticket                                                              #
# ======================================================================= #

@tickets_bp.route('/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    """
    Edit a ticket.
    - Users can edit only their own Open tickets (title/description/priority).
    - Admins can edit any ticket including status, assignment, and resolution.
    """
    ticket = Ticket.query.get_or_404(ticket_id)

    # Access control
    if not current_user.is_admin:
        if ticket.raised_by_id != current_user.id:
            abort(403)
        if ticket.status not in ['Open']:
            flash('You can only edit open tickets.', 'warning')
            return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))

    # Admins get extended form with status/assignment fields
    FormClass = AdminTicketForm if current_user.is_admin else TicketForm
    form = FormClass(obj=ticket)

    if form.validate_on_submit():
        old_status = ticket.status

        ticket.title = sanitize_input(form.title.data)
        ticket.description = sanitize_input(form.description.data)
        ticket.priority = form.priority.data
        ticket.category = form.category.data
        ticket.related_asset_id = form.related_asset_id.data if form.related_asset_id.data != 0 else None

        if current_user.is_admin:
            ticket.status = form.status.data
            ticket.assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else None
            ticket.resolution_notes = sanitize_input(form.resolution_notes.data)

            # Set resolved_at when status changes to Resolved
            if form.status.data == 'Resolved' and old_status != 'Resolved':
                ticket.resolved_at = datetime.utcnow()

        log_event_no_commit(
            event_type=AuditLog.EVENT_UPDATE,
            description=f'Ticket #{ticket_id} updated by {current_user.username}. '
                        f'Status: {old_status} → {ticket.status}',
            resource_type='Ticket', resource_id=ticket_id,
        )
        db.session.commit()

        flash(f'Ticket #{ticket_id} updated.', 'success')
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))

    # Pre-populate admin select fields
    if current_user.is_admin and ticket.assigned_to_id:
        form.assigned_to_id.data = ticket.assigned_to_id

    return render_template('tickets/form.html', form=form,
                           title=f'Edit Ticket #{ticket_id}', ticket=ticket)


# ======================================================================= #
#  Add Comment                                                              #
# ======================================================================= #

@tickets_bp.route('/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    """Post a comment on a ticket."""
    ticket = Ticket.query.get_or_404(ticket_id)

    # Access control: users can only comment on their own tickets
    if not current_user.is_admin and ticket.raised_by_id != current_user.id:
        abort(403)

    form = CommentForm()
    if form.validate_on_submit():
        # Only admins can post internal notes
        is_internal = form.is_internal.data and current_user.is_admin

        comment = Comment(
            ticket_id=ticket_id,
            author_id=current_user.id,
            body=sanitize_input(form.body.data),
            is_internal=is_internal,
        )
        db.session.add(comment)

        log_event_no_commit(
            event_type=AuditLog.EVENT_CREATE,
            description=f'Comment added to ticket #{ticket_id} by {current_user.username}',
            resource_type='Comment', resource_id=ticket_id,
        )
        db.session.commit()

        flash('Comment posted.', 'success')
    else:
        flash('Comment could not be posted. Please check your input.', 'danger')

    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))


# ======================================================================= #
#  Delete Ticket (Admin only)                                               #
# ======================================================================= #

@tickets_bp.route('/<int:ticket_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_ticket(ticket_id):
    """Delete a ticket (admin only) with confirmation step."""
    ticket = Ticket.query.get_or_404(ticket_id)
    form = ConfirmDeleteForm()

    if form.validate_on_submit():
        title = ticket.title
        log_event_no_commit(
            event_type=AuditLog.EVENT_DELETE,
            description=f'Ticket #{ticket_id} deleted by admin {current_user.username}: "{title}"',
            resource_type='Ticket', resource_id=ticket_id,
        )
        db.session.delete(ticket)
        db.session.commit()

        flash(f'Ticket #{ticket_id} has been deleted.', 'success')
        return redirect(url_for('tickets.list_tickets'))

    return render_template('tickets/confirm_delete.html', form=form, ticket=ticket)
