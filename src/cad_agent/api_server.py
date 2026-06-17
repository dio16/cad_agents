from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from cad_agent.job_queue import JobQueue
from cad_agent.observability import increment_api_request, record_job_enqueued, record_job_result, render_metrics
from cad_agent.platform_poc import golden_requirement, golden_specification
from cad_agent.project_service import create_project
from cad_agent.security_policy import check_api_key, is_allowed_raw_code

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_INDEX_PATHS = (
    ROOT / "artifacts" / "phase1_poc" / "artifact_store" / "artifact_index.jsonl",
    ROOT / "artifacts" / "phase2_pilot" / "artifact_store" / "artifact_index.jsonl",
    ROOT / "artifacts" / "phase2_pilot_validation" / "baseline" / "artifact_store" / "artifact_index.jsonl",
)
JSON_CONTENT_TYPE = "application/json; charset=utf-8"
TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"
NOT_IMPLEMENTED_BODY = {
    "status": "not_implemented",
    "message": "endpoint not implemented",
}
SUPPORTED_JOB_TYPES = {"cad_golden", "phase2_pilot", "validation"}
DEFAULT_JOB_QUEUE = JobQueue()
_PARSE_ERROR = object()


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def _parse_body(body: bytes | dict[str, Any] | None) -> dict[str, Any] | object:
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    if isinstance(body, bytes):
        if not body:
            return {}
        try:
            decoded = body.decode("utf-8")
        except UnicodeDecodeError:
            return _PARSE_ERROR
        if not decoded.strip():
            return {}
        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError:
            return _PARSE_ERROR
        return parsed if isinstance(parsed, dict) else _PARSE_ERROR
    if isinstance(body, str):
        if not body.strip():
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return _PARSE_ERROR
        return parsed if isinstance(parsed, dict) else _PARSE_ERROR
    return _PARSE_ERROR


def _relative_artifact_path(raw_path: str) -> str:
    path = Path(raw_path)
    if ".." in path.parts:
        return ""
    if path.is_absolute():
        try:
            return path.resolve(strict=False).relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return path.name
    return path.as_posix()


def _normalize_artifact_record(record: dict[str, Any]) -> dict[str, Any] | None:
    artifact_id = record.get("artifact_id")
    artifact_format = record.get("format")
    raw_path = record.get("path")
    artifact_hash = record.get("artifact_hash")
    if not isinstance(artifact_id, str) or not isinstance(artifact_format, str) or not isinstance(raw_path, str):
        return None
    relative_path = _relative_artifact_path(raw_path)
    if not relative_path or relative_path.startswith("../"):
        return None
    return {
        "artifact_id": artifact_id,
        "format": artifact_format,
        "path": relative_path,
        "artifact_hash": artifact_hash,
    }


def lookup_artifact(artifact_id: str) -> dict[str, Any] | None:
    for index_path in ARTIFACT_INDEX_PATHS:
        if not index_path.exists():
            continue
        with index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict) or record.get("artifact_id") != artifact_id:
                    continue
                normalized = _normalize_artifact_record(record)
                if normalized is not None:
                    return normalized
    return None


def _stub_requirement() -> dict[str, Any]:
    requirement = golden_requirement()
    requirement["mode"] = "stub"
    return requirement


def _stub_specification() -> dict[str, Any]:
    specification = golden_specification()
    specification["mode"] = "stub"
    return specification


def _error_body(message: str) -> dict[str, str]:
    return {"status": "error", "message": message}


def _append_unique_artifact_id(artifact_ids: list[str], artifact_id: Any) -> None:
    if isinstance(artifact_id, str) and artifact_id and artifact_id not in artifact_ids:
        artifact_ids.append(artifact_id)


def _collect_artifact_ids(value: Any) -> list[str]:
    seen: set[str] = set()
    artifact_ids: list[str] = []

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            _append_unique_artifact_id(artifact_ids, node.get("artifact_id"))
            if isinstance(node.get("artifact_id"), str) and node["artifact_id"]:
                seen.add(node["artifact_id"])
            for key in ("artifacts", "records"):
                items = node.get(key)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            artifact_id = item.get("artifact_id")
                            if isinstance(artifact_id, str) and artifact_id and artifact_id not in seen:
                                seen.add(artifact_id)
                                artifact_ids.append(artifact_id)
            for key in ("mesh_artifact", "review_ui_artifact"):
                item = node.get(key)
                if isinstance(item, dict):
                    artifact_id = item.get("artifact_id")
                    if isinstance(artifact_id, str) and artifact_id and artifact_id not in seen:
                        seen.add(artifact_id)
                        artifact_ids.append(artifact_id)
            for nested in node.values():
                if isinstance(nested, (dict, list)):
                    collect(nested)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(value)
    return artifact_ids


def _job_response(job: Any) -> dict[str, Any]:
    response: dict[str, Any] = {
        "job_id": job.job_id,
        "status": job.status,
        "job_type": job.job_type,
        "traceability_id": job.traceability_id,
        "created_at": job.created_at,
        "artifacts": _collect_artifact_ids(job.result),
    }
    if job.result is not None:
        response["result"] = job.result
    return response


def _create_cad_job(payload: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
    job_type = payload.get("job_type", "cad_golden")
    if not isinstance(job_type, str):
        return 400, _error_body("job_type must be a string"), JSON_CONTENT_TYPE
    if job_type not in SUPPORTED_JOB_TYPES:
        return 400, _error_body(f"unsupported job_type: {job_type}"), JSON_CONTENT_TYPE

    output_dir = payload.get("output_dir")
    if output_dir is not None and not isinstance(output_dir, (str, Path)):
        return 400, _error_body("output_dir must be a string path"), JSON_CONTENT_TYPE

    job = DEFAULT_JOB_QUEUE.enqueue(job_type, payload)
    record_job_enqueued(job_type)
    started_at = perf_counter()
    try:
        job = DEFAULT_JOB_QUEUE.run_sync(job.job_id)
    except Exception:
        record_job_result(job_type, "failed", (perf_counter() - started_at) * 1000.0)
        raise
    record_job_result(job_type, job.status, (perf_counter() - started_at) * 1000.0)
    return 201, _job_response(job), JSON_CONTENT_TYPE


def route_request(
    method: str,
    path: str,
    headers: Any | None = None,
    body: bytes | dict[str, Any] | None = None,
) -> tuple[int, Any, str]:
    try:
        status_code, response_body, content_type = _route_request(method, path, headers, body)
    except Exception:
        increment_api_request(method, 500)
        raise
    increment_api_request(method, status_code)
    return status_code, response_body, content_type


def _route_request(
    method: str,
    path: str,
    headers: Any | None = None,
    body: bytes | dict[str, Any] | None = None,
) -> tuple[int, Any, str]:
    headers = headers or {}
    path_only = urlparse(path).path
    normalized_method = method.upper()

    if normalized_method == "GET" and path_only == "/health":
        return 200, {"status": "ok"}, JSON_CONTENT_TYPE

    if not check_api_key(headers or {}):
        return 401, _error_body("missing or invalid API key"), JSON_CONTENT_TYPE

    if normalized_method == "GET" and path_only == "/metrics":
        return 200, render_metrics(), TEXT_CONTENT_TYPE

    if normalized_method == "GET" and path_only.startswith("/v1/artifacts/"):
        artifact_id = path_only.removeprefix("/v1/artifacts/")
        if not artifact_id:
            return 404, _error_body("artifact_id is required"), JSON_CONTENT_TYPE
        artifact = lookup_artifact(artifact_id)
        if artifact is None:
            return 404, _error_body("artifact not found"), JSON_CONTENT_TYPE
        return 200, artifact, JSON_CONTENT_TYPE

    if normalized_method == "GET" and path_only.startswith("/v1/cad/jobs/"):
        job_id = path_only.removeprefix("/v1/cad/jobs/")
        if not job_id:
            return 404, _error_body("job not found"), JSON_CONTENT_TYPE
        job = DEFAULT_JOB_QUEUE.poll(job_id)
        if job is None:
            return 404, _error_body("job not found"), JSON_CONTENT_TYPE
        return 200, _job_response(job), JSON_CONTENT_TYPE

    if normalized_method == "POST":
        payload = _parse_body(body)
        if payload is _PARSE_ERROR:
            return 400, _error_body("invalid JSON body"), JSON_CONTENT_TYPE
        assert isinstance(payload, dict)

        if not is_allowed_raw_code(payload):
            return 403, _error_body("allow_raw_code=true is not allowed"), JSON_CONTENT_TYPE

        if path_only == "/v1/projects":
            name = payload.get("name")
            description = payload.get("description")
            if not isinstance(name, str) or not isinstance(description, str):
                return 400, _error_body("name and description are required"), JSON_CONTENT_TYPE
            classification = payload.get("data_classification", "internal")
            if not isinstance(classification, str):
                return 400, _error_body("data_classification must be a string"), JSON_CONTENT_TYPE
            project = create_project(name=name, description=description, data_classification=classification)
            return 201, project, JSON_CONTENT_TYPE

        if path_only == "/v1/requirements/extract":
            return 200, _stub_requirement(), JSON_CONTENT_TYPE

        if path_only == "/v1/specifications/generate":
            return 200, _stub_specification(), JSON_CONTENT_TYPE

        if path_only == "/v1/cad/jobs":
            return _create_cad_job(payload)

        if path_only in {"/v1/validation/jobs", "/v1/revisions", "/v1/exports"}:
            return 501, NOT_IMPLEMENTED_BODY, JSON_CONTENT_TYPE

    return 404, _error_body("endpoint not found"), JSON_CONTENT_TYPE


class CADAgentAPIHandler(BaseHTTPRequestHandler):
    server_version = "CADAgentAPI/0.1"
    sys_version = ""

    def do_GET(self) -> None:
        status_code, response_body, content_type = route_request(self.command, self.path, self.headers)
        if content_type.startswith("text/plain"):
            self._send_text(status_code, str(response_body), content_type)
        else:
            self._send_json(status_code, response_body)

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            increment_api_request("POST", 400)
            self._send_json(400, _error_body("invalid Content-Length"))
            return
        body = self.rfile.read(content_length) if content_length else None
        status_code, response_body, content_type = route_request(self.command, self.path, self.headers, body)
        if content_type.startswith("text/plain"):
            self._send_text(status_code, str(response_body), content_type)
        else:
            self._send_json(status_code, response_body)

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def _send_json(self, status_code: int, body: Any) -> None:
        data = _json_bytes(body)
        self.send_response(status_code)
        self.send_header("Content-Type", JSON_CONTENT_TYPE)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status_code: int, body: str, content_type: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> HTTPServer:
    return HTTPServer((host, port), CADAgentAPIHandler)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def instantiate_handler() -> CADAgentAPIHandler:
    class NoopRequest:
        def makefile(self, *args: Any, **kwargs: Any) -> Any:
            class NoopFile:
                def close(self) -> None:
                    return None

            return NoopFile()

    class NoopServer:
        server_address = ("127.0.0.1", 0)
        RequestHandlerClass = CADAgentAPIHandler

    class DryRunHandler(CADAgentAPIHandler):
        def setup(self) -> None:
            return None

        def handle(self) -> None:
            return None

        def finish(self) -> None:
            return None

    return DryRunHandler(NoopRequest(), ("127.0.0.1", 0), NoopServer())  # type: ignore[arg-type]
