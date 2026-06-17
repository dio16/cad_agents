# Tasks

## Phase 0: Repository alignment

- [x] 原案を正本として明示する。
- [x] 旧個別成果物のドキュメントを削除する。
- [x] 旧成果物生成・検証スクリプトを削除する。
- [x] 文書整合性チェック用スクリプトを追加する。

## Phase 1: PoC（6〜10週）

目的: 単一部品で、要件抽出から CAD 生成、検証、artifact 保存までの最小パイプラインを成立させる。

| ID | タスク | 完了条件 |
|---|---|---|
| P1-1 | Requirement JSON Schema | ✅ `cad_agent.platform_poc` の contract test で required fields と unknowns/assumptions 分離を確認 |
| P1-2 | Specification JSON Schema | ✅ `parameter_table`、`constraints`、`validation_plan` を contract test で確認 |
| P1-3 | Parametric DSL Schema | ✅ `units=mm`、parameter 参照整合、feature order を AST validator で確認 |
| P1-4 | CAD Runtime MVP | ✅ allowlist DSL から STEP AP242 surrogate と STL を生成し、AST/volume 失敗理由を返す |
| P1-5 | Validation MVP | ✅ bbox、volume、topology proxy、unit consistency、DFM/AM 最小ルールを Validation Report に保存 |
| P1-6 | Artifact Store MVP | ✅ `traceability_id` と `artifact_hash` を `artifact_index.jsonl` に保存 |
| P1-7 | Human Approval Gate | ✅ 仕様変更/validation override の承認記録を JSONL に保存 |

## Phase 2: Pilot（10〜16週）

目的: Phase 1 の単一部品パイプラインを維持したまま、実 worker 接続点、製造プロファイル、レビュー、監査、モデルルーティングを Pilot 用に通す。

| ID | タスク | 完了条件 |
|---|---|---|
| P2-1 | FreeCAD headless / OCCT worker probe | ✅ `phase2-pilot-run` で executable を検出した場合のみ native mode を記録し、未導入環境では deterministic surrogate adapter を記録 |
| P2-2 | Blender render / mesh worker probe | ✅ `phase2-pilot-run` で Blender adapter を probe し、native executable 不在時は OBJ surrogate mesh を生成 |
| P2-3 | DFM/AM プロファイルカタログ | ✅ `fdm_standard` / `cnc_3axis_soft_metal` の profile catalog を保持し、Pilot golden path では `fdm_standard` の仕様の壁厚・穴径・材料・`dfm.build_volume.max`（`max_bbox_mm` に対する保守的 axis-aligned bbox 比較）を検証 |
| P2-4 | Review UI、diff viewer、版比較 | ✅ Phase 1 baseline と revised spec の parameter diff を HTML review viewer に保存 |
| P2-5 | 監査ログ、保持期間、データ分類 | ✅ `audit_log.jsonl` に `data_classification`、`retention_days`、`model_route` を保存 |
| P2-6 | commercial / onprem / hybrid の Model Gateway 試験 | ✅ public commercial は許可、confidential commercial は onprem fallback として fail 判定 |

## Phase 3: Production v1 readiness skeleton

- [x] API Gateway / Project Service skeleton: stdlib HTTP server, in-memory project CRUD, API-key stub, artifact index lookup only.
- [x] Synchronous job queue simulation: `cad_golden`, `phase2_pilot`, and `validation` stub jobs with deterministic tests.
- [x] Security and observability skeleton: prompt/schema/code escape tests, Prometheus-text counters, `serve --dry-run`.
- [x] CI/SBOM/provenance skeleton: GitHub Actions smoke workflow, local deterministic SBOM/provenance commands.
- Deferred: Kubernetes, KServe/vLLM, Argo CD, Cosign/Trivy, real worker pools, real LLM endpoints, and production SLO enforcement.

## Phase 4: Production v2 data-model stubs

- [x] Static material catalog stub for `PLA`, `PETG`, `ABS`, `6061-T6`, `POM`, `17-4PH` with explicit `skeleton_stub` / reference-only metadata.
- [x] Decoupled BOM aggregation stub with validation errors, weight stub, and cost stub.
- [x] Axis-aligned bbox assembly interference/separation/adjacency stub; contact, motion, and FEA remain future work.
- Deferred: real material database, parts library, PLM/ERP/MES adapters, tenant isolation, regulatory workflow, and production-grade assembly/FEA validation.
