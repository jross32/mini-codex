from flask import Flask, jsonify, request, session
from sqlalchemy import inspect

from .config import Settings, get_settings
from .db import build_engine, make_scoped_session
from .data_store import DataStore
from .admin import admin_bp
from .auth import auth_bp, get_or_set_csrf_token
from .models import Base
from .user_context_routes import user_ctx_bp
from .routes import api_bp
from .cli import migrate


def create_app(settings: Settings | None = None) -> Flask:
    """Application factory so tests and CLI use the same entrypoint."""
    app = Flask(__name__)
    app_settings = settings or get_settings()

    engine = build_engine(app_settings.database_url)
    db_session = make_scoped_session(engine)
    data_store = DataStore(app_settings.data_dir)
    
    # Log database being used (safe, no passwords)
    db_type = "SQLite" if "sqlite" in app_settings.database_url.lower() else "PostgreSQL"
    app.logger.info(f"Using {db_type} database")

    # Preload dataset so the API can serve meta/health immediately.
    try:  # pragma: no cover - defensive log path
        data_store.load()
    except Exception as exc:  # noqa: BLE001
        app.logger.warning("Continuing without preloaded dataset: %s", exc)

    # Store settings and engine on the app for easy access in blueprints/commands.
    app.secret_key = app_settings.secret_key
    app.config["ENV"] = app_settings.environment.lower()
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = app_settings.environment.lower() == "production"
    app.config["SESSION_COOKIE_NAME"] = "apar_session"
    app.config["JSON_SORT_KEYS"] = False
    app.config["CORS_ALLOW_ORIGIN"] = app_settings.cors_allow_origin
    app.config["SETTINGS"] = app_settings
    app.config["DB_ENGINE"] = engine
    app.config["DB_SESSION"] = db_session
    app.config["DATA_STORE"] = data_store
    
    # Create tables if they don't exist (safe for SQLite/dev, Alembic for Postgres/prod)
    Base.metadata.create_all(engine)
    
    # Check if required tables exist and warn if missing
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {"users", "user_contexts"}
    missing_tables = required_tables - existing_tables
    
    if missing_tables:
        app.logger.warning(
            f"Missing database tables: {missing_tables}. "
            f"Run migrations with: cd backend && alembic upgrade head"
        )

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_ctx_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    
    # Register CLI commands
    app.cli.add_command(migrate)

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:  # pragma: no cover
        db_session.remove()

    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests."""
        if request.method == "OPTIONS":
            allowed = app.config.get("CORS_ALLOW_ORIGIN")
            origin = request.headers.get("Origin")
            if allowed and origin and origin == allowed:
                return "", 204, {
                    "Access-Control-Allow-Origin": allowed,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Headers": "Content-Type, X-CSRF-Token",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                    "Access-Control-Max-Age": "3600",
                }
            return "", 204

    @app.before_request
    def enforce_csrf() -> tuple[object, int] | None:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return None
        if not request.path.startswith("/api/"):
            return None
        if request.path.startswith("/api/auth/csrf"):
            return None
        session_token = session.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")
        if not session_token or not header_token or session_token != header_token:
            return jsonify({"ok": False, "error": {"code": "csrf_failed", "message": "Invalid or missing CSRF token"}}), 403
        return None

    @app.after_request
    def add_cors_headers(response):
        allowed = app.config.get("CORS_ALLOW_ORIGIN")
        origin = request.headers.get("Origin")
        
        # Always add CORS headers if origin matches allowed origin
        if allowed and origin and origin == allowed:
            response.headers["Access-Control-Allow-Origin"] = allowed
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-CSRF-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "3600"
        
        return response

    return app
