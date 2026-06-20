# AI機械設計プラットフォーム エージェント運用規則

## 1. 目的

本ファイルは、`docs/Origen/Design_document_for_a_machine_design_platform.md` を原案とする機械設計プラットフォームに関与するAIエージェントの役割、責任範囲、連携方法を定義する。  
設計判断はエージェントが担い、実行・測定・構成・検証は決定論的CADカーネルと検証器が担う。  
この分離により、曖昧さの解消と真偽判定を明確にする。

## 2. プラットフォーム原則

- **LLMは設計計画器、CADカーネルは実行器、検証器は品質ゲート**
- **自由文を直接CADコードに流さない。構造化JSON/DSLをI/O境界に置く**
- **仕様変更は人間の承認を経由する。エージェントが単独で仕様を変更しない**
- **全生成物にtraceability IDを付与し、監査可能にする**

## 3. エージェント種別と役割

### 3.1 設計・仕様エージェント

| エージェント | 責務 | 連携先 | 禁止事項 |
|---|---|---|---|
| Requirement Extractor | 自然文→Requirement JSON | Spec Composer, Project Service | 仕様の無断変更、未知事項の推測による埋め合わせ |
| Spec Composer | Requirement→Specification JSON | DSL Compiler, Validation | 製造条件の独断、公差の勝手な設定 |
| DSL Compiler | Spec→Parametric DSL | CAD Runtime, Validation | 自由コード生成、スキーマ未検証DSLの実行要求 |

### 3.2 実行・検証エージェント

| エージェント | 責務 | 連携先 | 禁止事項 |
|---|---|---|---|
| CAD Runtime | DSL実行、形状生成 | Validation, Export | 仕様の解釈変更、実行失敗の隠蔽 |
| Validation | 幾何妥当、DFM/AM、将来拡張としてのFEA候補 | Orchestrator, Audit | 不合格の合格書き換え、検証条件の省略 |
| Export Worker | STEP/STL/OBJ/PDF生成 | Artifact Store | 正本formatsの破壊的変換 |

### 3.3 統制・承認エージェント

| エージェント | 責務 | 連携先 | 禁止事項 |
|---|---|---|---|
| Orchestrator | ワークフロー制御、修正ループ管理 | 全エージェント | 検証バイパス、ゲート省略 |
| Policy / Audit | ルーティング、ログ、法規タグ | Project Service, Gateway | 許可なしの監査ログ変更、保持期間違反 |
| Model Gateway | 商用/オンプレLLMルーティング | Requirement, Spec, DSL | 機密情報の不適切なルーティング |

### 3.4 人間の役割

人間は以下を最終的に担う。
- 設計意図の最終解釈と承認
- 仕様の変更決定
- 機微案件の法規・安全保障判断
- 検証結果の最終確認と長期運用方針

## 4. 責任境界

### 4.1 分離原則

```
[人間の責任領域]
設計意図の最終解釈
仕様変更の決定
機微案件の判断
最終承認

[エージェント責任領域]
要件の構造化
仕様のドラフト作成
DSLの生成と修正案提示
検証の自動実行
トレーサビリティ記録

[決定論的システム責任領域]
CAD形状の生成
幾何・DFM/AM検証
artifactの保存
append-style JSONLログ記録（将来の不変ストレージを目標）
```

### 4.2 エスカレーション条件

以下は人間の判断に委ねる。
- 仕様の矛盾解消（エージェントは矛盾を検出して報告するのみ）
- 3回以上の検証失敗
- 機微データの検出
- 法規タグ regulated / export-controlled の付与
- 新規DSL operationの追加

## 5. I/Oスキーマ厳守ルール

### 5.1 入力基準

| 入力種別 | 形式 | 検証 |
|---|---|---|
| 人間入力 | 自由文 + 既知条件 | エージェントが構造化 |
| エージェント間I/O | JSON Schema準拠 | スキーマvalidator通過が条件 |
| CAD実行入力 | Parametric DSL | AST validator通過が条件 |
| 検証入力 | Spec + Artifact | traceability照合 |

### 5.2 出力基準

| 出力種別 | 必須要素 |
|---|---|
| Requirement JSON | product_type, functional_requirements, dimensions, unknowns, assumptions |
| Specification JSON | parameter_table, constraints, material_candidates, manufacturing_profile, validation_plan |
| Parametric DSL | units=mm, parameters参照整合, features実行可能順序, derivative_outputs |
| Validation Report | dimensions_check, topology_check, unit_consistency, manufacturing_profile_rules, pass/fail |

## 6. 禁止事項と安全装置

### 6.1 絶対禁止

- 自由文を直接CADコードにすること
- 仕様の無断変更
- 任意コードの直接実行（allow_raw_code=true時でも監査ログ必須）
- 検証不合格の合格書き換え
- トレーサビリティIDの省略または改ざん
- 機密データを商用APIルートに送信すること

### 6.2 安全装置

- JSON Schema Contract Test：全LLM工程の入出力を自動検証
- AST/schema validator：DSL実行前に静的検証
- サンドボックス実行：CADランタイムはネットワーク分離環境で実行することを目標とし、現行PoC/PilotはローカルCLIとdeterministic surrogateで検証する
- 監査ログ：全I/Oと判断をappend-style JSONLに記録し、不変ストレージ化は将来目標
- 人間確認ゲート：仕様変更、機微案件、新規validation criteria適用時に必須

## 7. 作業フローとゲート

### 7.1 標準フロー

```
[人間] 設計意図入力
    ↓
[Requirement Extractor] 要件JSON生成
    ↓
[Spec Composer] 仕様JSON生成
    ↓
[人間またはReviewer] 仕様承認（critical jobsは必須）
    ↓
[DSL Compiler] Parametric DSL生成
    ↓
[AST Validator] スキーマ/整合性検証
    ↓
[CAD Runtime] 形状生成 → STEP/B-Rep
    ↓
[Validation] 幾何/DFM/AM（FEAは将来拡張候補）
    ↓
  合格 → 次の工程へ
  不合格 → failure reasonを添えてOrchestratorへ
    ↓
[Orchestrator] 修正ループ（max_revision_loops以内）
    ↓
[人間またはReviewer] 生成物承認
    ↓
[Export Worker] 成果物パッケージ
    ↓
[Artifact Store] 版管理付き保存
```

### 7.2 ゲート基準

| ゲート | 通過条件 | バイパス |
|---|---|---|
| Schema Gate | JSON Schema pass | 不可 |
| Validation Gate | 全check pass | Reviewer承認時のみ条件付き許容 |
| Compliance Gate | 法規/機密/輸出タグ確定 | 不可 |
| Human Approval Gate | 人手レビュー実施記録 | regulated/export-controlled案件は必須 |

### 7.3 実装前ステータス照合ゲート

実装・再実装・修正ループに入る前に、Orchestratorは以下の状態を照合する。

- `TASKS.md` の `active` / `closed` / `pending` 状態
- `docs/cad_agent_implementation_plan.md` の phase matrix と各 phase の詳細状態
- 関連する `docs/ORCHESTRATOR_WORKFLOW.md`、`operations_ja.md`、plan/checkpoint の最終検証結果
- 既存の git status / git log で、直近の完了・検証済み作業を確認

照合結果の扱い:

- 完了済み項目が `Not started` / `Skeleton` / `Stub` などとして残っている場合、それを新規実装対象ではなく status drift として報告する
- `status: closed` または最終検証 `pass` / `conditional pass` の計画は、ユーザーが明示的に「再開」「継続」「再実装」と指示しない限り再検証・再実装しない
- 状態が矛盾・不明な場合は、実装前にユーザーへ確認する
- 照合結果は要約で残し、必要に応じて「新規実装」か「最終状態の reconcile/summary」かを分岐する

## 8. 使用コマンドとインターフェース

### 8.1 基本操作

- 要件抽出：`POST /v1/requirements/extract`
- 仕様生成：`POST /v1/specifications/generate`
- CADジョブ起動：`POST /v1/cad/jobs`
- ジョブ状態：`GET /v1/cad/jobs/{job_id}`
- 再検証：`POST /v1/validation/jobs`
- 再生成：`POST /v1/revisions`
- 成果物出力：`POST /v1/exports`
- 成果物取得：`GET /v1/artifacts/{artifact_id}`

### 8.2 内部コマンド

- スキーマ検証：`bash ./run_cad_agent.sh phase1-contract-test`
- CAD実行：`bash ./run_cad_agent.sh phase1-golden-pipeline`（または同等のCAD runtime entrypoint）
- パイロット検証：`bash ./run_cad_agent.sh phase2-pilot-run`
- レポート生成：`bash ./run_cad_agent.sh phase2-pilot-run` による validation report, DFM/AM profile report, review diff HTML

## 9. エージェント品質要件

### 9.1 プロンプト設計原則

- 役割分離：要件抽出、仕様生成、DSL生成、検証、修正を別プロンプトに分割
- 構造化出力：全段階をJSON Schemaで固定
- 単位固定：mm / deg / N / MPa
- 不明点の明示：unknownsとassumptionsを分離
- 実行権限制限：default allow_raw_code=false
- 再試行設計：Validation Reportを入力にした修正ループを実装

### 9.2 評価指標

| 指標 | 目標 |
|---|---|
| 構造化要件JSONの妥当率 | 99%以上 |
| 単一部品の初回CADコンパイル成功率 | 80%以上 |
| 仕様→STEP生成成功率 | 95%以上 |
| 幾何妥当性チェック通過率 | 98%以上 |
| 監査ログ欠損率 | 0% |

## 10. 現場で迷わないための最小ルールセット

1. **仕様を変えたくなったら、エージェントは変更案を出すだけで実行しない**
2. **検証が不合格になったら、必ず理由を明記してから修正する**
3. **機密/regulated/export-controlled案件はオンプレルートへ**
4. **実装前にステータス照合ゲートを通す。完了済み項目の再実装は明示指示がない限り禁止**
5. **ユーザー向け返答は日本語。内部推論・調査メモ・専門用語は英語可。コンテキスト圧縮後もこの返答言語を維持する**

## 11. `.slim/deepwork/` 計画ファイルの lifecycle

- `.slim/deepwork/` は作業中の session state であり、未処理 backlog ではない。
- 計画ファイルを使う前に、該当ファイルを `active` / `closed` / `archived` のいずれかに分類する。
- `status: closed` または明確な最終レビュー `pass` / `conditional pass` と最終検証結果がある計画は、ユーザーが明示的に「再開」「継続」「再実装」と指示しない限り再検証・再実装しない。
- 完了済み計画が残っている場合は、作業対象として扱う前に「既存計画は完了済み。新規実装ではなく最終状態の reconcile/summary でよい」と確認する。
- 新規 Deepwork は、進行中の `status: active` の計画を優先する。該当する active 計画がない場合は、新しい plan file を作成し、冒頭に `status: active` を明記する。
- 計画を閉じる際は、同じ deepwork file に `status: closed`、`closed_at`、最終検証コマンド、最終レビュー verdict、未解決/延期 items を記録する。
- `closed` 計画を再開する場合は、再開理由と再開後の scope を deepwork file に追記し、再開前の最終検証結果を無効化しない。

## 12. 対話言語ルール

- ユーザーへの最終返答は日本語とする。
- 内部推論、調査メモ、検索クエリ、専門用語、コードレビュー注釈は英語で処理してよい。
- 推論や内部メモをユーザーに見せる場合は、ユーザー向けには日本語で要約する。
- ユーザーが明示的に別の言語を求めた場合は、その指示に従う。
- このルールはコンテキスト圧縮後も維持し、会話履歴が短くなってもユーザー向け返答を日本語にする。
