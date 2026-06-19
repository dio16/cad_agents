from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from cad_agent.api_server import ARTIFACT_INDEX_PATHS, route_request
from cad_agent.job_queue import default_job_queue, reset_job_queue
from cad_agent.observability import render_metrics, reset_metrics
from cad_agent.platform_poc import golden_requirement, golden_specification
from cad_agent.project_service import reset_projects
from cad_agent.security_policy import CAD_AGENT_API_KEY


AUTH_HEADERS = {"X-API-Key": CAD_AGENT_API_KEY}


class APIServerTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_metrics()
        reset_projects()
        reset_job_queue()

    def _route(self, method: str, path: str, headers: dict[str, Any] | None = None, body: bytes | dict[str, Any] | None = None):
        return route_request(method, path, headers or {}, body)

    def test_health(self) -> None:
        status_code, body, content_type = self._route("GET", "/health")

        self.assertEqual(status_code, 200)
        self.assertEqual(body, {"status": "ok"})
        self.assertEqual(content_type, "application/json; charset=utf-8")

    def test_create_project(self) -> None:
        status_code, body, content_type = self._route(
            "POST",
            "/v1/projects",
            AUTH_HEADERS,
            {"name": "fixture clamp", "description": "local test project"},
        )

        self.assertEqual(status_code, 201)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["name"], "fixture clamp")
        self.assertEqual(body["description"], "local test project")
        self.assertEqual(body["data_classification"], "internal")
        self.assertTrue(body["project_id"].startswith("proj_"))
        self.assertTrue(body["created_at"].endswith("+00:00"))
        self.assertTrue(body["updated_at"].endswith("+00:00"))

    def test_create_project_unauthorized(self) -> None:
        status_code, body, content_type = self._route(
            "POST",
            "/v1/projects",
            {},
            {"name": "fixture clamp", "description": "local test project"},
        )

        self.assertEqual(status_code, 401)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertIn("API key", body["message"])

    def test_get_artifact_lookup(self) -> None:
        artifact_id = self._existing_artifact_id()
        if artifact_id is None:
            with TemporaryDirectory() as temp_dir:
                index_path = Path(temp_dir) / "artifact_index.jsonl"
                index_path.write_text(
                    json.dumps(
                        {
                            "artifact_id": "art_mock_step",
                            "format": "step_ap242",
                            "path": "artifacts/mock/fixture.step",
                            "artifact_hash": "sha256:mock",
                        },
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                with mock.patch("cad_agent.api_server.ARTIFACT_INDEX_PATHS", (index_path,)):
                    status_code, body, content_type = self._route("GET", "/v1/artifacts/art_mock_step", AUTH_HEADERS)
        else:
            status_code, body, content_type = self._route(f"GET", f"/v1/artifacts/{artifact_id}", AUTH_HEADERS)

        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(set(body), {"artifact_id", "format", "path", "artifact_hash"})
        self.assertFalse(Path(body["path"]).is_absolute())
        self.assertEqual(body["artifact_hash"].startswith("sha256:"), True)

    def test_get_artifact_not_found(self) -> None:
        status_code, body, content_type = self._route("GET", "/v1/artifacts/art_unknown", AUTH_HEADERS)

        self.assertEqual(status_code, 404)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["message"], "artifact not found")

    def test_requirements_extract_stub(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/requirements/extract", AUTH_HEADERS)

        expected = golden_requirement()
        expected["mode"] = "stub"
        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body, expected)

    def test_allow_raw_code_rejected(self) -> None:
        status_code, body, content_type = self._route(
            "POST",
            "/v1/requirements/extract",
            AUTH_HEADERS,
            {"allow_raw_code": True},
        )

        self.assertEqual(status_code, 403)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertIn("allow_raw_code", body["message"])

    def test_workflow_run_requires_spec_approval(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/workflows/run", AUTH_HEADERS, {"traceability_id": "tr-test"})

        self.assertEqual(status_code, 400)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["reason"], "SPEC_APPROVAL_REQUIRED")
        self.assertTrue(body["blocked"])

    def test_specifications_generate_stub(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/specifications/generate", AUTH_HEADERS)

        expected = golden_specification()
        expected["mode"] = "stub"
        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body, expected)

    def test_create_cad_job_runs_golden_pipeline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            status_code, body, content_type = self._route(
                "POST",
                "/v1/cad/jobs",
                AUTH_HEADERS,
                {"output_dir": temp_dir},
            )

        self.assertEqual(status_code, 201)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["job_type"], "cad_golden")
        self.assertTrue(body["job_id"].startswith("job_"))
        self.assertTrue(body["traceability_id"].startswith("tr_job_"))
        self.assertEqual(body["result"]["status"], "pass")
        self.assertGreaterEqual(len(body["artifacts"]), 3)
        self.assertTrue(any(artifact_id.startswith("art_tr_dsl_phase1_pipe_clamp_") for artifact_id in body["artifacts"]))

        metrics = render_metrics()
        self.assertIn('cad_api_jobs_enqueued_total{job_type="cad_golden"} 1', metrics)
        self.assertIn('cad_api_jobs_completed_total{job_type="cad_golden"} 1', metrics)
        self.assertIn('cad_api_job_duration_ms_count{job_type="cad_golden"} 1', metrics)

    def test_get_cad_job_polls_existing_job(self) -> None:
        with TemporaryDirectory() as temp_dir:
            _, created_body, _ = self._route(
                "POST",
                "/v1/cad/jobs",
                AUTH_HEADERS,
                {"output_dir": temp_dir},
            )
            status_code, body, content_type = self._route(f"GET", f"/v1/cad/jobs/{created_body['job_id']}", AUTH_HEADERS)

        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["job_id"], created_body["job_id"])
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["job_type"], "cad_golden")

    def test_get_cad_job_not_found(self) -> None:
        status_code, body, content_type = self._route("GET", "/v1/cad/jobs/job_unknown", AUTH_HEADERS)

        self.assertEqual(status_code, 404)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["message"], "job not found")

    def test_allow_raw_code_rejected_for_cad_jobs(self) -> None:
        status_code, body, content_type = self._route(
            "POST",
            "/v1/cad/jobs",
            AUTH_HEADERS,
            {"allow_raw_code": True},
        )

        self.assertEqual(status_code, 403)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertIn("allow_raw_code", body["message"])
        self.assertEqual(default_job_queue().list(), [])

    def test_validation_jobs_not_implemented(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/validation/jobs", AUTH_HEADERS)

        self.assertEqual(status_code, 501)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "not_implemented")

    def test_revisions_not_implemented(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/revisions", AUTH_HEADERS)

        self.assertEqual(status_code, 501)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "not_implemented")

    def test_exports_not_implemented(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/exports", AUTH_HEADERS)

        self.assertEqual(status_code, 501)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "not_implemented")

    def test_invalid_json_body(self) -> None:
        status_code, body, content_type = self._route("POST", "/v1/projects", AUTH_HEADERS, b"not-json")

        self.assertEqual(status_code, 400)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        self.assertEqual(body["status"], "error")
        self.assertIn("JSON", body["message"])

    def test_metrics_endpoint(self) -> None:
        self._route("GET", "/health", AUTH_HEADERS)
        status_code, body, content_type = self._route("GET", "/metrics", AUTH_HEADERS)

        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "text/plain; charset=utf-8")
        self.assertIn("# TYPE cad_api_requests_total counter", body)
        self.assertIn('cad_api_requests_total{method="GET",status="200"} 1', body)

    @staticmethod
    def _existing_artifact_id() -> str | None:
        for index_path in ARTIFACT_INDEX_PATHS:
            if not index_path.exists():
                continue
            for line in index_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if isinstance(record, dict) and isinstance(record.get("artifact_id"), str):
                    return record["artifact_id"]
        return None


if __name__ == "__main__":
    unittest.main()
