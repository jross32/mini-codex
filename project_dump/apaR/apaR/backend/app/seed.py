from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from . import create_app
from .models import Base, User


def seed_users() -> None:
    """Create a default admin and normal user for local/dev testing."""
    app = create_app()
    with app.app_context():
        engine = app.config["DB_ENGINE"]
        session = app.config["DB_SESSION"]

        Base.metadata.create_all(engine)

        defaults = [
            {"email": "admin@example.com", "password": "password123", "is_admin": True, "username": "admin"},
            {"email": "user@example.com", "password": "password123", "is_admin": False, "username": "user"},
        ]

        created = []
        for data in defaults:
            existing = session.query(User).filter(User.email == data["email"]).first()
            if existing:
                continue
            user = User(
                email=data["email"],
                username=data["username"],
                password_hash=generate_password_hash(data["password"]),
                is_admin=data["is_admin"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            created.append(user.email)

        session.commit()
        if created:
            app.logger.info("Seeded users: %s", ", ".join(created))
        else:
            app.logger.info("Seed users already exist; nothing to create.")


if __name__ == "__main__":  # pragma: no cover - manual entrypoint
    seed_users()
