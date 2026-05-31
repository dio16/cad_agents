# 生成AI活用機械設計プラットフォーム 設計書

## 1. 目的とミッション

本プラットフォームは、LLM に直接「完成CAD」を一発生成させるのではなく、**要件の構造化 → 仕様化 → 安全なパラメトリックDSL生成 → CADカーネル実行 → 幾何/造形/必要に応じたFEA検証 → STEP/STL/OBJ等への派生出力**という多段パイプラインを提供することを目的とする。

設計意図の解釈と構造化は LLM が担い、実行・測定・構成・検証は決定論的 CAD カーネルと検証器が担う。この分離により、曖昧さの解消と真偽判定を明確に分担する。

## 2. 非目標（スコープ境界）

### 2.1 確約しない範囲

- 完全無人での最終設計承認
- 実機プリンタ・材料・スライサー依存の最終クリアランス保証
- 長時間運転時の摩耗・反り・耐久性の保証
- 実物組立後の操作感の保証
- ネイティブOnshape依存の完結性（あくまで任意の最終レビュー/共有手段）
- 機密性の高い案件を外部APIへ無条件で送信してよい旨の汎用承諾

### 2.2 アウトオブスコープを前提に運用する理由

これらを最初から含めると、検証不可能な責任を設計システムに押し付けることになる。プラットフォームは「設計/検証の信頼性向上」に責任を持ち、実機依存の最終適合判断は設計者/現場に委ねられる。

## 3. 推奨アーキテクチャ

### 3.1 アーキテクチャ原則

- **パラメトリック表現を正本とする**
- **LLMは設計計画器、CADカーネルは実行器、検証器は品質ゲート**
- **自由文を直接実行しない**
- **プロファイル駆動で公差・製造・運用条件を切り替え**
- **監査・版管理・証拠生成を同一世代で一元化**

### 3.2 4層アーキテクチャ

1. Model Gateway + Orchestrator（入力解釈、仕様生成、ワークフロー制御）
2. Deterministic CAD Runtime（パラメトリック実行、形状生成、属性管理）
3. Validation Loop（幾何検証、DFM/AM、必要に応じFEA）
4. Artifact / Audit Store（版管理、監査、配布）

## 4. コンポーネント構成

### 4.1 責務と推奨技術

| コンポーネント | 主責務 | 推奨技術 | 理由 |
|---|---|---|---|
| Web UI / CAD Viewer | 要件入力、差分表示、承認 | React系、three.js系ビューワ | 設計意図と形状の橋渡し |
| API Gateway / Auth | 認証認可、テナント境界、監査ID付与 | FastAPI / Kong / Keycloak | 責任分界とアクセス制御 |
| Project Service | 案件、版、承認状態、部材関係の管理 | PostgreSQL | 正本データのReliable Source |
| Requirement Extractor | 自由文→Requirement JSON | 商用API / オンプレLLM | 自然言語の構造化 |
| Spec Composer | 不足項目抽出、仮定管理、Specification JSON生成 | LLM + ルールエンジン | 仕様化とトレーサビリティ |
| Retrieval Service | 設計ルール/過去仕様/プリンタプロファイル検索 | PostgreSQL + pgvector | 知識の再利用 |
| CAD DSL Compiler | Spec→安全なParametric DSL | Python + AST/schema validator | 任意コード実行の回避 |
| CAD Runtime | DSL実行、B-Rep/STEP生成、属性埋込み | CadQuery / build123d / OCCT | 決定論的生成 |
| Render / Mesh Worker | レンダリング、STL/OBJ/glTF派生 | text-to-CAD Harness / 同等 | 視覚確認/配布 |
| Validation Service | 幾何妥当性、寸法照合、機能チェック | Local gate chain | 独立した品質判定 |
| Export Service | STEP/STL/OBJ/PDF等のパッケージ出力 | CadQuery/OCP/FreeCAD adapter | 成果物の利用性 |
| Policy / Audit Service | ルーティング規則、ログ、法規タグ、保持期間 | OPA / Postgres / Object Storage | 運用制御と監査 |
| Observability | Token、ジョブ、失敗要因、SLO監視 | OpenTelemetry / Prometheus | 運用健全性 |

### 4.2 正本/派生データの定義

| レイヤ | 正本 | 派生 |
|---|---|---|
| 要件 | Requirement JSON | - |
| 仕様 | Specification JSON | - |
| 生成命令 | Parametric DSL / Operation Graph | - |
| 形状 | STEP AP242 / B-Rep | STL / OBJ / glTF |
| 検証 | Validation Report JSON | PNG / PDF 図面 |
| メタ | 版ID、生成ID、監査ID、利用モデル | レポート要約 |

編輯・再生成・差分管理の正本はSTEP/B-Repとパラメトリック情報に置き、STL/OBJは派生物として扱う。公差はモデル属性ではなく工程属性として管理する。

## 5. ワークフロー

### 5.1 標準設計フロー

1. 要件入力
   - 自然言語、図面、表ファイルを統合して Requirement JSON を生成
   - unknowns/assumptions を分離し不足情報を明示

2. 仕様化
   - 寸法、材料、製造プロファイル、検証条件を Specification JSON へ確定
   - conservative default は仕様側で確定し、推測を下流へ流さない

3. Parametric DSL 生成
   - Specification JSON から決定論的 operation graph を生成
   - JSON Schema / AST validator を通過した DSL だけを実行

4. CAD 実行
   - STEP AP242 / B-Rep 生成
   - 属性情報をモデルに併記

5. 検証ループ
   - geometry, DFM/AM, assembly interference, validation report を生成
   - NG なら failure reason を添えて仕様不変の修正 DSL を要求

6. パッケージ化
   - STEP, STL, preview, validation report, BOM/assembly info を同一世代 ID で固化
   - current delivery artifact を更新

## 6. 技術スタック

### 6.1 技術選択の基準

- 決定論的再現性がある
- 監査ログとトレーサビリティを作りやすい
- ヘッドレス実行とバッチ処理に適合する
- 標準フォーマット（STEP/STL/JSON）と相性が良い
- 機密性とデータルーティング要件に柔軟に対応できる

### 6.2 スタック案

| 候補 | 構成 | 強み | 弱み | 採用判断 |
|---|---|---|---|---|
| OSS核心ハイブリッド | OCCT + CadQuery/build123d + Blender + 商用API | 最短PoC化、デバッグ容易 | 商用API依存の継続コスト | 初期推奨 |
| 主権重視ハイブリッド | 同上 + vLLM + KServe | データ主権、運用ポリシーの自己決定 | GPU運用コスト | 拡張期 |
| 既存CAD統合型 | 同上 + Fusion Connector | 下流CAM/CAE連携 | クラウド依存とライセンス管理 | 条件付き採用 |
| 商用Kernel拡張型 | 商用 CAD Kernel + connector | 既存資産親和性 | ライセンス費/ベンダロック | 非推奨（初期） |

## 7. データルート、API設計、非機能要件

### 7.1 API設計原則

- 全LLM工程は JSON Schema 契約で入出力を固定
- CAD/検証ワーカーは非同期ジョブとして実行
- 失敗時は failure_code + reason を必須

### 7.2 主要API（例）

| エンドポイント | 用途 | 同期/非同期 |
|---|---|---|
| POST /v1/projects | 案件作成 | 同期 |
| POST /v1/requirements/extract | 自然文→要件JSON | 同期 |
| POST /v1/specifications/generate | 要件JSON→仕様JSON | 同期 |
| POST /v1/cad/jobs | 仕様→CAD生成ジョブ | 非同期 |
| GET /v1/cad/jobs/{job_id} | ジョブ状態取得 | 同期 |
| POST /v1/validation/jobs | 再検証ジョブ | 非同期 |
| POST /v1/exports | 成果物パッケージ出力 | 同期 |
| GET /v1/artifacts/{artifact_id} | 成果物取得 | 同期 |

### 7.3 非機能要件

- 再現性：同一DSL/parameter/specで同一artifact hash
- 監査性：全生成物に requirement_id / specification_id / model_route / prompt_version / artifact_hash を付与
- セキュリティ：任意コードの直接実行は既定で禁止、エキスパート用途も明示許可ログ
- 分離：CADランタイムはネットワーク分離サンドボックスで実行
- 可観測性：ジョブ所要時間、失敗理由、コスト、待ち時間を計測
- 移行性：商用/オンプレ切替は gateway でルーティング変更だけで完了させる

## 8. LLMプロンプト設計原則

### 8.1 適用原則

- 自由文を直接CADコードにしない
- Structured Outputs / Function Calling を前提に構造化JSONだけをI/Oに使う
- 要件抽出、仕様生成、DSL生成、検証、修正はプロンプト責務を分ける
- 単位系、unknowns、assumptions、実行権限制限を明示
- 修正はValidation Reportを根拠に、仕様不変でDSL差分だけを実施

### 8.2 適用方針

| 原則 | 具体方針 |
|---|---|
| 役割分離 | 要件抽出 / 仕様生成 / DSL生成 / 検証 / 修正を分離 |
| 構造化出力 | 全段でJSON Schema準拠を要求 |
| 単位固定 | mm / deg / N / MPa |
| 禁止事項 | 任意コード生成、仕様の無断変更 |
| 再試行設計 | 検証失敗時の修正ループを定義 |

## 9. 運用コストと移行、スケーラビリティ

### 9.1 段階移行

| 段階 | 現場の使い方 | 期待効果 | 技術要件 |
|---|---|---|---|
| 支援型 | 要件整理・仕様ドラフト | 記述品質と抜け漏れ改善 | LLM + Structured Output |
| 半自動 | 単一部品の雛形生成 | 試作スピード向上 | DSL + CadQuery/OCCT |
| 検証付き自動 | DFM/AM/幾何検証つき再試行 | 再作業削減 | Validation loop |
| 組立・解析拡張 | 組立干渉・FEA・PLM接続 | 実案件適用 | FEA / Connector / Policy |

### 9.2 スケール方針

| テーマ | 推奨方式 |
|---|---|
| マルチテナント | object prefix / DB row-level security |
| ジョブ処理 | API短時間同期 / CAD・FEA非同期 |
| モデル切替 | `commercial / onprem / hybrid` |
| 知識ベース | 版管理埋め込み + 案件固有DB分離 |
| 監査 | 全artifactに traceability を保存 |
| 将来拡張 | 組立、材料DB、BOM、PLM、MES adapter追加 |

### 9.3 CI/CDフロー（指針）

- CI：Lint / Unit / Contract / Schema / CAD Integration / Golden Regression
- CD：Model Gateway のルーティング変更、承認フロー、カナリア
- 供給網：SLSA provenance + container signature + SBOM
