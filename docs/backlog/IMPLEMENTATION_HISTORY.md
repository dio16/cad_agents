# Implementation History — Completed Task Backlog

> **目的**: `TASKS.md` のコンテキスト削減のため、完了済みタスクの詳細記録を本ファイルへ移管。
> **正本タスク在庫**: `TASKS.md`（現在のアクティブ/保留タスクのみ）
> **最終更新**: 2026-07-12

---

## CAD-REVIEW-02 (2026-07-12 catch-up)

| Task | Summary | Key files | Tests |
|---|---|---|---|
| CAD-FG-18 | Validation honesty: topology null, DFM parameter_proxy, doc reconcile | `platform_poc.py`, schema, README, SPEC | 247 pass |
| CAD-FG-19 | E2E job runner (fixture/structured/llm modes) | `job_runner.py`, `cli.py` | 258 pass |
| CAD-FG-20 | Local durable job store (sqlite3) | `job_store.py`, `job_runner.py` | 272 pass |
| CAD-FG-21 | Native export gate (EXPORT_REQUIRES_NATIVE_KERNEL) | `orchestrator.py` | 276 pass |
| CAD-FG-22 | Real LLM loop (mock + live opt-in, routing enforced) | `llm_adapter.py`, agents, `job_runner.py` | 288 pass |

Plan: `docs/cadagent_plans/CAD-REVIEW-02/implementation-plan.md`
Design: `docs/cad_agent_catchup_detailed_design.md`
Review: `docs/repository_review_2026-07-12_ja.md`

---

## CAD-P00–P09 (Core platform phases)

All 10 phases implemented and validated (skeleton/Pilot maturity). Plans at `docs/cadagent_plans/CAD-P*/implementation-plan.md`.

| Phase | Summary |
|---|---|
| P00 | Design-contract finalization: MVP_SCOPE, DSL, Runtime, Validation, Orchestrator contracts |
| P01 | PoC: single-part pipeline (Requirement→Spec→DSL→CAD→Validation→Store) |
| P02 | Pilot: FreeCAD/OCCT/Blender probes, DFM/AM catalog, review diff, audit, gateway |
| P03 | Production v1 skeleton: API server, project service, job queue, security, CI/SBOM |
| P04 | Local API workflow v1: run/revision/export endpoints |
| P05 | Assembly DSL + AABB validation (interference, adjacency, workflow gate) |
| P06 | Mechanism DSL compiler (allowlist, op approval, Phase 1 integration) |
| P07 | LLM agents (fixture/mock routes, schema retry, model routing, audit) |
| P08 | Motion validation (bounded clearance, workflow gate) |
| P09 | First target object (gyro_kinetic_v1) end-to-end integration |

---

## CAD-FG-00–FG-17 (Functional gaps)

| Task | Summary | Plan |
|---|---|---|
| FG-00 | Maintained-doc status drift reconciliation | `cadagent_plans/CAD-FG-00/` |
| FG-01 | Active workflow safety gate: store_artifacts checks validation pass | `cadagent_plans/CAD-FG-01/` |
| FG-02 | Validation report & artifact metadata hardening | `cadagent_plans/CAD-FG-02/` |
| FG-03 | Model Gateway & data-classification API integration | `cadagent_plans/CAD-FG-03/` |
| FG-04 | Agent route hardening (fixture boundary, schema retry, audit, routing) | `cadagent_plans/CAD-FG-04/` |
| FG-05 | Production infrastructure deferral (docs accurately reflect deferred state) | `cadagent_plans/CAD-FG-05/` |
| FG-06 | Orchestrator state machine dedup audit timestamp | `cadagent_plans/CAD-FG-06/` |
| FG-07 | validate_artifacts() decomposition (5 sub-validators) | `cadagent_plans/CAD-FG-07/` |
| FG-08 | DSL compiler cleanup (dead parameter_name removal) | `cadagent_plans/CAD-FG-08/` |
| FG-09 | Security hardening (API key env, CORS) | `cadagent_plans/CAD-FG-09/` |
| FG-10 | Surrogate STL normals fix | `cadagent_plans/CAD-FG-10/` |
| FG-11 | Error handling expansion (BOOLEAN_FAILED, KERNEL_TIMEOUT) | `cadagent_plans/CAD-FG-11/` |
| FG-12 | Test quality improvement (public API tests, combined assembly+motion) | `cadagent_plans/CAD-FG-12/` |
| FG-13 | Documentation alignment (architecture diagram, API key/CORS docs) | `cadagent_plans/CAD-FG-13/` |
| FG-14 | HTML assembly viewer + 7-stage workflow embedding | `cadagent_plans/CAD-FG-14/` |
| FG-15 | Detailed-design/implementation gap inventory | `cadagent_plans/CAD-FG-15/` |
| FG-17 | Mechanism DSL tourbillon operations (gear, escape_wheel, etc.) | `cadagent_plans/CAD-FG-17/` |

---

## gear_train_v2

Changed-dimension test case: `examples/gear_train_v2/`. Radii 10/25/12/48, teeth 10/25/12/48, thickness 12/12/8/8. Viewer + STL fidelity test in `tests/test_gear_train_v2.py`.

---

## PWF (Prompt Workflow Framework)

PWF-G001, PWF-P00–P05 completed. `prompt.md`, `docs/prompt_execution_plan.md`, TASKS integration, operations docs. Deepwork: `.slim/deepwork/prompt_workflow_framework.md` (closed).
