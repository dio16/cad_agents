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
| P2-1 | FreeCAD headless / OCCT worker 統合 | ✅ `phase2-pilot-run` で native executable を検出、未導入環境では deterministic surrogate adapter を記録 |
| P2-2 | Blender render / mesh worker 統合 | ✅ `phase2-pilot-run` で Blender adapter を probe し、OBJ surrogate mesh を生成 |
| P2-3 | DFM/AM プロファイルカタログ | ✅ `fdm_standard` / `cnc_3axis_soft_metal` の profile catalog で仕様の壁厚・穴径・材料を検証 |
| P2-4 | Review UI、diff viewer、版比較 | ✅ Phase 1 baseline と revised spec の parameter diff を HTML review viewer に保存 |
| P2-5 | 監査ログ、保持期間、データ分類 | ✅ `audit_log.jsonl` に `data_classification`、`retention_days`、`model_route` を保存 |
| P2-6 | commercial / onprem / hybrid の Model Gateway 試験 | ✅ public commercial は許可、confidential commercial は onprem fallback として fail 判定 |

## Phase 3: Production v1（4〜6か月）

- Kubernetes job queue と CAD/FEA worker pool
- KServe / vLLM を使ったオンプレモデルルート
- GitHub Actions + Argo CD による CI/CD
- SLSA provenance、Cosign 署名、SBOM / Trivy scan
- Prompt Injection、schema escape、code escape の security tests
- SLO、コスト監視、queue p95 監視

## Phase 4: Production v2（6か月以降）

- 組立干渉、接触、運動、FEA の高度化
- PLM / ERP / MES adapter
- 材料DB、部品ライブラリ、BOM連携
- 部門横断のテナント分離と規制案件運用
