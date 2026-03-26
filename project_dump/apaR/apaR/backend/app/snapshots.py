from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


SNAPSHOT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS data_snapshots (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_file TEXT,
    meta JSONB,
    payload JSONB NOT NULL
);
"""


def ensure_snapshot_table(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text(SNAPSHOT_TABLE_SQL))
        # Ensure newer columns exist
        conn.execute(text("ALTER TABLE data_snapshots ADD COLUMN IF NOT EXISTS meta JSONB"))
        conn.commit()


def save_snapshot(engine: Engine, dataset: dict[str, Any], source_file: str | None = None) -> None:
    """Persist a snapshot of the dataset for audit/history."""
    ensure_snapshot_table(engine)
    payload = json.loads(json.dumps(dataset))  # ensure JSON-serializable copy
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO data_snapshots (created_at, source_file, meta, payload)
                VALUES (:created_at, :source_file, :meta, :payload)
                """
            ),
            {
                "created_at": datetime.now(timezone.utc),
                "source_file": source_file,
                "meta": payload.get("meta", {}),
                "payload": payload,
            },
        )


def latest_snapshot(engine: Engine) -> dict[str, Any] | None:
    ensure_snapshot_table(engine)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, created_at, source_file, meta, payload FROM data_snapshots ORDER BY created_at DESC LIMIT 1")
        ).mappings().first()
        return dict(row) if row else None


def list_snapshots(engine: Engine, limit: int = 20) -> list[dict[str, Any]]:
    ensure_snapshot_table(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, created_at, source_file, meta, payload FROM data_snapshots ORDER BY created_at DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]
