# 運用・CI/CD設計

## ローカルコマンド

このリポジトリの maintained script は文書・契約整合性チェック、Phase 1 PoC の最小パイプライン検証、Phase 2 Pilot の adapter / review / audit / gateway 検証を提供します。

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh sbom --output /tmp/cad_agent_sbom.json
bash ./run_cad_agent.sh provenance --output /tmp/cad_agent_provenance.json
```

## Prompt-driven workflow

`prompt.md`、`docs/prompt_execution_plan.md`、`docs/cad_agent_detailed_design.md`、`docs/cad_agent_implementation_plan.md`、およびPhase 0設計契約文書（`docs/MVP_SCOPE.md`、`docs/MECHANISM_DSL_V1.md`、`docs/CAD_RUNTIME_CONTRACT.md`、`docs/VALIDATION_CONTRACT.md`、`docs/ORCHESTRATOR_WORKFLOW.md`）は、原案ベースのCADAGENT設計・実装計画をフェーズ単位で実行するための運用エントリポイントです。

- `prompt.md`: 進め方の指示、Gate、許可コマンド、禁止事項、traceability rules を定義します。
- `docs/cad_agent_detailed_design.md`: CADAGENTの詳細設計を定義します。
- `docs/cad_agent_implementation_plan.md`: CADAGENTの実装計画、Gate、Validation、Stop conditionsを定義します。
- `docs/prompt_execution_plan.md`: 修正後ゴール、現在の成熟度、Phase map、Acceptance criteria、Validation commands、Review package template を定義します。
- 最初の適用範囲は docs-only workflow です。実装は文書中心とし、`validate-docs`を維持するためのvalidation-harness更新以外は新規実行機能・CAD feature・Production API service・native worker pool・外部LLM endpoint を追加しません。
- Phase 0 design-contract finalization passでは、CADAGENT実装契約文書（`MVP_SCOPE.md`、`MECHANISM_DSL_V1.md`、`CAD_RUNTIME_CONTRACT.md`、`VALIDATION_CONTRACT.md`、`ORCHESTRATOR_WORKFLOW.md`）を契約文書として作成します。それ以外の pass では、実装コード・`schemas/v1/*`・API endpoint schema・native worker pool は作成しません。

## CI/CD skeleton

現在の CI は Production v1/v2 の完全運用ではなく、GitHub Actions 上で既存の文書・契約・Phase 1/2・SBOM/provenance・serve dry-run を通す smoke workflow です。

```mermaid
flowchart TD
    A[Git Push / PR] --> B[GitHub Actions]
    B --> C[uv sync --locked --extra dev]
    C --> D[pytest -q]
    D --> E[validate-docs]
    E --> F[phase1-contract-test]
    F --> G[phase1-golden-pipeline]
    G --> H[phase2-pilot-run]
    H --> I[sbom / provenance stubs]
    I --> J[serve --dry-run]
```

## 実行基盤 skeleton

- 現リポジトリは Production v1/v2 実行基盤の skeleton/contract を示す。
- API server は stdlib `http.server` の local stub。
- job queue は synchronous simulation。
- CI は GitHub Actions smoke workflow。
- SBOM/provenance は決定論的 local stub。
- Production 実運用: Kubernetes、KServe/vLLM、Argo CD、Cosign/Trivy、sandbox worker pool は将来拡張。

## SLO候補

| 指標 | 初期目標 |
|---|---|
| Requirement JSON schema pass rate | 99%以上 |
| 単一部品の初回 CAD compile success rate | 80%以上 |
| Specification から STEP 生成成功率 | 95%以上 |
| Geometry validation pass rate | 98%以上 |
| Audit log 欠損率 | 0% |
| Queue p95 待ち時間 | Pilot で計測し Production v1 で固定 |

## ゴールデンケース

PoC の regression には、ブラケット、カバー、スペーサ、治具、パイプクランプ、簡易組立を使います。各ケースは Requirement / Specification / DSL / STEP / Validation Report を generation identity で束ねます。

## Phase 2 Pilot コマンド

`bash ./run_cad_agent.sh phase2-pilot-run` は、FreeCAD/OCCT と Blender が導入済みなら native executable を記録し、未導入なら deterministic surrogate adapter として結果を残します。加えて DFM/AM profile catalog、HTML review viewer、version diff、`audit_log.jsonl` の保持期間・データ分類、Model Gateway の public / confidential ルーティング試験を 1 つの report にまとめます。
