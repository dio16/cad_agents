from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from threading import Lock
from typing import Any, DefaultDict

_REQUESTS_TOTAL = "cad_api_requests_total"
_JOBS_ENQUEUED_TOTAL = "cad_api_jobs_enqueued_total"
_JOBS_COMPLETED_TOTAL = "cad_api_jobs_completed_total"
_JOBS_FAILED_TOTAL = "cad_api_jobs_failed_total"
_JOB_DURATION_MS_SUM = "cad_api_job_duration_ms_sum"
_JOB_DURATION_MS_COUNT = "cad_api_job_duration_ms_count"

_METRIC_HELP = {
    _REQUESTS_TOTAL: "Total API requests keyed by HTTP method and status code.",
    _JOBS_ENQUEUED_TOTAL: "Total CAD API jobs accepted into the synchronous queue.",
    _JOBS_COMPLETED_TOTAL: "Total CAD API jobs completed successfully.",
    _JOBS_FAILED_TOTAL: "Total CAD API jobs that failed.",
    _JOB_DURATION_MS_SUM: "Total observed CAD API job duration in milliseconds.",
    _JOB_DURATION_MS_COUNT: "Total observed CAD API job duration samples.",
}

_request_totals: DefaultDict[tuple[str, str], int] = defaultdict(int)
_job_enqueued_totals: DefaultDict[str, int] = defaultdict(int)
_job_completed_totals: DefaultDict[str, int] = defaultdict(int)
_job_failed_totals: DefaultDict[str, int] = defaultdict(int)
_job_duration_ms_sum: DefaultDict[str, float] = defaultdict(float)
_job_duration_ms_count: DefaultDict[str, int] = defaultdict(int)
_metrics_lock = Lock()


def reset_metrics() -> None:
    """Clear all in-process API metrics for deterministic tests."""
    with _metrics_lock:
        _request_totals.clear()
        _job_enqueued_totals.clear()
        _job_completed_totals.clear()
        _job_failed_totals.clear()
        _job_duration_ms_sum.clear()
        _job_duration_ms_count.clear()


def increment_api_request(method: str, status_code: int) -> None:
    """Increment the request counter keyed by HTTP method and status code."""
    with _metrics_lock:
        _request_totals[(method.upper(), str(status_code))] += 1


def record_job_enqueued(job_type: str) -> None:
    """Record that a CAD API job was accepted into the queue."""
    with _metrics_lock:
        _job_enqueued_totals[job_type] += 1


def record_job_result(job_type: str, status: str, duration_ms: float) -> None:
    """Record job completion/failure counters and duration histogram samples."""
    with _metrics_lock:
        if status == "completed":
            _job_completed_totals[job_type] += 1
        elif status == "failed":
            _job_failed_totals[job_type] += 1
        _job_duration_ms_sum[job_type] += duration_ms
        _job_duration_ms_count[job_type] += 1


def render_metrics() -> str:
    """Render metrics in Prometheus text exposition format."""
    with _metrics_lock:
        request_totals = dict(_request_totals)
        job_enqueued_totals = dict(_job_enqueued_totals)
        job_completed_totals = dict(_job_completed_totals)
        job_failed_totals = dict(_job_failed_totals)
        job_duration_ms_sum = dict(_job_duration_ms_sum)
        job_duration_ms_count = dict(_job_duration_ms_count)

    lines: list[str] = []
    _append_help(lines, _REQUESTS_TOTAL)
    _append_counter(lines, _REQUESTS_TOTAL, request_totals, label_names=("method", "status"))
    _append_help(lines, _JOBS_ENQUEUED_TOTAL)
    _append_counter(lines, _JOBS_ENQUEUED_TOTAL, job_enqueued_totals, label_names=("job_type",))
    _append_help(lines, _JOBS_COMPLETED_TOTAL)
    _append_counter(lines, _JOBS_COMPLETED_TOTAL, job_completed_totals, label_names=("job_type",))
    _append_help(lines, _JOBS_FAILED_TOTAL)
    _append_counter(lines, _JOBS_FAILED_TOTAL, job_failed_totals, label_names=("job_type",))
    _append_help(lines, _JOB_DURATION_MS_SUM)
    _append_counter(lines, _JOB_DURATION_MS_SUM, job_duration_ms_sum, label_names=("job_type",), value_formatter=_format_float)
    _append_help(lines, _JOB_DURATION_MS_COUNT)
    _append_counter(lines, _JOB_DURATION_MS_COUNT, job_duration_ms_count, label_names=("job_type",))
    return "\n".join(lines) + "\n"


def _append_help(lines: list[str], metric_name: str) -> None:
    lines.append(f"# HELP {metric_name} {_METRIC_HELP[metric_name]}")


def _append_counter(
    lines: list[str],
    metric_name: str,
    values: Mapping[Any, int | float],
    *,
    label_names: tuple[str, ...],
    value_formatter: Callable[[int | float], str] | None = None,
) -> None:
    lines.append(f"# TYPE {metric_name} counter")
    if not values:
        return
    formatter = value_formatter or str
    for key in sorted(values, key=lambda item: item if isinstance(item, tuple) else (item,)):
        labels = key if isinstance(key, tuple) else (key,)
        label_text = ",".join(f'{name}="{_escape_label(values_label)}"' for name, values_label in zip(label_names, labels, strict=True))
        lines.append(f"{metric_name}{{{label_text}}} {formatter(values[key])}")


def _format_float(value: int | float) -> str:
    return f"{float(value):.6f}"


def _escape_label(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
