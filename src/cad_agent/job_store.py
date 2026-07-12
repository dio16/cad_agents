"""Local durable job store backed by stdlib sqlite3.

Maturity: local_durable_stub — single local developer use. No replication,
backup, or multi-process lock coordination.

Tables:
  - jobs:      job_id, state, payload_json, result_json, created_at, updated_at
  - approvals: approval_id, job_id, approval_type, decision, approver, recorded_at
  - audit_events: event_id, job_id, event_type, payload_json, recorded_at
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id       TEXT PRIMARY KEY,
    state        TEXT NOT NULL DEFAULT 'created',
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json  TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id  TEXT PRIMARY KEY,
    job_id       TEXT NOT NULL REFERENCES jobs(job_id),
    approval_type TEXT NOT NULL,
    decision     TEXT NOT NULL,
    approver     TEXT NOT NULL DEFAULT '',
    recorded_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id     TEXT PRIMARY KEY,
    job_id       TEXT NOT NULL REFERENCES jobs(job_id),
    event_type   TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    recorded_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_approvals_job_id ON approvals(job_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_job_id ON audit_events(job_id);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return uuid.uuid4().hex


@dataclass
class JobRecord:
    job_id: str
    state: str
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class JobStore:
    """Local sqlite3-backed durable job store."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._db_path = Path(db_path) if db_path != ":memory:" else Path(":memory:")
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    @property
    def db_path(self) -> Path:
        return self._db_path

    # ── job CRUD ────────────────────────────────────────────────────────

    def create_job(self, job_id: str | None = None, state: str = "created", payload: dict[str, Any] | None = None) -> str:
        """Create a job row and return its job_id."""
        job_id = job_id or _uid()
        now = _utcnow()
        self._conn.execute(
            "INSERT INTO jobs (job_id, state, payload_json, result_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, state, json.dumps(payload or {}), "{}", now, now),
        )
        self._conn.commit()
        return job_id

    def get_job(self, job_id: str) -> JobRecord | None:
        """Retrieve a job by id, or None."""
        row = self._conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return JobRecord(
            job_id=row["job_id"],
            state=row["state"],
            payload=json.loads(row["payload_json"]),
            result=json.loads(row["result_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_job_state(self, job_id: str, state: str, result: dict[str, Any] | None = None) -> bool:
        """Update job state and optionally result. Returns True if a row was updated."""
        now = _utcnow()
        cursor = self._conn.execute(
            "UPDATE jobs SET state = ?, result_json = ?, updated_at = ? WHERE job_id = ?",
            (state, json.dumps(result or {}), now, job_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def upsert_job(self, job_id: str, state: str = "created", payload: dict[str, Any] | None = None, result: dict[str, Any] | None = None) -> str:
        """Insert or update a job row."""
        existing = self.get_job(job_id)
        now = _utcnow()
        if existing is None:
            self._conn.execute(
                "INSERT INTO jobs (job_id, state, payload_json, result_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, state, json.dumps(payload or {}), json.dumps(result or {}), now, now),
            )
        else:
            self._conn.execute(
                "UPDATE jobs SET state = ?, payload_json = ?, result_json = ?, updated_at = ? WHERE job_id = ?",
                (state, json.dumps(payload or existing.payload), json.dumps(result or existing.result), now, job_id),
            )
        self._conn.commit()
        return job_id

    def list_jobs(self, limit: int = 50, offset: int = 0) -> list[JobRecord]:
        rows = self._conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return [
            JobRecord(
                job_id=r["job_id"],
                state=r["state"],
                payload=json.loads(r["payload_json"]),
                result=json.loads(r["result_json"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    # ── approvals ──────────────────────────────────────────────────────

    def record_approval(self, job_id: str, approval_type: str, decision: str, approver: str = "") -> str:
        """Record an approval decision. Returns approval_id."""
        approval_id = _uid()
        now = _utcnow()
        self._conn.execute(
            "INSERT INTO approvals (approval_id, job_id, approval_type, decision, approver, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
            (approval_id, job_id, approval_type, decision, approver, now),
        )
        self._conn.commit()
        return approval_id

    def get_approvals(self, job_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM approvals WHERE job_id = ? ORDER BY recorded_at", (job_id,)).fetchall()
        return [dict(r) for r in rows]

    def has_export_approval(self, job_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM approvals WHERE job_id = ? AND approval_type = 'export' AND decision = 'approved' LIMIT 1",
            (job_id,),
        ).fetchone()
        return row is not None

    # ── audit ──────────────────────────────────────────────────────────

    def record_audit_event(self, job_id: str, event_type: str, payload: dict[str, Any] | None = None) -> str:
        event_id = _uid()
        now = _utcnow()
        self._conn.execute(
            "INSERT INTO audit_events (event_id, job_id, event_type, payload_json, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (event_id, job_id, event_type, json.dumps(payload or {}), now),
        )
        self._conn.commit()
        return event_id

    def get_audit_events(self, job_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM audit_events WHERE job_id = ? ORDER BY recorded_at", (job_id,)).fetchall()
        return [dict(r) for r in rows]

    # ── lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> JobStore:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
