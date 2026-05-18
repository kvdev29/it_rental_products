"""
WTForms form definitions. All forms use FlaskForm so CSRF tokens
are included automatically.
"""

import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField,
    TextAreaField, DateField, DecimalField, HiddenField, SubmitField, IntegerField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional,
    ValidationError, NumberRange, Regexp
)
from app.models import User


# custom validators

def password_strength(form, field):
    """Require min 8 chars with upper, lower, digit and special char."""
    password = field.data
    errors = []
    if len(password) < 8:
        errors.append('at least 8 characters')
    if not re.search(r'[A-Z]', password):
        errors.append('an uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('a lowercase letter')
    if not re.search(r'\d', password):
        errors.append('a number')
    if not re.search(r'[^a-zA-Z0-9]', password):
        errors.append('a special character (!@#$%^&* etc.)')
    if errors:
        raise ValidationError('Password must contain ' + ', '.join(errors) + '.')


def no_html(form, field):
    """Reject any input that contains HTML tags."""
    if field.data and re.search(r'<[^>]+>', field.data):
        raise ValidationError('HTML tags are not permitted in this field.')


# auth forms

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
    ])
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Admin-only user creation form."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp(r'^[a-zA-Z0-9_.-]+$',
               message='Username may only contain letters, numbers, dots, hyphens and underscores.'),
    ])
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.'),
        Length(max=120),
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=120),
        no_html,
    ])
    department = StringField('Department', validators=[
        Optional(),
        Length(max=80),
        no_html,
    ])
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^[\d\s\+\-\(\)]*$', message='Phone number format is invalid.'),
    ])
    role = SelectField('Role', choices=[('user', 'Standard User'), ('admin', 'Administrator')])
    password = PasswordField('Password', validators=[
        DataRequired(),
        password_strength,
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.'),
    ])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        """Check username is not already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already registered.')

    def validate_email(self, email):
        """Check email is not already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email address is already registered.')


class PublicRegistrationForm(FlaskForm):
    """Self-service registration for guests and employees."""
    account_type = SelectField('Account Type', choices=[
        ('user', 'Employee'),
        ('guest', 'Guest'),
    ], default='user')
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp(r'^[a-zA-Z0-9_.-]+$',
               message='Username may only contain letters, numbers, dots, hyphens and underscores.'),
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(), Length(min=2, max=120), no_html,
    ])
    email = StringField('Email Address', validators=[
        DataRequired(), Email(message='Please enter a valid email address.'), Length(max=120),
    ])
    department = StringField('Department', validators=[Optional(), Length(max=80), no_html])
    password = PasswordField('Password', validators=[DataRequired(), password_strength])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.'),
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('That email address is already registered.')


class ChangePasswordForm(FlaskForm):
    """Allow a user to change their own password."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        password_strength,
    ])
    new_password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.'),
    ])
    submit = SubmitField('Change Password')


class EditProfileForm(FlaskForm):
    """User self-service profile edit (limited fields)."""
    full_name = StringField('Full Name', validators=[
        DataRequired(), Length(min=2, max=120), no_html,
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120),
    ])
    department = StringField('Department', validators=[Optional(), Length(max=80), no_html])
    phone = StringField('Phone', validators=[
        Optional(), Length(max=20),
        Regexp(r'^[\d\s\+\-\(\)]*$', message='Invalid phone format.'),
    ])
    submit = SubmitField('Save Changes')


# asset forms

class AssetForm(FlaskForm):
    name = StringField('Asset Name', validators=[
        DataRequired(), Length(min=2, max=120), no_html,
    ])
    asset_tag = StringField('Asset Tag', validators=[
        DataRequired(),
        Length(min=2, max=50),
        Regexp(r'^[a-zA-Z0-9\-_]+$',
               message='Asset tag may only contain letters, numbers, hyphens and underscores.'),
    ])
    asset_type = SelectField('Type', choices=[])
    manufacturer = StringField('Manufacturer', validators=[
        Optional(), Length(max=80), no_html,
    ])
    model = StringField('Model', validators=[Optional(), Length(max=80), no_html])
    serial_number = StringField('Serial Number', validators=[
        Optional(), Length(max=100), no_html,
    ])
    status = SelectField('Status', choices=[])
    location = StringField('Location', validators=[
        Optional(), Length(max=100), no_html,
    ])
    purchase_date = DateField('Purchase Date', validators=[Optional()])
    purchase_cost = DecimalField('Purchase Cost (£)', validators=[
        Optional(), NumberRange(min=0, max=9999999),
    ], places=2)
    warranty_expiry = DateField('Warranty Expiry', validators=[Optional()])
    assigned_to_id = SelectField('Assigned To', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000), no_html])
    submit = SubmitField('Save Asset')

    def __init__(self, *args, **kwargs):
        from app.models import Asset
        super().__init__(*args, **kwargs)
        self.asset_type.choices = [(t, t) for t in Asset.TYPE_CHOICES]
        self.status.choices = [(s, s) for s in Asset.STATUS_CHOICES]

        # Build user list for assignment dropdown
        users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        self.assigned_to_id.choices = [(0, '-- Unassigned --')] + \
                                       [(u.id, u.full_name) for u in users]


# ticket forms

class TicketForm(FlaskForm):
    """Raise a new helpdesk ticket."""
    title = StringField('Summary', validators=[
        DataRequired(), Length(min=5, max=200), no_html,
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(), Length(min=10, max=5000), no_html,
    ])
    priority = SelectField('Priority', choices=[])
    category = SelectField('Category', choices=[])
    related_asset_id = SelectField('Related Asset (optional)',
                                   coerce=int, validators=[Optional()])
    submit = SubmitField('Submit Ticket')

    def __init__(self, *args, **kwargs):
        from app.models import Ticket, Asset
        super().__init__(*args, **kwargs)
        self.priority.choices = [(p, p) for p in Ticket.PRIORITY_CHOICES]
        self.category.choices = [(c, c) for c in Ticket.CATEGORY_CHOICES]

        assets = Asset.query.order_by(Asset.name).all()
        self.related_asset_id.choices = [(0, '-- None --')] + \
                                         [(a.id, f'{a.asset_tag} - {a.name}') for a in assets]


class AdminTicketForm(TicketForm):
    """Extended ticket form for admins - adds assignment and status."""
    status = SelectField('Status', choices=[])
    assigned_to_id = SelectField('Assign To', coerce=int, validators=[Optional()])
    resolution_notes = TextAreaField('Resolution Notes',
                                     validators=[Optional(), Length(max=5000), no_html])

    def __init__(self, *args, **kwargs):
        from app.models import Ticket
        super().__init__(*args, **kwargs)
        self.status.choices = [(s, s) for s in Ticket.STATUS_CHOICES]
        users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
        self.assigned_to_id.choices = [(0, '-- Unassigned --')] + \
                                       [(u.id, u.full_name) for u in users]


class CommentForm(FlaskForm):
    """Add a comment or internal note to a ticket."""
    body = TextAreaField('Comment', validators=[
        DataRequired(), Length(min=1, max=2000), no_html,
    ])
    is_internal = BooleanField('Internal note (admin-only)')
    submit = SubmitField('Post Comment')


# admin forms

class AdminEditUserForm(FlaskForm):
    """Admin edit of any user account."""
    full_name = StringField('Full Name', validators=[
        DataRequired(), Length(min=2, max=120), no_html,
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120),
    ])
    department = StringField('Department', validators=[
        Optional(), Length(max=80), no_html,
    ])
    phone = StringField('Phone', validators=[
        Optional(), Length(max=20),
        Regexp(r'^[\d\s\+\-\(\)]*$', message='Invalid phone format.'),
    ])
    role = SelectField('Role', choices=[('user', 'Standard User'), ('admin', 'Administrator')])
    is_active = BooleanField('Account Active')
    submit = SubmitField('Save Changes')


class ConfirmDeleteForm(FlaskForm):
    """Simple confirmation form to prevent CSRF-free deletions."""
    confirm = HiddenField('confirm', default='yes')
    submit = SubmitField('Confirm Delete')


class SearchForm(FlaskForm):
    """Global search/filter form."""
    query = StringField('Search', validators=[Optional(), Length(max=100), no_html])
    submit = SubmitField('Search')


# rental forms

class RentalRequestForm(FlaskForm):
    """Request to rent a device for the day."""
    return_by = DateField('Return By', validators=[DataRequired()])
    notes = TextAreaField('Notes (optional)', validators=[Optional(), Length(max=500), no_html])
    submit = SubmitField('Confirm Rental')


class RentalItemForm(FlaskForm):
    """Admin form to add or edit a rental catalog item."""
    name = StringField('Item Name', validators=[DataRequired(), Length(min=2, max=120), no_html])
    category = SelectField('Category', choices=[])
    location = SelectField('Office Location', choices=[])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500), no_html])
    quantity_total = IntegerField('Total Quantity', validators=[
        DataRequired(), NumberRange(min=1, max=999, message='Quantity must be between 1 and 999.'),
    ])
    is_active = BooleanField('Available for Rental')
    submit = SubmitField('Save Item')

    def __init__(self, *args, **kwargs):
        from app.models import RentalItem
        super().__init__(*args, **kwargs)
        self.category.choices = [(c, c) for c in RentalItem.CATEGORY_CHOICES]
        self.location.choices = [(l, l) for l in RentalItem.LOCATION_CHOICES]
