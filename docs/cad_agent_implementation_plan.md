# CADAGENT Implementation Plan

## 1. Document status

- Status: maintained; all phases completed (2026-07-12)
- Source: `docs/Origen/cad_agent_design_spec_and_implementation_plan.md`
- Related: `docs/cad_agent_detailed_design.md`, `docs/backlog/IMPLEMENTATION_HISTORY.md`
- Final validation: `uv run pytest -q` → 288 passed, 2 subtests; `validate-docs` pass

## 2. Current maturity

| Area | State |
|---|---|
| Phase 1 PoC/native CadQuery | Implemented and hardened |
| Phase 2 DFM/AM Pilot | Implemented |
| E2E Job Runner | Implemented (fixture/structured/llm modes) |
| Local Job Store | Implemented (sqlite3 durable) |
| Export gate | Implemented (EXPORT_REQUIRES_NATIVE_KERNEL) |
| LLM agents | Implemented (mock default, CAD_AGENT_LLM_LIVE=1 for live) |
| API server | Skeleton (stdlib HTTP, local only) |
| Material/BOM/AABB | Stubs only |
| Production deployment | **Deferred** (K8s, Cosign, real workers, FEA, auth) |

## 3. Phase matrix

All phases CAD-P00–P09, CAD-FG-00–FG-22, CAD-REVIEW-01/02, gear_train_v2, PWF completed.

| Phase | Summary | Status |
|---|---|---|
| CAD-P00 | Design-contract finalization | completed |
| CAD-P01 | PoC single-part pipeline | completed |
| CAD-P02 | Pilot (probes, DFM/AM, review, audit, gateway) | completed |
| CAD-P03 | Production v1 skeleton (API, jobs, security, CI) | completed |
| CAD-P04 | Local API workflow v1 | completed |
| CAD-P05 | Assembly DSL + AABB validation | completed |
| CAD-P06 | Mechanism DSL compiler | completed |
| CAD-P07 | LLM agents (fixture, retry, routing, audit) | completed |
| CAD-P08 | Motion validation (bounded clearance) | completed |
| CAD-P09 | First target object E2E | completed |
| CAD-FG-00–22 | Functional gaps (honesty, runner, store, export, LLM) | completed |
| CAD-REVIEW-01/02 | Repository review catch-ups | completed |

Detailed per-phase records: `docs/backlog/IMPLEMENTATION_HISTORY.md`

## 4. Deferred scope

- Production deployment (Kubernetes, Cosign, Trivy)
- Real native worker pools (OCCT/FreeCAD/CadQuery)
- Production-grade material DB, PLM/ERP/MES adapters
- FEA solver integration
- Production dynamic motion simulation
- Durable production artifact storage
- Production SLO enforcement, regulatory/export-control
- New DSL operations beyond current allowlist

## 5. Validation commands

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh run-job
bash ./run_cad_agent.sh serve --dry-run
uv run pytest -q
git diff --check
```

## 6. Stop conditions

Stop and submit review package if:
- Validation fails
- Review not approved
- Must-fix items remain open
- Phase attempts forbidden work (production, FEA, raw code, new DSL ops)
- Stale validation term in maintained docs

## 7. Risk register

| Risk | Mitigation |
|---|---|
| Completed stubs mistaken for production | Explicit maturity labels, deferred scope list |
| Validation over-claims capability | Topology/DFM honesty enforced (null, parameter_proxy) |
| LLM data leakage | route_model enforced, sensitive → onprem only, mock default |
| Stale terms in docs | `validate-docs` scan on every commit |

## 8. Decision log (key)

| ID | Decision |
|---|---|
| CAD-D001 | Create `docs/cad_agent_detailed_design.md` |
| CAD-D002 | Create `docs/cad_agent_implementation_plan.md` |
| CAD-D012 | CAD-P03 (approval/revision/export gates) = highest-value next phase |
| CAD-REVIEW-02 | FG-18–22 catch-up (honesty, E2E, store, export gate, LLM) |

## 9. Reference

- Active tasks: `TASKS.md`
- Completed history: `docs/backlog/IMPLEMENTATION_HISTORY.md`
- Detailed design: `docs/cad_agent_detailed_design.md`
- Catch-up design: `docs/cad_agent_catchup_detailed_design.md`
