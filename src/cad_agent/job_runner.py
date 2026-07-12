"""E2E job runner — wires agents, DSL AST, CAD runtime, validation, and artifact storage
into a single deterministic pipeline.

Only fixture_pipeline and structured_pipeline modes are executable_now.
llm_pipeline mode is approval_required and raises NotImplementedError.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import platform_poc
from .agents.requirement_extractor import extract_requirement, requirement_fixture
from .agents.spec_composer import compose_specification, specification_fixture
from .orchestrator import CREATED, SPEC_APPROVED, Workflow, WorkflowDecision
from .platform_poc import (
    contract_status,
    golden_dsl,
    validate_parametric_dsl_ast,
    validate_requirement_schema,
    validate_specification_schema,
    validate_artifacts,
    store_artifacts,
)

ALLOWED_MODES = frozenset({"fixture_pipeline", "structured_pipeline"})
# llm_pipeline is approval_required — not executable now


@dataclass
class JobResult:
    """Deterministic output of a single pipeline run."""

    job_id: str
    state: str
    traceability_id: str
    mode: str
    requirement: dict[str, Any] | None = None
    specification: dict[str, Any] | None = None
    dsl: dict[str, Any] | None = None
    runtime: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    artifact_store: dict[str, Any] | None = None
    audit_events: list[dict[str, Any]] = field(default_factory=list)
    blocked: bool = False
    reason_code: str | None = None
    detail: str | None = None


def run_job(
    input_spec: dict[str, Any],
    output_dir: Path | None = None,
) -> JobResult:
    """Run an end-to-end pipeline job.

    input_spec expected keys:
      - mode: "fixture_pipeline" | "structured_pipeline"
      - traceability_id (optional str)
      - requirement (dict, for structured_pipeline)
      - specification (dict, for structured_pipeline)
      - dsl (dict, for structured_pipeline)
      - data_classification (optional str, default "internal")
      - max_revision_loops (optional int, default 3)
    """
    mode = input_spec.get("mode", "fixture_pipeline")
    if mode not in ALLOWED_MODES:
        return JobResult(
            job_id="",
            state="blocked",
            traceability_id="",
            mode=mode,
            blocked=True,
            reason_code="UNSUPPORTED_MODE",
            detail=f"mode={mode!r} not supported; allowed: {sorted(ALLOWED_MODES)}",
        )

    traceability_id = input_spec.get("traceability_id", "")
    if not isinstance(traceability_id, str) or not traceability_id:
        traceability_id = f"tr_job_{mode}"

    max_revision_loops = input_spec.get("max_revision_loops", 3)
    if not isinstance(max_revision_loops, int) or max_revision_loops < 1:
        max_revision_loops = 3

    data_classification = input_spec.get("data_classification", "internal")
    if not isinstance(data_classification, str):
        data_classification = "internal"

    if output_dir is None:
        output_dir = platform_poc.DEFAULT_OUTPUT_DIR / traceability_id
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow = Workflow(CREATED, max_revision_loops=max_revision_loops)

    # ── Step 1: Requirement ────────────────────────────────────────────
    if mode == "structured_pipeline":
        requirement = input_spec.get("requirement")
        if not isinstance(requirement, dict):
            return JobResult(
                job_id=traceability_id,
                state="blocked",
                traceability_id=traceability_id,
                mode=mode,
                blocked=True,
                reason_code="INVALID_REQUIREMENT",
                detail="structured_pipeline requires a 'requirement' dict",
            )
        req_checks = validate_requirement_schema(requirement)
        if contract_status(req_checks) != "pass":
            return JobResult(
                job_id=traceability_id,
                state="blocked",
                traceability_id=traceability_id,
                mode=mode,
                requirement=requirement,
                blocked=True,
                reason_code="REQUIREMENT_SCHEMA_FAILED",
                detail="requirement schema validation failed",
            )
    else:
        requirement = requirement_fixture()

    # ── Step 2: Specification ──────────────────────────────────────────
    if mode == "structured_pipeline":
        specification = input_spec.get("specification")
        if not isinstance(specification, dict):
            return JobResult(
                job_id=traceability_id,
                state="blocked",
                traceability_id=traceability_id,
                mode=mode,
                requirement=requirement,
                blocked=True,
                reason_code="INVALID_SPECIFICATION",
                detail="structured_pipeline requires a 'specification' dict",
            )
        spec_checks = validate_specification_schema(specification)
        if contract_status(spec_checks) != "pass":
            return JobResult(
                job_id=traceability_id,
                state="blocked",
                traceability_id=traceability_id,
                mode=mode,
                requirement=requirement,
                specification=specification,
                blocked=True,
                reason_code="SPECIFICATION_SCHEMA_FAILED",
                detail="specification schema validation failed",
            )
    else:
        specification = specification_fixture(requirement_id=requirement.get("traceability_id", "tr_req_agent_fixture"))
    # Auto-approve spec for fixture and internal data
    spec_id = specification.get("traceability_id", traceability_id)
    spec_decision = workflow.approve_specification(
        spec_id,
        data_classification=data_classification,
    )
    if spec_decision.blocked:
        return JobResult(
            job_id=traceability_id,
            state=workflow.state,
            traceability_id=traceability_id,
            mode=mode,
            requirement=requirement,
            specification=specification,
            blocked=True,
            reason_code="SPEC_APPROVAL_BLOCKED",
            detail=spec_decision.reason or "specification approval blocked",
            audit_events=list(workflow.events),
        )

    # ── Step 3: DSL ────────────────────────────────────────────────────
    if mode == "structured_pipeline":
        dsl = input_spec.get("dsl")
        if not isinstance(dsl, dict):
            return JobResult(
                job_id=traceability_id,
                state="blocked",
                traceability_id=traceability_id,
                mode=mode,
                requirement=requirement,
                specification=specification,
                blocked=True,
                reason_code="INVALID_DSL",
                detail="structured_pipeline requires a 'dsl' dict",
            )
    else:
        dsl = golden_dsl()

    ast_checks = validate_parametric_dsl_ast(dsl)
    if contract_status(ast_checks) != "pass":
        return JobResult(
            job_id=traceability_id,
            state="blocked",
            traceability_id=traceability_id,
            mode=mode,
            requirement=requirement,
            specification=specification,
            dsl=dsl,
            blocked=True,
            reason_code="DSL_AST_VALIDATION_FAILED",
            detail="; ".join(str(c) for c in ast_checks if c.status != "pass"),
        )

    # ── Step 4: CAD Runtime ────────────────────────────────────────────
    cad_decision = workflow.run_cad(
        dsl,
        traceability_id=traceability_id,
        data_classification=data_classification,
    )
    if cad_decision.blocked:
        return JobResult(
            job_id=traceability_id,
            state=workflow.state,
            traceability_id=traceability_id,
            mode=mode,
            requirement=requirement,
            specification=specification,
            dsl=dsl,
            blocked=True,
            reason_code=cad_decision.reason or "CAD_RUN_BLOCKED",
            audit_events=list(workflow.events),
        )

    runtime_output = output_dir / "runtime"
    runtime = platform_poc.run_cad_runtime(dsl, runtime_output)
    if runtime.get("status") != "pass":
        _ = workflow.handle_validation(
            {"pass": False, "failures": [{"reason_code": runtime.get("reason_code", "CAD_RUNTIME_FAILED"), "failure_location": "cad_runtime", "detail": runtime.get("detail", "")}], "traceability_id": traceability_id, "specification_id": specification.get("traceability_id", ""), "artifact_ids": [], "dimensions_check": {}, "topology_check": {}, "unit_consistency": {}, "manufacturing_profile_rules": {}, "artifact_provenance_check": {}, "revision_feedback": []},
            traceability_id=traceability_id,
        )
        return JobResult(
            job_id=traceability_id,
            state=workflow.state,
            traceability_id=traceability_id,
            mode=mode,
            requirement=requirement,
            specification=specification,
            dsl=dsl,
            runtime=runtime,
            blocked=True,
            reason_code=runtime.get("reason_code", "CAD_RUNTIME_FAILED"),
            detail=runtime.get("detail", ""),
            audit_events=list(workflow.events),
        )

    # ── Step 5: Validation ─────────────────────────────────────────────
    workflow.start_validation(traceability_id=traceability_id)
    validation = validate_artifacts(specification, dsl, runtime)
    val_decision = workflow.handle_validation(
        validation,
        traceability_id=traceability_id,
    )
    if val_decision.blocked:
        return JobResult(
            job_id=traceability_id,
            state=workflow.state,
            traceability_id=traceability_id,
            mode=mode,
            requirement=requirement,
            specification=specification,
            dsl=dsl,
            runtime=runtime,
            validation_report=validation,
            blocked=True,
            reason_code="VALIDATION_FAILED",
            detail="validation failed",
            audit_events=list(workflow.events),
        )

    # ── Step 6: Store artifacts (only on validation pass) ──────────────
    store = store_artifacts(runtime, validation, output_dir / "artifact_store")

    return JobResult(
        job_id=traceability_id,
        state=workflow.state,
        traceability_id=traceability_id,
        mode=mode,
        requirement=requirement,
        specification=specification,
        dsl=dsl,
        runtime=runtime,
        validation_report=validation,
        artifact_store=store,
        audit_events=list(workflow.events),
    )
