# CAD-FG-02 Task 02 Report

## Status

DONE

## Files changed

- `src/cad_agent/platform_poc.py`: Added deterministic failed-report `revision_feedback`, artifact provenance validation, metadata `cad_kernel` validation, and artifact hash recomputation checks.
- `src/cad_agent/contracts/phase1/validation_report.schema.json`: Added `revision_feedback`, `artifact_provenance_check`, and schema conditions for failed reports.
- `SPEC.md`: Updated Validation Report required keys for `revision_feedback` and `artifact_provenance_check`.
- `tests/test_platform_poc.py`: Added coverage for failed-report feedback, passing-report feedback omission, missing metadata, missing `cad_kernel`, invalid artifact hashes, and metadata hash provenance.
- `TASKS.md`: Recorded CAD-FG-02 validation commands, reviewer verdict, and deviation-check verdict.

## Tests run

- `uv run pytest tests/test_platform_poc.py -q`: pass (`32 passed`)
- `bash ./run_cad_agent.sh phase1-contract-test`: pass (`status: pass`)
- `uv run pytest -q`: pass (`185 passed, 2 subtests passed`)
- `git diff --check`: pass

## Concerns

None.

## Deviation-check verdict

Pass against `docs/cad_agent_detailed_design.md` and `docs/cad_agent_implementation_plan.md`.

- Failed Validation Reports include machine-readable `revision_feedback`.
- Passing Validation Reports keep `revision_feedback` empty.
- Metadata existence, `cad_kernel`, and artifact hash validity are validated as artifact provenance failures when invalid.
- No production artifact storage was added.
- No new CAD feature was added.
- Existing approval boundaries were preserved.
- CAD-FG-03 files were not touched.

## Fix Round 1

### Files changed

- `src/cad_agent/platform_poc.py`: Made `validate_artifacts` tolerant of malformed `runtime_result["artifacts"]` entries. Non-dict entries now produce `ARTIFACT_ENTRY_INVALID`; dict entries missing `artifact_id` now produce `ARTIFACT_ID_MISSING`; missing `path` remains `ARTIFACT_PATH_MISSING`. Metadata and hash validation still feed `artifact_provenance_check` failures with deterministic reason codes. Removed the harmless dead `NON_POSITIVE_VOLUME` branch from `_suggested_revision_action`.
- `tests/test_platform_poc.py`: Added focused regression coverage for non-dict artifact entries, missing `artifact_id`, and missing `path` in runtime artifact entries.
- `docs/VALIDATION_CONTRACT.md`: Updated current PoC validation scope to include `artifact_provenance_check`, including metadata readability, required `cad_kernel`, metadata traceability alignment, artifact paths, and recomputed SHA-256 artifact hashes.

### Tests run

- `uv run pytest tests/test_platform_poc.py -q`: pass (`35 passed`).
- `bash ./run_cad_agent.sh phase1-contract-test`: pass (`status: pass`).
- `git diff --check`: pass.

### Concerns

None.

### Deviation-check verdict

Pass for the CAD-FG-02 reviewer findings. Scope stayed bounded to CAD-FG-02 hardening: no production validation service language was added, no production artifact storage was added, no new CAD feature was added, and CAD-FG-03 files were not touched.
