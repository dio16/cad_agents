# CAD Agents: AI Machine Design Platform

This repository now tracks the reference architecture for an AI-assisted mechanical design platform. The original proposal is [`docs/Origen/Design_document_for_a_machine_design_platform.md`](docs/Origen/Design_document_for_a_machine_design_platform.md); every maintained document and script is aligned to that proposal.

## Core principle

Do **not** ask an LLM to emit executable CAD code from free text. The platform uses a gated pipeline:

1. natural-language design intent
2. `Requirement JSON`
3. `Specification JSON`
4. validated `Parametric DSL`
5. deterministic CAD runtime / worker probes for OCCT / FreeCAD / Blender executables; native mode is recorded only when executables are present, otherwise deterministic surrogate adapters are used
6. validation reports for geometry, DFM/AM, with assembly interference and FEA treated as future-scope validation concepts; separate AABB assembly stubs exist as Production v2 data-model skeletons
7. current PoC/Pilot outputs include deterministic STEP surrogate, STL, and OBJ surrogate; glTF, PNG, and PDF remain export targets

The LLM is a design planner, the CAD kernel is the executor, and validation is the quality gate.

## Canonical files

| File | Purpose |
|---|---|
| [`GOAL.md`](GOAL.md) | Repository mission, non-goals, and acceptance criteria |
| [`SPEC.md`](SPEC.md) | System architecture and data contracts |
| [`TASKS.md`](TASKS.md) | Implementation roadmap derived from the proposal |
| [`AGENTS.md`](AGENTS.md) | Agent responsibility and safety operating rules |
| [`docs/architecture_ja.md`](docs/architecture_ja.md) | Japanese architecture summary |
| [`docs/api_contracts_ja.md`](docs/api_contracts_ja.md) | API, schema, and traceability contracts |
| [`docs/validation_security_ja.md`](docs/validation_security_ja.md) | Validation, audit, and security gates |
| [`docs/operations_ja.md`](docs/operations_ja.md) | CI/CD, runtime, and operational model |

Legacy tourbillon-specific documents and scripts were removed because they were unrelated to the machine-design-platform proposal.

## Run the repository checks

```bash
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh sbom --output /tmp/cad_agent_sbom.json
bash ./run_cad_agent.sh provenance --output /tmp/cad_agent_provenance.json
bash ./run_cad_agent.sh status
```

The runner exposes platform documentation checks plus the Phase 1 PoC/native CadQuery hardening commands, the Phase 2 pilot command, `serve --dry-run`, and deterministic SBOM/provenance stubs. The Phase 1 pipeline validates Requirement JSON, Specification JSON, Parametric DSL AST, z-only feature axes, parameter references, `step_ap242`, STEP/STL export failure handling, Validation Report creation, artifact hash indexing, and human approval records. The Phase 2 pilot exercises FreeCAD/OCCT and Blender adapter probes, DFM/AM profile checks, review diff HTML generation, audit retention metadata, data classification, and Model Gateway route decisions. Current PoC/Pilot maturity: production worker deployment is not promised; the Phase 1 path records native CadQuery when available and otherwise keeps the deterministic surrogate boundary explicit. Production v1/v2 additions are decoupled skeletons: stdlib API server, in-memory project/job services, security/observability tests, CI/SBOM/provenance commands, and static material/BOM/AABB assembly stubs.

## Repository layout

```text
docs/Origen/   Original proposal supplied by the user
docs/          Maintained platform documentation
scripts/       Deterministic validation scripts for the platform docs
cad_agent/platform_poc.py  Phase 1 single-part platform PoC runtime and gates
cad_agent/phase2_pilot.py  Phase 2 pilot adapters, DFM/AM catalog, review diff, audit, and gateway checks
cad_agent/api_server.py     Production v1 API skeleton using stdlib http.server
cad_agent/project_service.py In-memory project service skeleton
cad_agent/job_queue.py      Synchronous job queue simulation
cad_agent/observability.py  In-process Prometheus-text counters
cad_agent/material_catalog.py Production v2 static material catalog stub
cad_agent/bom.py            Decoupled BOM aggregation stub
cad_agent/assembly_checks.py Axis-aligned bbox assembly interference stub
schemas/phase1/  JSON Schema contracts for Phase 1 I/O boundaries
tests/         Unit tests for schema, AST, runtime, validation, artifact, and approval gates
run_cad_agent.sh  Bash entrypoint for local checks
```

## License

Apache-2.0. See [`LICENSE`](LICENSE).
