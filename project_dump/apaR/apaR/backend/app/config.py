from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    environment: str
    secret_key: str
    database_url: str
    api_host: str
    api_port: int
    data_dir: str
    cors_allow_origin: str | None


def get_settings() -> Settings:
    """Load settings from environment with sensible defaults."""
    project_root = Path(__file__).resolve().parents[2]
    environment = os.getenv("FLASK_ENV", "development")
    
    # In development, default CORS_ALLOW_ORIGIN to localhost Vite dev server
    cors_origin = os.getenv("CORS_ALLOW_ORIGIN")
    if not cors_origin and environment.lower() == "development":
        cors_origin = "http://localhost:5173"
    
    # Database URL: env-based selection with SQLite default for dev
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        if environment.lower() == "development":
            # Use SQLite for local development
            database_url = f"sqlite:///{project_root / 'backend' / 'app.db'}"
        else:
            # Postgres for production
            database_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/app_db"
    
    return Settings(
        environment=environment,
        secret_key=os.getenv("SECRET_KEY", "dev-secret-key"),
        database_url=database_url,
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "5000")),
        data_dir=os.getenv("DATA_DIR", str(project_root / "data")),
        cors_allow_origin=cors_origin,
    )
