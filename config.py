"""
config.py - Application Configuration
--------------------------------------
Loads environment variables and defines configuration classes
for different deployment environments (development, testing, production).

Reference: Flask documentation - Configuration Handling
https://flask.palletsprojects.com/en/3.0.x/config/
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    # ------------------------------------------------------------------ #
    # Core Flask settings                                                  #
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-CHANGE-ME'
    DEBUG = False
    TESTING = False

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///itsm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------ #
    # Session & Cookie Security (OWASP A02 - Cryptographic Failures)      #
    # ------------------------------------------------------------------ #
    SESSION_COOKIE_HTTPONLY = True       # Prevent JS access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF mitigation
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 1800))
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=1)

    # ------------------------------------------------------------------ #
    # CSRF Protection (OWASP A01 - Broken Access Control)                 #
    # ------------------------------------------------------------------ #
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600          # Token expires after 1 hour

    # ------------------------------------------------------------------ #
    # Rate Limiting (OWASP A07 - Identification & Auth Failures)          #
    # ------------------------------------------------------------------ #
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True

    # ------------------------------------------------------------------ #
    # Content Security Policy (OWASP A03 - Injection / XSS)              #
    # ------------------------------------------------------------------ #
    CSP_DIRECTIVES = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
        "img-src": "'self' data:",
        "font-src": "'self' https://fonts.gstatic.com",
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
    }


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False             # Set True to log all SQL queries


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False            # Disable CSRF in tests for simplicity
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration - stricter security settings."""
    SESSION_COOKIE_SECURE = True        # HTTPS only
    REMEMBER_COOKIE_SECURE = True


# Configuration registry
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
