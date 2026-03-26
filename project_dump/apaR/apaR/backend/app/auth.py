from __future__ import annotations

import re
import time
from collections import defaultdict
from datetime import datetime, timezone
import secrets
from functools import wraps
from typing import DefaultDict

from flask import Blueprint, current_app, jsonify, request, session, g
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .models import User

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LEN = 8


class SimpleRateLimiter:
    """In-memory sliding-window limiter for development environments."""

    def __init__(self, window_seconds: int, max_attempts: int) -> None:
        self.window = window_seconds
        self.max_attempts = max_attempts
        self.hits: DefaultDict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window
        entries = [ts for ts in self.hits.get(key, []) if ts >= window_start]
        if len(entries) >= self.max_attempts:
            self.hits[key] = entries
            return False
        entries.append(now)
        self.hits[key] = entries
        return True


login_ip_limiter = SimpleRateLimiter(window_seconds=60, max_attempts=12)
login_email_limiter = SimpleRateLimiter(window_seconds=60, max_attempts=8)
signup_ip_limiter = SimpleRateLimiter(window_seconds=60, max_attempts=6)
signup_email_limiter = SimpleRateLimiter(window_seconds=60, max_attempts=4)


def _db():
    return current_app.config["DB_SESSION"]


def _normalize_email(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    normalized = raw.strip().lower()
    return normalized or None


def _user_payload(user: User) -> dict[str, object]:
    return user.to_dict()


def get_current_user() -> User | None:
    if hasattr(g, "current_user"):
        return getattr(g, "current_user")
    user_id_raw = session.get("user_id")
    if not user_id_raw:
        g.current_user = None
        return None
    db_session = _db()
    try:
        user: User | None = db_session.query(User).filter(User.id == str(user_id_raw)).first()
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.warning("get_current_user failed: %s", exc)
        user = None
    g.current_user = user
    return user


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _error(code: str, message: str, status: int = 400, field: str | None = None, debug: dict[str, object] | None = None):
    payload: dict[str, object] = {"ok": False, "error": {"code": code, "message": message}}
    if field:
        payload["error"]["field"] = field
    if debug:
        payload["error"]["debug"] = debug
    return jsonify(payload), status


def _success(payload: dict[str, object], status: int = 200):
    data = {"ok": True}
    data.update(payload)
    return jsonify(data), status


def _validate_email(email: str | None) -> bool:
    return bool(email and EMAIL_REGEX.match(email))


def _rate_limit(kind: str, ip_key: str, user_key: str | None) -> tuple[bool, tuple[dict[str, object], int] | None]:
    limiter_ip = signup_ip_limiter if kind == "signup" else login_ip_limiter
    limiter_user = signup_email_limiter if kind == "signup" else login_email_limiter

    if not limiter_ip.allow(ip_key):
        return False, _error("rate_limited", "Too many attempts. Try again shortly.", 429)
    if user_key and not limiter_user.allow(user_key):
        return False, _error("rate_limited", "Too many attempts. Try again shortly.", 429, field="email")
    return True, None


@auth_bp.post("/signup")
def signup() -> tuple[dict[str, object], int]:
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""
    username = (data.get("username") or "").strip() or None

    ip_key = _client_ip()
    allowed, response = _rate_limit("signup", ip_key, email)
    if not allowed:
        return response  # type: ignore[return-value]

    if not _validate_email(email):
        return _error("invalid_email", "Provide a valid email address.", field="email")
    if len(password) < PASSWORD_MIN_LEN:
        return _error("weak_password", f"Password must be at least {PASSWORD_MIN_LEN} characters.", field="password")

    db_session = _db()
    try:
        existing = db_session.query(User).filter(User.email == email).first()
        if existing:
            return _error("email_in_use", "Email is already registered.", 409, field="email")

        if username:
            conflict = db_session.query(User).filter(User.username == username).first()
            if conflict:
                return _error("username_in_use", "Username is already taken.", 409, field="username")

        user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        return _error("email_in_use", "Email is already registered.", 409, field="email")
    except Exception as exc:  # noqa: BLE001
        db_session.rollback()
        current_app.logger.exception("Signup failed")
        
        # In development, include exception details for debugging
        message = "Unable to create account right now."
        debug_info = None
        if current_app.config.get("ENV") == "development":
            debug_info = {"exception_type": type(exc).__name__, "exception_message": str(exc)}
        
        return _error("signup_failed", message, 500, debug=debug_info)

    session["user_id"] = str(user.id)
    session.permanent = False
    return _success({"user": _user_payload(user)}, status=201)


@auth_bp.post("/login")
def login() -> tuple[dict[str, object], int]:
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    ip_key = _client_ip()
    allowed, response = _rate_limit("login", ip_key, email)
    if not allowed:
        return response  # type: ignore[return-value]

    if not _validate_email(email):
        return _error("invalid_credentials", "Invalid credentials.", 401)
    if len(password) < 1:
        return _error("invalid_credentials", "Invalid credentials.", 401)

    db_session = _db()
    try:
        user: User | None = db_session.query(User).filter(User.email == email).first()
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("Login lookup failed: %s", exc, exc_info=True)
        return _error("login_failed", "Unable to login right now.", 500)

    if not user or not check_password_hash(user.password_hash, password):
        return _error("invalid_credentials", "Invalid credentials.", 401)

    session["user_id"] = str(user.id)
    session.permanent = False
    return _success({"user": _user_payload(user)}, status=200)


@auth_bp.post("/logout")
def logout() -> tuple[dict[str, object], int]:
    session.pop("user_id", None)
    return _success({"status": "logged_out"})


@auth_bp.post("/complete-onboarding")
def complete_onboarding() -> tuple[dict[str, object], int]:
    user_id_raw = session.get("user_id")
    if not user_id_raw:
        return _error("unauthorized", "Login required.", 401)

    db_session = _db()
    try:
        user: User | None = db_session.query(User).filter(User.id == str(user_id_raw)).first()
        if not user:
            session.pop("user_id", None)
            return _error("unauthorized", "Login required.", 401)
        if not user.onboarding_completed:
            user.onboarding_completed = True
            user.updated_at = datetime.now(timezone.utc)
            db_session.add(user)
            db_session.commit()
        return _success({"user": _user_payload(user)}, 200)
    except Exception as exc:  # noqa: BLE001
        db_session.rollback()
        current_app.logger.error("Complete onboarding failed: %s", exc, exc_info=True)
        return _error("onboarding_failed", "Unable to finish onboarding right now.", 500)


@auth_bp.get("/me")
def me() -> tuple[dict[str, object], int]:
    user = get_current_user()
    if not user:
        return _success({"user": None, "context": None})
    context = user.context.to_dict() if getattr(user, "context", None) else None
    return _success({"user": _user_payload(user), "context": context})


def get_or_set_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@auth_bp.get("/csrf")
def csrf() -> tuple[dict[str, object], int]:
    token = get_or_set_csrf_token()
    return jsonify({"ok": True, "csrf_token": token}), 200


def auth_required(view_func):
    """Decorator to enforce session auth on protected endpoints."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _error("unauthorized", "Login required.", 401)
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Decorator to enforce admin access."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _error("unauthorized", "Login required.", 401)
        if not user.is_admin:
            return _error("admin_forbidden", "Admin access required.", 403)
        return view_func(*args, **kwargs)

    return wrapper
