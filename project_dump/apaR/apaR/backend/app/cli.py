"""Flask CLI commands for database management."""
from __future__ import annotations

import subprocess
import sys

import click


@click.command()
@click.option("--rev-id", default="head", help="Alembic revision ID (default: head)")
def migrate(rev_id: str) -> None:
    """Run database migrations using Alembic.
    
    Usage:
        flask --app app.main migrate          # Upgrade to latest
        flask --app app.main migrate --rev-id 20250125_000001  # Specific revision
    """
    cmd = ["alembic", "upgrade", rev_id]
    result = subprocess.run(cmd, cwd=".")  # noqa: S603, S607
    sys.exit(result.returncode)
