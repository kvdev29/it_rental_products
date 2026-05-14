"""
app/__init__.py - Application Factory
---------------------------------------
Creates and configures the Flask application using the factory pattern.

The factory pattern allows:
  - Multiple app instances (useful for testing with different configs)
  - Clean extension initialisation
  - Blueprint registration

Extensions initialised:
  - SQLAlchemy  : ORM / database
  - Flask-Login : Authentication session management
  - Flask-WTF   : CSRF protection on all forms
  - Flask-Limiter: Rate limiting (OWASP A07)
  - Flask-Migrate: Database migrations

Reference: Flask Application Factories
https://flask.palletsprojects.com/en/3.0.x/patterns/appfactories/
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from app.models import db, User
from config import config


# ------------------------------------------------------------------ #
# Extension instances (not yet bound to any app)                      #
# ------------------------------------------------------------------ #
login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Application factory function.

    Args:
        config_name (str): Key from config dict in config.py.
                           Defaults to FLASK_ENV env var or 'development'.

    Returns:
        Flask: Configured application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ---------------------------------------------------------------- #
    # Initialise extensions                                              #
    # ---------------------------------------------------------------- #
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)

    # ---------------------------------------------------------------- #
    # Flask-Login configuration                                          #
    # ---------------------------------------------------------------- #
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'  # Regenerate session on IP change

    @login_manager.user_loader
    def load_user(user_id):
        """Load user from DB by session-stored ID."""
        return User.query.get(int(user_id))

    # ---------------------------------------------------------------- #
    # Register Blueprints                                                #
    # ---------------------------------------------------------------- #
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.assets import assets_bp
    from app.routes.tickets import tickets_bp
    from app.routes.admin import admin_bp
    from app.routes.rentals import rentals_bp

    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(main_bp,    url_prefix='/')
    app.register_blueprint(assets_bp,  url_prefix='/assets')
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(admin_bp,   url_prefix='/admin')
    app.register_blueprint(rentals_bp, url_prefix='/rentals')

    # ---------------------------------------------------------------- #
    # Security Headers (applied to every response)                       #
    # ---------------------------------------------------------------- #
    from app.utils.security import apply_security_headers

    @app.after_request
    def set_security_headers(response):
        return apply_security_headers(response)

    # ---------------------------------------------------------------- #
    # Custom error handlers                                              #
    # ---------------------------------------------------------------- #
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # ---------------------------------------------------------------- #
    # Logging configuration                                              #
    # ---------------------------------------------------------------- #
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/itsm.log', maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ITSM application startup')

    return app
