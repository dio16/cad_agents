# CAD-FG-03 Task 03 Report

## Status

DONE

## Fix Round 1

### Files changed

- `src/cad_agent/api_server.py`: Added local durable JSONL route-audit hook (`set_api_audit_path`, `reset_api_audit_path`), preserved in-memory `get_audit_events`, appended route-decision JSONL records when configured, and recorded the selected default route in `model_route` when no requested route was supplied.
- `tests/test_api_server.py`: Added regression coverage for JSONL audit output, project update route-policy enforcement, workflow run route-policy enforcement, and CAD job creation route-policy enforcement.

### Tests run

- `uv run pytest tests/test_api_server.py tests/test_security.py tests/test_phase2_pilot.py -q`: pass (`56 passed, 2 subtests passed`).
- `uv run pytest tests/test_security.py tests/test_api_server.py -q`: pass (`48 passed`).
- `uv run pytest -q`: pass (`201 passed, 2 subtests passed`).
- `bash ./run_cad_agent.sh serve --dry-run`: pass (`API server dry-run OK: configured for 127.0.0.1:8000`).
- `git diff --check`: pass.
- Forbidden scope check `git status --short -- schemas/v1 .github k8s docker-compose.yml Dockerfile`: pass (no changes).

### Concerns

None.

### Deviation-check verdict

Pass. Fix Round 1 stayed within the CAD-FG-03 reviewer findings: no CAD-FG-02 files were touched, the API audit support remains a small local hook rather than production infrastructure, and the requested route-policy regressions pass.

## Files changed

- `src/cad_agent/security_policy.py`: Centralized `MODEL_GATEWAY_RULES` and allowed data classifications; added allowed-class export for project validation.
- `src/cad_agent/project_service.py`: Added `data_classification` validation for project creation and update.
- `src/cad_agent/api_server.py`: Enforced model route policy in project, requirement, specification, workflow, and CAD job API flows; added local project update routing; preserved in-memory route audit evidence with data classification and routing decision.
- `src/cad_agent/phase2_pilot.py`: Reused the security-policy route decision for pilot gateway probes and included `model_routing` evidence in audit records.
- `tests/test_api_server.py`: Added regression coverage for invalid classifications, public commercial allowance, confidential/regulated/export-controlled commercial rejection, project update validation, and route audit evidence.
- `tests/test_security.py`: Added route-policy coverage for export-controlled commercial rejection, unknown classifications, and allowed-class consistency.
- `tests/test_phase2_pilot.py`: Added audit-record coverage for `data_classification`, `model_route`, and `model_routing`.
- `TASKS.md`: Recorded CAD-FG-03 validation commands, reviewer verdict, and deviation-check verdict.

## Tests run

- `uv run pytest tests/test_security.py tests/test_api_server.py -q`: pass (`48 passed`).
- `uv run pytest -q`: pass (`201 passed, 2 subtests passed`).
- `bash ./run_cad_agent.sh serve --dry-run`: pass (`API server dry-run OK: configured for 127.0.0.1:8000`).
- `git diff --check`: pass.
- Forbidden scope check `git status --short -- schemas/v1 .github k8s docker-compose.yml Dockerfile`: pass (no changes).

## Concerns

None.

## Deviation-check verdict

Pass against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`.

- Project `data_classification` is validated against allowed classes.
- Requirement, specification, API, project, workflow, and CAD job flows enforce the existing commercial/on-prem model route policy when route metadata is supplied.
- Confidential, regulated, and export-controlled data cannot use commercial routes.
- Audit records preserve route/data-classification evidence where applicable.
- No external LLM endpoint was called.
- No production deployment, production auth/worker/storage, or new schemas/v1 were added.
- Existing commercial/on-prem policy and approval boundaries were preserved.
