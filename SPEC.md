# Platform Specification

## 1. システム原則

本仕様は、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` を実装単位へ分解したものです。

- LLM は設計計画器であり、CAD 実行器ではない。
- CAD Runtime は OCCT / FreeCAD 互換の決定論的実行器である。
- Validation は品質ゲートであり、合否と理由を機械可読に返す。
- 自由文と CAD 実行の間には、必ず JSON Schema と Parametric DSL の境界を置く。
- STEP AP242 / B-Rep を正本形状とし、STL / OBJ / glTF / PNG / PDF は派生物として扱う。

## 2. 現在の実装成熟度

- 実装済み: ローカル CLI、Phase 1 PoC contract/golden pipeline、Phase 2 Pilot adapter probe、DFM/AM catalog、review diff HTML、audit JSONL、Model Gateway trial。
- 未実装: API Gateway/Auth、Project Service、非同期ジョブキュー、sandbox CAD worker pool、Observability、Production v1/v2 の PLM/ERP/MES adapter。
- 本リポジトリの現在の成功基準は、設計案全体を本番運用することではなく、原案に基づく安全な I/O 境界・検証ゲート・PoC/Pilot パイプラインを再現可能に保つことです。

## 3. 正本データ階層

| レイヤ | 正本 | 目的 |
|---|---|---|
| 要件 | Requirement JSON | 自然文の曖昧さを工学項目へ分解する |
| 仕様 | Specification JSON | 寸法、拘束、材料、工程、検証条件を確定する |
| 生成命令 | Parametric DSL / Operation Graph | LLM 出力を安全に実行可能化する |
| 形状 | STEP AP242 / B-Rep | 組立、交換、再利用の正本にする |
| 派生物 | STL / OBJ / glTF / PNG / PDF | 造形、表示、共有、図面化に使う |
| 検証 | Validation Report JSON | 幾何、工程、FEA の判定と差分を記録する |

## 4. エージェント責任境界

| エージェント | 責務 | 禁止事項 |
|---|---|---|
| Requirement Extractor | 自然文を Requirement JSON に変換する | 未知事項を推測で埋める |
| Spec Composer | Requirement を Specification JSON に変換する | 製造条件や公差を独断で確定する |
| DSL Compiler | Specification を Parametric DSL に変換する | 自由コード生成、未検証 DSL 実行要求 |
| CAD Runtime | DSL を実行し STEP/B-Rep を生成する | 仕様解釈の変更、失敗の隠蔽 |
| Validation | 幾何、DFM/AM、FEA を判定する | 不合格の合格書き換え |
| Orchestrator | ゲートと修正ループを制御する | 検証バイパス、承認省略 |
| Policy / Audit | ルーティング、ログ、法規タグを管理する | 監査ログ改ざん、保持期間違反 |
| Model Gateway | commercial / onprem / hybrid を切り替える | 機密情報の不適切ルーティング |

## 5. 必須スキーマ要点

### Requirement JSON

必須キー: `traceability_id`, `product_type`, `functional_requirements`, `dimensions`, `manufacturing`, `unknowns`, `assumptions`。

### Specification JSON

必須キー: `traceability_id`, `requirement_id`, `parameter_table`, `constraints`, `material_candidates`, `manufacturing_profile`, `validation_plan`, `unresolved_risks`。

### Parametric DSL

必須キー: `traceability_id`, `units`, `parameters`, `features`, `derivative_outputs`。`units` は `mm` 固定で、`features` は実行可能順序でなければならない。

### Validation Report JSON

必須キー: `traceability_id`, `specification_id`, `artifact_ids`, `dimensions_check`, `topology_check`, `unit_consistency`, `manufacturing_profile_rules`, `pass`, `failures`。

## 6. API境界

- `POST /v1/projects`
- `POST /v1/requirements/extract`
- `POST /v1/specifications/generate`
- `POST /v1/cad/jobs`
- `GET /v1/cad/jobs/{job_id}`
- `POST /v1/validation/jobs`
- `POST /v1/revisions`
- `POST /v1/exports`
- `GET /v1/artifacts/{artifact_id}`

## 7. ゲート

| ゲート | 通過条件 | バイパス |
|---|---|---|
| Schema Gate | JSON Schema pass | 不可 |
| AST Gate | Parametric DSL が AST validator pass | 不可 |
| Validation Gate | 全 check pass | Reviewer 承認時のみ条件付き許容 |
| Compliance Gate | データ分類、法規、輸出タグ確定 | 不可 |
| Human Approval Gate | 仕様変更、regulated/export-controlled、新規 DSL operation の承認記録 | 不可 |
