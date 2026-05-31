# 生成AI活用機械設計プラットフォーム 実装計画書

## 1. 計画方針と前提

### 1.1 不変の制約

- 完成CADを一発生成させる設計にはしない
- 正本仕様と検証を分離し、決定論的生成を確実にする
- セキュリティ/法規/監査の要件は本番移行に先立って確定
- 小規模から検証し、段階的に自動範囲を拡張する

### 1.2 成功の定義（暫定）

- 参照する目標定義は `docs/platform_goal_ja.md`
- 監査可能な設計システムとして機能している
- 人手レビューの継続を前提としつつ、再生成と再検証の繰り返し時間を削減できている

## 2. 開発フェーズ

### Phase 0: Foundation（基盤）

**目的**：契約と運用基盤を確定する。

- Requirement JSON, Specification JSON, Parametric DSL, Validation Report のスキーマ確定とバージョン管理
- CI/CD初期フロー：Lint/Unit/Contract/Schema
- リポジトリ構成、ディレクトリ命名、artifact ID規則、generation identity規則
- 開発/運用表、責任境界、非機能要件の再定義

**完了条件**：4スキーマが初回版として固定され、プルリク/マージが可能になっている。

### Phase 1: PoC（6〜10週）

**目的**：自然文要求から単一部品のSTEP/STLを端緒まで自動生成する最小パイプラインを成立させる。

#### タスク

| ID | 名称 | 内容 | 担当 |
|---|---|---|---|
| 1.1 | 要件抽出モジュール | LLM+スキーマ→Requirement JSON | AI/プロンプト |
| 1.2 | 仕様生成モジュール | Requirement→Specification JSON | AI/プロンプト |
| 1.3 | Parametric DSL仕様策定 | 実行可能・監査可能なDSLを定義 | CAD Runtime |
| 1.4 | CAD Runtime最小版 | STEP/STL生成、エラー報告 | CAD Runtime |
| 1.5 | Geometry Validation最小版 | watertight, self-intersection, bbox/volume | Validation |
| 1.6 | Artifact Store最小版 | 同一generation identityで保存/参照 | Platform |
| 1.7 | PoC受入基準策定 | 単一部品のend-to-end成功とログ保存 | Platform/Ops |

#### リソース

- Product Owner：要件とKPI管理
- AI/LLM担当：プロンプト、スキーマ、モデル選定
- CAD Runtime担当：DSL、CadQuery/OCCT/FreeCAD ブリッジ
- Validation/QA：テストケース、regression基準
- Platform/Ops：CI/CD、artifact store、環境

#### スケジュール（目安）

- Week 1–2：スキーマ確定、CI/CD、アーキテクチャ凍結
- Week 3–5：DSL/CAD Runtime最小版
- Week 6–8：要件/仕様とループ検証
- Week 9–10：PoC受入と完了報告

### Phase 2: Pilot（10〜16週）

**目的**：設計者が設計作業内で試行できる運用体制を確立する。

- CadQuery/FreeCAD ヘッドレス統合
- ビューア/レンダリング/プレビュー 派生生成
- DFM/AMプロファイル適用と工程別ルール切替
- レビューUI + diff viewer + 版比較
- 監査ログ・監査ID・保持期間ポリシー
- ノイハイサイクル・サーキュラー設計向け最小機能

**完了条件**：設計者が対象パートカタログ内で反復生成・承認を進められる。

### Phase 3: Production v1（4〜6か月）

**目的**：部門導入可能な信頼性と運用基盤を実装する。

- Model Gateway（商用API / オンプレvLLM のポリシー切替）
- 承認フロー（草案承認、製造承認、法務タグ）
- 権限制御（テナント別 Object prefix / Row Level Security）
- セキュリティ策：AST/schema検査、サンドボックス実行、プロンプトインジェクション検証
- 観測基盤：ジョブ所要時間、失敗理由分類、コスト、GPU利用率
- CDパイプライン（Argo CD、カナリア、署名、SBOM）
- セルフホストランナー対応

**完了条件**：部門内の案件フローが回り、手順書と責任分担が文書化されている。

### Phase 4: Production v2（6か月以降）

**目的**：実案件適用と拡張性を確実にする。

- 組立干渉検査、BOM/PLM連携
- FEA統合（CalculiX/同等）
- 大規模ジョブキュー、優先度、タイムアウト、リトライ
- 材料DB、工程DB、標準部品ライブラリ統合
- オンプレLLM評価・切替フロー

**完了条件**：実案件で適用回数が増え、失敗原因の分布が安定して縮小している。

## 3. タスク分割と責任

### 3.1 チーム/役割

| 役割 | 責任 | 連携先 |
|---|---|---|
| Product Owner | 顧客価値、優先順位、Go/No-Go判断 | 全チーム |
| Lead AI Engineer | プロンプト、スキーマ、生成品質、エスカレーション設計 | CAD Runtime, Validation |
| CAD Runtime Engineer | Parametric DSL、CADカーネル実行、フォーマット出力 | AI Engineer, Validation |
| Validation Engineer | 幾何/DFM/AM/FEA基準、テスト自動化 | CAD Runtime, Platform |
| Security / Compliance | データ分類、ルーティング、監査、法規対応タグ | Platform, AI Engineer |
| Platform / SRE | ジョブ実行、ストレージ、監視、CD/セキュリティ基盤 | 全チーム |
| Mechanical Design Reviewer | 仕様と検証結果の妥当性、人手承認基準 | AI Engineer, Validation |

### 3.2 責任境界

- AI Engineer は「仕様化案とDSL案」を出すが、CAD Runtime が実行する
- CAD Runtime は仕様変更を判断せず、仕様違反/実行失敗を報告する
- Validation は工学基準で判定し、工程プロファイルと連動する
- Security/Compliance は案件開始時に法規・機密・輸出管理タグを確定する
- Reviewer は生成物の機械設計的妥当性と承認可否を判定する

## 4. 開発リソース構成

### 4.1 リソース条件

| 項目 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| 開発人数 | 4–6人 | 6–10人 | 10–16人 | 12–20人 |
| LLM担当 | 1–2 | 1–2 | 2–3 | 2–3 |
| CAD Runtime担当 | 1–2 | 2–3 | 3–4 | 3–4 |
| Validation担当 | 1 | 1–2 | 2 | 2–3 |
| Platform/SRE | 1 | 1–2 | 2–3 | 2–3 |
| Security/Compliance | 0.5 | 0.5–1 | 1 | 1 |
| 外部契約/評価 | 都度 | 都度 | 常時/定期 | 常時 |

### 4.2 人件費・期間の想定

- PoC：1,200万〜2,500万円、6–10週
- Pilot：開発継続、運用慣熟
- Production v1：4–6か月、4,000万–1.2億円規模を想定
- Production v2：実案件拡張、保守運用費が増加

## 5. スケジュールとマイルストン

### 5.1 マイルストン一覧

| マイルストン | 観測可能な完了条件 | 検証方法 |
|---|---|---|
| M1 スキーマ固定 | 4スキーマがCIでvalid | JSON Schema Contract Test |
| M2 PoC成功 | 単一部品のend-to-end生成成功 | generation_idで検証可能 |
| M3 Pilot導入 | 設計者が1案件を回せる | 利用率/所要時間/失敗率 |
| M4 Production v1開始 | 承認フローと監査運用が機能 | 監査ログ欠損率=0 |
| M5 Production v2適用 | 実案件1件完了 | FEA/組立/DFM合格レポート |

## 6. コスト構造と移行計画

### 6.1 コスト大分類

| 分類 | 内容 |
|---|---|
| LLM利用料 | API or GPU推論、ルーティング方式で変動 |
| CAD/検証ワーカー | CPU/GPUワーカー、キュー、待ち時間 |
| ストレージ/監査 | Artifact、ログ保持、検索基盤 |
| 開発人件費 | 設計/実装/レビュー/運用 |
| セキュリティ/監査 | 外部監査、契約、SBOM管理 |

### 6.2 移行順序

1. 支援型：要件整理と仕様ドラフト作成
2. 半自動：単一部品の雛形生成
3. 検証付き自動：DFM/AM/幾何検証付き再試行
4. 組立・解析拡張：干渉/FEA/PLM接続

## 7. 品質保証とテスト計画

### 7.1 テスト階層

| 層 | 目的 | 例 |
|---|---|---|
| Unit | スキーマ・ロジック破綻防止 | JSON Schema validator, parameter resolver |
| Contract | LLM出力契約維持 | requirement/spec/dsl strict validation |
| CAD Integration | 実行器健全性 | DSL→STEP/STL成功 |
| Geometry | 形状妥当性 | watertight, self-intersection, bbox/volume |
| DFM/AM | 工程適合 | 最小肉厚、支持角度、最小クリアランス |
| Regression | 差分監視 | gold case の体积/質量/寸法比較 |
| Visual Regression | ビュー品質 | 固定視点差分 |
| FEA Verification | 工学要件 | 最大変位、応力、固有値条件 |
| Security | 生成AI脅威 | prompt injection, code escape |
| Performance | SLO | p95応答、queue待ち、GPU利用率 |

### 7.2 推奨ゴールデンケース

- ブラケット、カバー、スペーサ、治具、パイプクランプ、簡易組立
- 機微案件はexternal blockerとして管理

## 8. 主要リスクと対応

### 8.1 リスク一覧

| リスク | 影響 | 緩和策 |
|---|---|---|
| 仕様の未確定性 | 再生成コスト増 | assumption/unknown分離、初期profile適用 |
| LLMモデル変更 | 出力スキーマ逸脱 | JSON Schema Contract Test |
| データ漏えい | 法規・信用失墜 | データ分類/ルーティング/外部送信禁止 |
| 機密設計情報の流出 | 競争優位喪失 | オンプレ優先ルート、監査ID、保持期限 |
| FEA/DFM誤判定 | 不合格/不合格突破 | 複数検証器、人手承認自動化抑制 |
| 法規/安全保障違反 | 法的制裁 | export tag, 該非判定フロー |
| 実機適合差 | 現地調整工数増 | 公差profile, 実機試験はアウトオブスコープ明記 |
