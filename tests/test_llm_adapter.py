"""Tests for LLM adapter — routing enforcement, mock responses, and opt-in live mode."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from cad_agent.llm_adapter import LLMAdapter, LLMCallResult
from cad_agent.agents.common import AgentRouteResult
from cad_agent.agents.requirement_extractor import extract_requirement_llm
from cad_agent.agents.spec_composer import compose_specification_llm
from cad_agent.job_runner import run_job

ROOT = Path(__file__).resolve().parents[1]


class TestLLMAdapter(TestCase):
    def setUp(self) -> None:
        # Ensure live mode is off for all tests
        self._orig_live = os.environ.get("CAD_AGENT_LLM_LIVE")
        os.environ["CAD_AGENT_LLM_LIVE"] = "0"

    def tearDown(self) -> None:
        if self._orig_live is None:
            os.environ.pop("CAD_AGENT_LLM_LIVE", None)
        else:
            os.environ["CAD_AGENT_LLM_LIVE"] = self._orig_live

    def test_mock_extract_requirement_returns_fixture(self) -> None:
        """In mock mode, extract_requirement must return a valid fixture."""
        adapter = LLMAdapter()
        result = adapter.extract_requirement(
            input_text="Design a pipe clamp for 25mm pipe",
            data_classification="internal",
        )
        self.assertTrue(result.valid)
        self.assertIn("traceability_id", result.json)
        self.assertEqual(result.json.get("product_type"), "single_part")

    def test_mock_compose_specification_returns_fixture(self) -> None:
        """In mock mode, compose_specification must return a valid fixture."""
        adapter = LLMAdapter()
        result = adapter.compose_specification(
            requirement={"traceability_id": "tr_req_test", "product_type": "single_part"},
            data_classification="internal",
        )
        self.assertTrue(result.valid)
        self.assertIn("parameter_table", result.json)

    def test_confidential_classification_blocks_commercial_route(self) -> None:
        """Confidential data must be blocked from commercial route."""
        adapter = LLMAdapter()
        result = adapter.extract_requirement(
            input_text="Design a widget",
            data_classification="confidential",
            requested_route="commercial",
        )
        self.assertFalse(result.valid)
        self.assertIn("ROUTE", result.reason_code or "")

    def test_internal_classification_allows_hybrid_route(self) -> None:
        """Internal data must be allowed on hybrid route."""
        adapter = LLMAdapter()
        result = adapter.extract_requirement(
            input_text="Design a widget",
            data_classification="internal",
            requested_route="hybrid",
        )
        self.assertTrue(result.valid)

    def test_audit_event_written(self) -> None:
        """LLM adapter must write audit events when audit_path is set."""
        with TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "llm_audit.jsonl"
            adapter = LLMAdapter(audit_path=audit_path)
            adapter.extract_requirement(
                input_text="Design a widget",
                data_classification="internal",
                traceability_id="tr_test_audit",
            )
            self.assertTrue(audit_path.exists())
            lines = audit_path.read_text().strip().split("\n")
            self.assertGreater(len(lines), 0)
            event = json.loads(lines[0])
            self.assertEqual(event["event_type"], "llm_adapter_call")
            self.assertEqual(event["agent_route"], "requirement_extractor")

    def test_llm_pipeline_mode_runs_in_mock(self) -> None:
        """llm_pipeline mode must complete in mock mode (no live endpoint)."""
        with TemporaryDirectory() as tmp:
            result = run_job(
                {
                    "mode": "llm_pipeline",
                    "design_intent": "Design a pipe clamp for a 25mm pipe with two screw holes",
                    "traceability_id": "tr_job_llm_test",
                    "data_classification": "internal",
                },
                output_dir=Path(tmp) / "out",
            )
        self.assertFalse(result.blocked, f"blocked: reason={result.reason_code} detail={result.detail}")
        self.assertEqual(result.state, "validation_passed")
        self.assertIsNotNone(result.requirement)
        self.assertIsNotNone(result.specification)


class TestLLMAgentRoutes(TestCase):
    def setUp(self) -> None:
        self._orig_live = os.environ.get("CAD_AGENT_LLM_LIVE")
        os.environ["CAD_AGENT_LLM_LIVE"] = "0"

    def tearDown(self) -> None:
        if self._orig_live is None:
            os.environ.pop("CAD_AGENT_LLM_LIVE", None)
        else:
            os.environ["CAD_AGENT_LLM_LIVE"] = self._orig_live

    def test_extract_requirement_llm_returns_fixture_in_mock(self) -> None:
        result = extract_requirement_llm(
            input_text="Design a bracket for mounting a sensor",
            data_classification="internal",
            traceability_id="tr_test_1",
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.json.get("product_type"), "single_part")
        self.assertEqual(result.metadata.get("route"), "requirement_extractor_llm")

    def test_extract_requirement_llm_blocks_confidential_commercial(self) -> None:
        result = extract_requirement_llm(
            input_text="Design a bracket",
            data_classification="confidential",
            requested_route="commercial",
            traceability_id="tr_test_2",
        )
        self.assertFalse(result.valid)
        self.assertIn("ROUTE", result.reason_code or "")

    def test_compose_specification_llm_returns_fixture_in_mock(self) -> None:
        from cad_agent.agents.requirement_extractor import requirement_fixture

        result = compose_specification_llm(
            requirement=requirement_fixture(),
            data_classification="internal",
            traceability_id="tr_test_3",
        )
        self.assertTrue(result.valid)
        self.assertIn("parameter_table", result.json)
        self.assertIn("material_candidates", result.json)


class TestLLMAdapterIntegration(TestCase):
    """Integration: llm_pipeline mode via CLI and job_runner."""

    def setUp(self) -> None:
        self._orig_live = os.environ.get("CAD_AGENT_LLM_LIVE")
        os.environ["CAD_AGENT_LLM_LIVE"] = "0"

    def tearDown(self) -> None:
        if self._orig_live is None:
            os.environ.pop("CAD_AGENT_LLM_LIVE", None)
        else:
            os.environ["CAD_AGENT_LLM_LIVE"] = self._orig_live

    def test_run_job_llm_pipeline_blocked_without_design_intent(self) -> None:
        """llm_pipeline without design_intent must block."""
        result = run_job({"mode": "llm_pipeline"})
        self.assertTrue(result.blocked)
        self.assertEqual(result.reason_code, "INVALID_DESIGN_INTENT")

    def test_run_job_llm_pipeline_blocked_confidential_commercial(self) -> None:
        """llm_pipeline with confidential+commercial must block at routing."""
        result = run_job(
            {
                "mode": "llm_pipeline",
                "design_intent": "Design a secret widget",
                "data_classification": "confidential",
                "model_route": "commercial",
                "traceability_id": "tr_blocked_conf",
            }
        )
        self.assertTrue(result.blocked)
        # Reason code from routing failure
        self.assertIsNotNone(result.reason_code)

    def test_cli_run_job_llm_pipeline(self) -> None:
        """CLI run-job with llm_pipeline input must succeed in mock mode."""
        input_spec = json.dumps(
            {
                "mode": "llm_pipeline",
                "design_intent": "Design a simple bracket",
                "traceability_id": "tr_cli_llm",
            }
        )
        proc = subprocess.run(
            [sys.executable, "-m", "cad_agent.cli", "run-job"],
            input=input_spec,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = json.loads(proc.stdout)
        self.assertEqual(output.get("blocked"), False)
        self.assertEqual(output.get("state"), "validation_passed")
        self.assertEqual(output.get("mode"), "llm_pipeline")
