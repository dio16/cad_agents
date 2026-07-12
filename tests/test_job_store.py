"""Tests for local durable job store (sqlite3-backed)."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from cad_agent.job_store import JobStore


class JobStoreTest(TestCase):
    def test_create_and_get_job(self) -> None:
        store = JobStore(":memory:")
        job_id = store.create_job(state="created")
        record = store.get_job(job_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.job_id, job_id)
        self.assertEqual(record.state, "created")

    def test_update_job_state(self) -> None:
        store = JobStore(":memory:")
        job_id = store.create_job()
        self.assertTrue(store.update_job_state(job_id, "running", {"key": "val"}))
        record = store.get_job(job_id)
        assert record is not None
        self.assertEqual(record.state, "running")
        self.assertEqual(record.result, {"key": "val"})

    def test_update_nonexistent_job_returns_false(self) -> None:
        store = JobStore(":memory:")
        self.assertFalse(store.update_job_state("no-such-job", "running"))

    def test_upsert_creates_new_job(self) -> None:
        store = JobStore(":memory:")
        store.upsert_job("j1", state="running", payload={"a": 1})
        record = store.get_job("j1")
        assert record is not None
        self.assertEqual(record.state, "running")
        self.assertEqual(record.payload, {"a": 1})

    def test_upsert_updates_existing_job(self) -> None:
        store = JobStore(":memory:")
        store.create_job("j1", state="created")
        store.upsert_job("j1", state="done", result={"ok": True})
        record = store.get_job("j1")
        assert record is not None
        self.assertEqual(record.state, "done")
        self.assertEqual(record.result, {"ok": True})

    def test_list_jobs(self) -> None:
        store = JobStore(":memory:")
        store.create_job("a")
        store.create_job("b")
        store.create_job("c")
        jobs = store.list_jobs()
        self.assertEqual(len(jobs), 3)

    def test_durable_across_reopen(self) -> None:
        """Same sqlite file can be reopened and jobs are readable."""
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            store1 = JobStore(db_path)
            job_id = store1.create_job(state="pending")
            store1.record_approval(job_id, "export", "approved", "reviewer1")
            store1.record_audit_event(job_id, "job_started", {"by": "test"})
            store1.close()

            store2 = JobStore(db_path)
            record = store2.get_job(job_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.state, "pending")

            approvals = store2.get_approvals(job_id)
            self.assertEqual(len(approvals), 1)
            self.assertEqual(approvals[0]["decision"], "approved")

            events = store2.get_audit_events(job_id)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_type"], "job_started")
            store2.close()

    def test_approval_persistence(self) -> None:
        store = JobStore(":memory:")
        job_id = store.create_job()
        aid = store.record_approval(job_id, "export", "approved", "tester")
        self.assertTrue(aid)
        self.assertTrue(store.has_export_approval(job_id))

    def test_export_blocked_without_approval(self) -> None:
        store = JobStore(":memory:")
        job_id = store.create_job()
        self.assertFalse(store.has_export_approval(job_id))
        store.record_approval(job_id, "export", "approved")
        self.assertTrue(store.has_export_approval(job_id))

    def test_audit_event_recording(self) -> None:
        store = JobStore(":memory:")
        job_id = store.create_job()
        eid = store.record_audit_event(job_id, "validation_started", {"check": "topology"})
        self.assertTrue(eid)
        events = store.get_audit_events(job_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "validation_started")
        self.assertIn("topology", events[0]["payload_json"])

    def test_close_idempotent(self) -> None:
        store = JobStore(":memory:")
        store.close()
        store.close()  # should not raise

    def test_context_manager(self) -> None:
        with JobStore(":memory:") as store:
            store.create_job("ctx_test")
        # should be closed after context exit

    def test_job_store_integration_with_runner(self) -> None:
        """job_runner with a JobStore must persist job state."""
        from cad_agent.job_runner import run_job

        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "jobs.db"
            store = JobStore(db_path)
            result = run_job({"mode": "fixture_pipeline"}, output_dir=Path(tmp) / "out", job_store=store)
            self.assertFalse(result.blocked)
            self.assertEqual(result.state, "validation_passed")

            # Verify persistence
            record = store.get_job(result.job_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.state, "validation_passed")

            # Verify audit events persisted
            events = store.get_audit_events(result.job_id)
            self.assertGreater(len(events), 0)

            store.close()

    def test_job_store_runner_reopen_readable(self) -> None:
        """Job persisted by runner must be readable after store reopen."""
        from cad_agent.job_runner import run_job

        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "jobs2.db"

            store1 = JobStore(db_path)
            result = run_job(
                {"mode": "fixture_pipeline", "traceability_id": "tr_job_store_reopen"},
                output_dir=Path(tmp) / "out",
                job_store=store1,
            )
            store1.close()

            store2 = JobStore(db_path)
            record = store2.get_job(result.job_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.state, "validation_passed")

            events = store2.get_audit_events(result.job_id)
            self.assertGreater(len(events), 0)
            store2.close()
