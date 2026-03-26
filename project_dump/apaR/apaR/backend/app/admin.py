from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .models import User
from .auth import get_current_user

admin_bp = Blueprint("admin", __name__)


ADMIN_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS admin_runs (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INT DEFAULT 0,
    message TEXT,
    payload JSONB,
    log_path TEXT,
    log_text TEXT,
    error_text TEXT
);
"""


ALLOWED_JOB_TYPES = {"url_discovery", "sniffer", "translate", "full_pipeline", "import_json"}


def _ensure_runs_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(ADMIN_RUNS_TABLE_SQL))


def _row_to_run(row: Any) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "started_at": row["started_at"].isoformat() if row.get("started_at") else None,
        "finished_at": row["finished_at"].isoformat() if row.get("finished_at") else None,
        "job_type": row.get("job_type"),
        "status": row.get("status"),
        "progress": row.get("progress"),
        "message": row.get("message"),
        "payload": row.get("payload") or {},
        "log_path": row.get("log_path"),
        "log_text": row.get("log_text"),
        "error_text": row.get("error_text"),
    }


def _current_running(engine: Engine) -> dict[str, object] | None:
    _ensure_runs_table(engine)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM admin_runs WHERE status = 'running' ORDER BY created_at DESC LIMIT 1")
        ).mappings().first()
        return _row_to_run(row) if row else None


def _list_runs(engine: Engine, limit: int = 50) -> list[dict[str, object]]:
    _ensure_runs_table(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM admin_runs ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}
        ).mappings()
        return [_row_to_run(row) for row in rows]


def _get_run(engine: Engine, run_id: str) -> dict[str, object] | None:
    _ensure_runs_table(engine)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM admin_runs WHERE id = :id"), {"id": run_id}).mappings().first()
        return _row_to_run(row) if row else None


def _insert_run(engine: Engine, job_type: str, payload: dict[str, Any] | None = None) -> dict[str, object]:
    _ensure_runs_table(engine)
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO admin_runs (id, created_at, job_type, status, progress, message, payload)
                VALUES (:id, :created_at, :job_type, 'queued', 0, :message, :payload)
                """
            ),
            {"id": run_id, "created_at": now, "job_type": job_type, "message": "Queued", "payload": payload or {}},
        )
    return _get_run(engine, run_id) or {"id": run_id, "status": "queued"}


@admin_bp.get("/health")
def admin_health() -> tuple[dict[str, str], int]:
    """Lightweight admin ping."""
    return jsonify({"status": "ok"}), 200


@admin_bp.before_request
def require_admin():
    """Ensure only logged-in admins can reach admin endpoints."""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": {"code": "unauthorized", "message": "Login required"}}), 401
    if not user.is_admin:
        return jsonify({"ok": False, "error": {"code": "admin_forbidden", "message": "Admin access required"}}), 403
    return None


@admin_bp.get("/status")
def admin_status() -> tuple[dict[str, object], int]:
    """Return worker state and currently running job (if any)."""
    engine: Engine = current_app.config["DB_ENGINE"]
    try:
        current = _current_running(engine)
        runs = _list_runs(engine, limit=5)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "status_failed", "detail": str(exc)}), 500

    return (
        jsonify(
            {
                "worker_state": "busy" if current else "idle",
                "current_job": current,
                "recent_runs": runs,
            }
        ),
        200,
    )


@admin_bp.get("/runs")
def admin_runs_list() -> tuple[dict[str, object], int]:
    engine: Engine = current_app.config["DB_ENGINE"]
    limit_raw = request.args.get("limit")
    try:
        limit = int(limit_raw) if limit_raw else 50
    except ValueError:
        limit = 50
    try:
        runs = _list_runs(engine, limit=limit)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "list_failed", "detail": str(exc)}), 500
    return jsonify({"runs": runs}), 200


@admin_bp.get("/run/<run_id>")
def admin_run_detail(run_id: str) -> tuple[dict[str, object], int]:
    engine: Engine = current_app.config["DB_ENGINE"]
    try:
        run = _get_run(engine, run_id)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "detail_failed", "detail": str(exc)}), 500
    if not run:
        return jsonify({"error": "not_found"}), 404
    return jsonify(run), 200


@admin_bp.post("/run")
def admin_run_create() -> tuple[dict[str, object], int]:
    engine: Engine = current_app.config["DB_ENGINE"]
    data = request.get_json(silent=True) or {}
    job_type = data.get("job_type")
    payload = data.get("payload") or {}
    if job_type not in ALLOWED_JOB_TYPES:
        return jsonify({"error": "invalid_job_type", "allowed": sorted(ALLOWED_JOB_TYPES)}), 400

    try:
        current = _current_running(engine)
        if current:
            return jsonify({"error": "job_running", "current_job": current}), 409
        run = _insert_run(engine, job_type, payload=payload)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "create_failed", "detail": str(exc)}), 500

    return jsonify(run), 202
