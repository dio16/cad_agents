from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory

from cad_agent.job_queue import FAILED, JobQueue, reset_job_queue


class JobQueueTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_job_queue()

    def test_enqueue_creates_pending_job(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("validation", {"output_dir": temp_dir})

        self.assertTrue(job.job_id.startswith("job_"))
        self.assertTrue(job.traceability_id.startswith("tr_job_"))
        self.assertEqual(job.job_type, "validation")
        self.assertEqual(job.status, "pending")
        self.assertIsNone(job.result)
        self.assertEqual(job.payload["output_dir"], temp_dir)

    def test_run_sync_cad_golden_completes_with_pass_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("cad_golden", {"output_dir": temp_dir})
            updated = queue.run_sync(job.job_id)

        self.assertEqual(updated.status, "completed")
        result = updated.result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["status"], "pass")
        self.assertGreaterEqual(len(result["runtime"]["artifacts"]), 3)

    def test_run_sync_phase2_pilot_completes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("phase2_pilot", {"output_dir": temp_dir})
            updated = queue.run_sync(job.job_id)

        self.assertEqual(updated.status, "completed")
        result = updated.result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["status"], "pass")
        self.assertIn("mesh_artifact", result)
        self.assertIn("review_ui_artifact", result)

    def test_run_sync_validation_returns_stub_completed_result(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("validation", {"output_dir": temp_dir})
            updated = queue.run_sync(job.job_id)

        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.result, {"status": "completed", "result": {"status": "not_implemented", "message": "validation job stub"}})

    def test_run_sync_unknown_job_type_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("unknown_type", {"output_dir": temp_dir})
            updated = queue.run_sync(job.job_id)

        self.assertEqual(updated.status, FAILED)
        result = updated.result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("unsupported job_type", result["error"]["message"])

    def test_poll_returns_job_state_and_none_for_unknown_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("validation", {"output_dir": temp_dir})

            pending = queue.poll(job.job_id)
            self.assertIsNotNone(pending)
            assert pending is not None
            self.assertEqual(pending.status, "pending")

            completed = queue.run_sync(job.job_id)
            self.assertEqual(completed.status, "completed")

            polled = queue.poll(job.job_id)
            self.assertIsNotNone(polled)
            assert polled is not None
            self.assertEqual(polled.status, "completed")
            self.assertIsNone(queue.poll("job_unknown"))

    def test_reset_job_queue_clears_store(self) -> None:
        with TemporaryDirectory() as temp_dir:
            queue = JobQueue()
            job = queue.enqueue("validation", {"output_dir": temp_dir})

        self.assertIsNotNone(queue.poll(job.job_id))
        reset_job_queue()
        self.assertIsNone(queue.poll(job.job_id))
        self.assertEqual(queue.list(), [])


if __name__ == "__main__":
    unittest.main()
