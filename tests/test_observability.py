from __future__ import annotations

import unittest

from cad_agent.observability import increment_api_request, record_job_enqueued, record_job_result, render_metrics, reset_metrics


class ObservabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_metrics()

    def test_counter_increments_render_metrics_shape(self) -> None:
        increment_api_request("GET", 200)
        increment_api_request("POST", 201)
        record_job_enqueued("cad_golden")
        record_job_result("cad_golden", "completed", 12.5)
        record_job_result("phase2_pilot", "failed", 3.25)

        metrics = render_metrics()

        self.assertIn("# TYPE cad_api_requests_total counter", metrics)
        self.assertIn('cad_api_requests_total{method="GET",status="200"} 1', metrics)
        self.assertIn('cad_api_requests_total{method="POST",status="201"} 1', metrics)
        self.assertIn('# TYPE cad_api_jobs_enqueued_total counter', metrics)
        self.assertIn('cad_api_jobs_enqueued_total{job_type="cad_golden"} 1', metrics)
        self.assertIn('cad_api_jobs_completed_total{job_type="cad_golden"} 1', metrics)
        self.assertIn('cad_api_jobs_failed_total{job_type="phase2_pilot"} 1', metrics)
        self.assertIn('cad_api_job_duration_ms_sum{job_type="cad_golden"} 12.500000', metrics)
        self.assertIn('cad_api_job_duration_ms_count{job_type="cad_golden"} 1', metrics)
        self.assertIn('cad_api_job_duration_ms_sum{job_type="phase2_pilot"} 3.250000', metrics)

    def test_reset_metrics_clears_counters(self) -> None:
        increment_api_request("GET", 200)
        record_job_enqueued("validation")
        record_job_result("validation", "completed", 1.0)
        self.assertIn("cad_api_requests_total", render_metrics())

        reset_metrics()

        self.assertEqual(
            render_metrics(),
            "\n".join(
                [
                    "# HELP cad_api_requests_total Total API requests keyed by HTTP method and status code.",
                    "# TYPE cad_api_requests_total counter",
                    "# HELP cad_api_jobs_enqueued_total Total CAD API jobs accepted into the synchronous queue.",
                    "# TYPE cad_api_jobs_enqueued_total counter",
                    "# HELP cad_api_jobs_completed_total Total CAD API jobs completed successfully.",
                    "# TYPE cad_api_jobs_completed_total counter",
                    "# HELP cad_api_jobs_failed_total Total CAD API jobs that failed.",
                    "# TYPE cad_api_jobs_failed_total counter",
                    "# HELP cad_api_job_duration_ms_sum Total observed CAD API job duration in milliseconds.",
                    "# TYPE cad_api_job_duration_ms_sum counter",
                    "# HELP cad_api_job_duration_ms_count Total observed CAD API job duration samples.",
                    "# TYPE cad_api_job_duration_ms_count counter",
                    "",
                ]
            ),
        )

    def test_metrics_route_request_returns_prometheus_text(self) -> None:
        from cad_agent.api_server import route_request
        from cad_agent.security_policy import CAD_AGENT_API_KEY

        status_code, body, content_type = route_request("GET", "/metrics", {"X-API-Key": CAD_AGENT_API_KEY})

        self.assertEqual(status_code, 200)
        self.assertEqual(content_type, "text/plain; charset=utf-8")
        self.assertIn("# TYPE cad_api_requests_total counter", body)
        self.assertIn("cad_api_requests_total", body)


if __name__ == "__main__":
    unittest.main()
