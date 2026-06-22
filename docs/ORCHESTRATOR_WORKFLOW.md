# Orchestrator Workflow

## Status

Local/in-process workflow safety gate is implemented and validated as a bounded PoC/Pilot skeleton. Production API service, native worker pool, production auth, production artifact storage, and durable audit deployment remain future scope.

## Purpose
Define the workflow state machine, revision loop, escalation rules, human approval events, and audit obligations for the first CADAGENT implementation pass.

## Source traceability
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:477-526`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:595-625`
- `docs/Origen/cad_agent_design_spec_and_implementation_plan.md:693-890`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:121-190`
- `docs/Origen/Design_document_for_a_machine_design_platform.md:612-628`

## In scope
- State machine:
  ```text
  created
    → requirement_extracted
    → spec_drafted
    → pending_spec_approval
    → spec_approved
    → mechanism_planned
    → dsl_generated
    → cad_built
    → validation_running
    → validation_failed
    → validation_passed
    → pending_export_approval
    → exported
  ```
- Failure loop:
  ```text
  validation_failed
    → revision_requested
    → dsl_revised
    → cad_built
    → validation_running
  ```
- Maximum automatic revision loop count: 3.
- Escalation conditions: specification contradiction, three or more validation failures, sensitive data, regulated/export-controlled tags, new DSL operation, or required spec change.
- Human approval events: spec freeze, manufacturing profile change, material change, drive method change, validation override, new DSL operation, print export, regulated/export-controlled/safety-critical tag.
- Audit obligations: append-style JSONL records for inputs, outputs, validation results, approvals, model route, traceability IDs, and artifact hashes.
- API references are future contracts only; no endpoint schema files are created by this pass.

## Out of scope / deferred
- Production API service, native worker pool, real LLM endpoint, multi-tenant authorization, and immutable production audit storage.
- Direct specification changes by agents.
- Validation bypass or failed-to-pass rewrites.
- Production job queue, event bus, and deployment orchestration.

## Contract summary
The Orchestrator controls workflow state, gates, revision loops, and escalation. It never changes specifications on its own and never bypasses Validation. LLM agents may propose corrections or change requests, but human/reviewer approval is required for spec changes, validation overrides, regulated/export-controlled tags, new DSL operations, and print export.

## Acceptance criteria
- Workflow states and failure loop are documented and deterministic.
- `max_revision_loops` is 3.
- Escalation to `needs_human_review` occurs after three failed automatic revisions or any escalation condition.
- Human approval events are explicit and auditable.
- Traceability IDs and artifact hashes are preserved across Requirement JSON, Specification JSON, Parametric DSL, Validation Report, and artifacts.
- API endpoint references remain future contracts only.

## Open decisions / deferred decisions
- Production job queue, persistence, authorization, and observability are future scope.
- Exact approval UI/API contracts are future work.
- Long-term immutable audit storage and retention enforcement are future scope.
- Production model routing policy is governed by Policy/Audit and Model Gateway contracts.
