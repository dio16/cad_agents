# プラットフォーム設計・実装計画・ゴール定義書・エージェント運用規則 作成計画

## 目的

参照元 `docs/Origen/Design_document_for_a_machine_design_platform.md` の設計思想を反映しつつ、現実的な運用観点で以下を準備する：
1. プラットフォーム設計書
2. 実装計画書
3. ゴール定義書
4. AGENTS.md

## スコープ

- 生wikiの内容を逐語コピーしない。抽象化・再構成して、プロジェクトの既存文書群と矛盾なく運用できる形へ翻案する。
- 法務・セキュリティ・運用統制は原則として記録と手順に留め、プロンプト内に機微情報を埋め込まない。
- すべての成果物は markdown であり、更新容易性と参照可能性を重視する。

## 参照元から採用する設計原則

- LLMは設計意図の構造化装置、CADカーネルと検証器が真偽判定の主体である
- 自由文を直接CADコードに流さない。構造化DSL / JSON Schema をI/O境界に置く
- 正本は STEP AP242 + B-Rep + Parametric DSL であり、STL/OBJ/PNG/PDF は派生物
- 公差はモデル属性でなく工程属性として管理
- セキュリティは「外部API禁止」「人間確認ゲート厳守」で基本設計する

## 作成対象ドキュメント

### 1. プラットフォーム設計書
- ファイル名: `docs/platform_design_ja.md`
- 内容:
  - エグゼクティブサマリ
  - 設計前提と要求定義
  - 推奨アーキテクチャ（コンポーネント、責務、技術選定、比較）
  - データフローとAPI設計
  - LLMプロンプト設計原則
  - セキュリティ、法規、運用統制
  - 運用コストと移行、スケーラビリティ

### 2. 実装計画書
- ファイル名: `docs/platform_implementation_ja.md`
- 内容:
  - 開発フェーズ（PoC / Pilot / Production v1 / Production v2）
  - タスク分割と責任分担
  - リソース割り当て（ロール、人数、期間）
  - スケジュールとマイルストン
  - CI/CD、テスト計画、KPI
  - コストと移行計画

### 3. ゴール定義書
- ファイル名: `docs/platform_goal_ja.md`
- 内容:
  - SMART で定義した目標
  - 成功基準（工学的 / 運用 / 業務）
  - 失敗条件
  - 優先目標
  - 測定方法と頻度

### 4. AGENTS.md
- ファイル名: `AGENTS.md`
- 内容:
  - 全体ゴールの最上位要約（参照先を明記）
  - エージェント種別と役割（設計、実装、検証、インテグレータなど）
  - 責任範囲と境界条件
  - I/Oスキーマ厳守ルール（人入力、AI出力、CAD実行、検証レポート）
  - 禁止事項と安全装置
  - 作業フロー、ゲート、使用コマンド
  - 現場で迷わないための最小ルールセット

## 想定されるエージェント一覧

- Product Manager：要件優先順位、Go/No-Go、非機能要件の責任者
- Architect：プラットフォーム構成、技術選定、アーキテクチャ図
- Specification Designer：RequirementJSON / SpecJSON / DSL スキーマの設計と改訂
- AI Engineer：LLM呼び出し、プロンプト設計、構造化出力保証
- CAD Engineer：CAD Runtime DSL・FreeCAD Bridge・STEP生成の責務
- Validation Engineer：幾何妥当、DFM/AM、FEA、Regressionテストの責務
- QA Engineer：テスト計画、品質レビュー、出来高検証
- Security Engineer：データ分類、ルーティング、監査、法規対応
- Release Engineer：CI/CD、キュー、観測、デプロイ
- Integrator：仕様と実装の橋渡し、依存関係整理、契約テスト
- Reviewer：人間による設計承認、規程遵守確認、最終証明
- Operator：ジョブ実行、失敗調査、エスカレーション

## 作成手順

1. 既存の `docs/`、`AGENTS.md`、`GOAL.md`、`SPEC.md`、`TASKS.md` を読み、既存の正本や用語と整合する。
2. 原案の設計思想を尊重しつつ、プロジェクト文脈に合わせて名称・粒度を調整する。
3. Markdown生成が必要になるが、現状の実行環境では `docs/` 配下へのファイル作成が許可されていないため、**実装可能なプランナに保存する**。
4. 実装担当エージェントは、本計画の「対象ドキュメント」に従って markdown ファイルを所定パスに生成する。

## 検証

- ドラフト段階では全文を人間確認へ回す運用とする
- 受け入れ条件は明確な参照構造を持ち、プロジェクト内の他の文書と矛盾しないこと

## ブランチ/ファイル配置

```
docs/
  platform_design_ja.md
  platform_implementation_ja.md
  platform_goal_ja.md
```

```
AGENTS.md
```

## 次の一歩

実装可能なエージェントが本計画に従い、以下のファイルを作成する：
- docs/platform_design_ja.md
- docs/platform_implementation_ja.md
- docs/platform_goal_ja.md
- AGENTS.md
