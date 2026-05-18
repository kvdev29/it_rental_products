# Database models for GearDesk
# SQLAlchemy ORM — all tables defined here

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# --- User ---

class User(UserMixin, db.Model):
    """App user. role is 'admin', 'user' or 'guest'."""
    __tablename__ = 'users'

    id                 = db.Column(db.Integer, primary_key=True)
    username           = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email              = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash      = db.Column(db.String(256), nullable=False)
    role               = db.Column(db.String(20), nullable=False, default='user')  # 'admin' | 'user'
    is_active          = db.Column(db.Boolean, default=True, nullable=False)
    full_name          = db.Column(db.String(120), nullable=False)
    department         = db.Column(db.String(80))
    phone              = db.Column(db.String(20))
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until       = db.Column(db.DateTime, nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow,
                                   onupdate=datetime.utcnow)
    last_login         = db.Column(db.DateTime, nullable=True)

    # Relationships
    raised_tickets   = db.relationship('Ticket', foreign_keys='Ticket.raised_by_id',
                                        backref='raised_by', lazy='dynamic')
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id',
                                        backref='assigned_to', lazy='dynamic')
    assigned_assets  = db.relationship('Asset', foreign_keys='Asset.assigned_to_id',
                                        backref='assigned_to', lazy='dynamic')
    comments         = db.relationship('Comment', backref='author', lazy='dynamic')
    audit_logs       = db.relationship('AuditLog', backref='user', lazy='dynamic')

    # ------------------------------------------------------------------ #
    # Password management                                                  #
    # ------------------------------------------------------------------ #

    def set_password(self, password):
        """Hash and store password using PBKDF2-SHA256."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------ #
    # Account lockout helpers (OWASP A07)                                  #
    # ------------------------------------------------------------------ #

    def is_locked(self):
        """Return True if the account is currently locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def increment_failed_login(self):
        """Increment failed login counter; lock after 5 failures."""
        from datetime import timedelta
        self.failed_login_count += 1
        if self.failed_login_count >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)

    def reset_failed_login(self):
        """Reset counter and lock on successful login."""
        self.failed_login_count = 0
        self.locked_until = None

    # ------------------------------------------------------------------ #
    # Helpers                                                               #
    # ------------------------------------------------------------------ #

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_guest(self):
        return self.role == 'guest'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


# --- Asset ---

class Asset(db.Model):
    """IT asset — laptop, licence, peripheral, etc."""
    __tablename__ = 'assets'

    # Status choices - validated at form level
    STATUS_CHOICES = ['Available', 'In Use', 'Under Repair', 'Decommissioned', 'Lost']

    # Type choices
    TYPE_CHOICES = ['Laptop', 'Desktop', 'Server', 'Monitor', 'Mobile',
                    'Printer', 'Switch', 'Software Licence', 'Peripheral', 'Other']

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(120), nullable=False)
    asset_tag        = db.Column(db.String(50), unique=True, nullable=False, index=True)
    asset_type       = db.Column(db.String(50), nullable=False)
    manufacturer     = db.Column(db.String(80))
    model            = db.Column(db.String(80))
    serial_number    = db.Column(db.String(100), unique=True)
    status           = db.Column(db.String(30), nullable=False, default='Available')
    purchase_date    = db.Column(db.Date)
    purchase_cost    = db.Column(db.Numeric(10, 2))
    warranty_expiry  = db.Column(db.Date)
    location         = db.Column(db.String(100))
    notes            = db.Column(db.Text)
    assigned_to_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                  onupdate=datetime.utcnow)

    # Relationships
    tickets = db.relationship('Ticket', backref='related_asset', lazy='dynamic')

    def __repr__(self):
        return f'<Asset {self.asset_tag}: {self.name}>'


# --- Ticket ---

class Ticket(db.Model):
    """Helpdesk support ticket. Open → In Progress → Resolved → Closed."""
    __tablename__ = 'tickets'

    STATUS_CHOICES   = ['Open', 'In Progress', 'Resolved', 'Closed', 'Cancelled']
    PRIORITY_CHOICES = ['Low', 'Medium', 'High', 'Critical']
    CATEGORY_CHOICES = ['Hardware', 'Software', 'Network', 'Account Access',
                        'Email', 'Printer', 'Security Incident', 'Other']

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    description      = db.Column(db.Text, nullable=False)
    status           = db.Column(db.String(30), nullable=False, default='Open')
    priority         = db.Column(db.String(20), nullable=False, default='Medium')
    category         = db.Column(db.String(50), nullable=False)
    raised_by_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    related_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    resolution_notes = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                  onupdate=datetime.utcnow)
    resolved_at      = db.Column(db.DateTime, nullable=True)

    # Relationships
    comments = db.relationship('Comment', backref='ticket',
                                lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Ticket #{self.id}: {self.title[:40]}>'


# --- Comment ---

class Comment(db.Model):
    """Comment on a ticket. is_internal=True means admin-only."""
    __tablename__ = 'comments'

    id         = db.Column(db.Integer, primary_key=True)
    ticket_id  = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    is_internal= db.Column(db.Boolean, default=False)  # Admin-only notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Comment by user {self.author_id} on ticket {self.ticket_id}>'


# --- AuditLog (insert-only, never updated or deleted) ---

class AuditLog(db.Model):
    """Audit trail. Records are insert-only — nothing is ever updated or deleted."""
    __tablename__ = 'audit_logs'

    # Event type constants for consistency
    EVENT_LOGIN_SUCCESS  = 'LOGIN_SUCCESS'
    EVENT_LOGIN_FAIL     = 'LOGIN_FAIL'
    EVENT_LOGOUT         = 'LOGOUT'
    EVENT_ACCOUNT_LOCKED = 'ACCOUNT_LOCKED'
    EVENT_ACCESS_DENIED  = 'ACCESS_DENIED'
    EVENT_CREATE         = 'CREATE'
    EVENT_UPDATE         = 'UPDATE'
    EVENT_DELETE         = 'DELETE'
    EVENT_PASSWORD_CHANGE= 'PASSWORD_CHANGE'
    EVENT_USER_ACTIVATED = 'USER_ACTIVATED'
    EVENT_USER_DEACTIVATED = 'USER_DEACTIVATED'

    id             = db.Column(db.Integer, primary_key=True)
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow,
                                nullable=False, index=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type     = db.Column(db.String(50), nullable=False, index=True)
    resource_type  = db.Column(db.String(50))      # e.g. 'Asset', 'Ticket', 'User'
    resource_id    = db.Column(db.Integer)          # PK of affected record
    description    = db.Column(db.Text, nullable=False)
    ip_address     = db.Column(db.String(45))       # IPv4 or IPv6
    user_agent     = db.Column(db.String(255))
    extra_data     = db.Column(db.Text)             # JSON string for additional context

    def __repr__(self):
        return f'<AuditLog {self.event_type} by user {self.user_id} at {self.timestamp}>'


# --- RentalItem / Rental ---

class RentalItem(db.Model):
    """A device available for short-term rental within the office."""
    __tablename__ = 'rental_items'

    CATEGORY_CHOICES = ['Headset', 'Keyboard', 'Mouse', 'Webcam',
                        'Laptop', 'Tablet', 'Phone', 'Cable / Adapter', 'Other']
    LOCATION_CHOICES = ['London', 'Hove', 'Cardiff']

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(120), nullable=False)
    category       = db.Column(db.String(50), nullable=False)
    location       = db.Column(db.String(50), nullable=False, default='London')
    description    = db.Column(db.Text)
    quantity_total = db.Column(db.Integer, nullable=False, default=1)
    is_active      = db.Column(db.Boolean, default=True, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    rentals = db.relationship('Rental', backref='item', lazy='dynamic')

    @property
    def quantity_available(self):
        active = self.rentals.filter(Rental.status.in_(['Active', 'Overdue'])).count()
        return max(0, self.quantity_total - active)

    @property
    def is_available(self):
        return self.is_active and self.quantity_available > 0

    def __repr__(self):
        return f'<RentalItem {self.name}>'


# ======================================================================= #
#  Rental Model                                                             #
# ======================================================================= #

class Rental(db.Model):
    """A single rental transaction — one item borrowed by one user."""
    __tablename__ = 'rentals'

    STATUS_ACTIVE   = 'Active'
    STATUS_RETURNED = 'Returned'
    STATUS_OVERDUE  = 'Overdue'

    id          = db.Column(db.Integer, primary_key=True)
    item_id     = db.Column(db.Integer, db.ForeignKey('rental_items.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rented_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    return_by   = db.Column(db.Date, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    status      = db.Column(db.String(20), nullable=False, default='Active')
    notes       = db.Column(db.Text)

    borrower = db.relationship('User', backref=db.backref('rentals', lazy='dynamic'))

    def __repr__(self):
        return f'<Rental #{self.id} status={self.status}>'
