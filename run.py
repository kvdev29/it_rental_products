"""
run.py - Application Entry Point
----------------------------------
Starts the Flask development server and registers CLI commands.

Usage:
    python run.py                    # Start development server
    flask seed-db                    # Seed the database
    flask shell                      # Flask interactive shell
"""

import click
from app import create_app
from app.models import db

app = create_app()


@app.cli.command('seed-db')
def seed_db_command():
    """Seed the database with sample data."""
    from seed import seed_database
    seed_database()


@app.shell_context_processor
def make_shell_context():
    """Make db and models available in flask shell."""
    from app.models import User, Asset, Ticket, Comment, AuditLog
    return dict(db=db, User=User, Asset=Asset, Ticket=Ticket,
                Comment=Comment, AuditLog=AuditLog)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
