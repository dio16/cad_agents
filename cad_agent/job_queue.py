from __future__ import annotations

import uuid
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from cad_agent.phase2_pilot import run_phase2_pilot
from cad_agent.platform_poc import DEFAULT_OUTPUT_DIR, run_golden_pipeline

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
SUPPORTED_JOB_TYPES = {"cad_golden", "phase2_pilot", "validation"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_job_id() -> str:
    return f"job_{uuid.uuid4().hex}"


def _new_traceability_id(job_id: str) -> str:
    return f"tr_job_{job_id.removeprefix('job_')}"


@dataclass(slots=True)
class Job:
    job_id: str
    traceability_id: str
    job_type: str
    payload: dict[str, Any]
    status: str
    result: dict[str, Any] | None
    created_at: str
    updated_at: str


class InMemoryJobStore:
    """Deterministic in-memory store used by tests and the local API skeleton."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, job: Job) -> Job:
        stored = deepcopy(job)
        self._jobs[job.job_id] = stored
        return deepcopy(stored)

    def get(self, job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        return deepcopy(job) if job is not None else None

    def update(self, job_id: str, **fields: Any) -> Job | None:
        current = self._jobs.get(job_id)
        if current is None:
            return None
        allowed_fields = {field.name for field in Job.__dataclass_fields__.values()}
        updates = {key: value for key, value in fields.items() if key in allowed_fields}
        updates.setdefault("updated_at", _utc_now())
        updated = replace(current, **updates)
        self._jobs[job_id] = updated
        return deepcopy(updated)

    def list(self) -> list[Job]:
        return [deepcopy(job) for job in self._jobs.values()]

    def reset(self) -> None:
        self._jobs.clear()


class JobRunner(Protocol):
    def run(self, job: Job) -> Job:
        """Execute a job and return the updated job state."""
        ...


class SyncJobRunner:
    """Synchronous runner used by the API server simulation."""

    def run(self, job: Job) -> Job:
        job = replace(job, status=RUNNING, result=None, updated_at=_utc_now())
        try:
            output_dir = self._resolve_output_dir(job)
            if job.job_type == "cad_golden":
                report = run_golden_pipeline(output_dir)
                status = COMPLETED if report.get("status") == "pass" else FAILED
                result = report
            elif job.job_type == "phase2_pilot":
                report = run_phase2_pilot(output_dir)
                status = COMPLETED if report.get("status") == "pass" else FAILED
                result = report
            elif job.job_type == "validation":
                status = COMPLETED
                result = {
                    "status": COMPLETED,
                    "result": {
                        "status": "not_implemented",
                        "message": "validation job stub",
                    },
                }
            else:
                raise ValueError(f"unsupported job_type: {job.job_type}")
        except Exception as exc:
            status = FAILED
            result = {
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            }
        return replace(job, status=status, result=result, updated_at=_utc_now())

    def _resolve_output_dir(self, job: Job) -> Path:
        output_dir = job.payload.get("output_dir")
        if isinstance(output_dir, Path):
            return output_dir
        if isinstance(output_dir, str) and output_dir:
            return Path(output_dir)
        return DEFAULT_OUTPUT_DIR / "jobs" / job.job_id


class JobQueue:
    def __init__(self, store: InMemoryJobStore | None = None, runner: JobRunner | None = None) -> None:
        self.store = store or _default_store
        self.runner = runner or SyncJobRunner()

    def enqueue(self, job_type: str, payload: dict[str, Any], output_dir: Path | str | None = None) -> Job:
        job_id = _new_job_id()
        payload_copy = deepcopy(payload)
        if output_dir is None and not payload_copy.get("output_dir"):
            output_dir = DEFAULT_OUTPUT_DIR / "jobs" / job_id
        if output_dir is not None:
            payload_copy["output_dir"] = str(output_dir)
        else:
            existing_output_dir = payload_copy.get("output_dir")
            if isinstance(existing_output_dir, Path):
                payload_copy["output_dir"] = str(existing_output_dir)
        job = Job(
            job_id=job_id,
            traceability_id=_new_traceability_id(job_id),
            job_type=job_type,
            payload=payload_copy,
            status=PENDING,
            result=None,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        return self.store.create(job)

    def poll(self, job_id: str) -> Job | None:
        return self.store.get(job_id)

    def list(self) -> list[Job]:
        return self.store.list()

    def run_sync(self, job_id: str) -> Job:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        updated = self.runner.run(job)
        return self.store.update(job_id, status=updated.status, result=updated.result, updated_at=updated.updated_at) or updated


_default_store = InMemoryJobStore()


def reset_job_queue() -> None:
    """Clear the process-global job store for deterministic tests."""
    _default_store.reset()


def default_job_queue() -> JobQueue:
    return JobQueue()
