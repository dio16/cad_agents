# 未決定設計要素レポート

**対象リポジトリ**: `cad_agent_framework`  
**生成日**: 2026-06-17  
**目的**: スケルトン実装から「実際の CADAGENT」へ進むために、未決定または不足している設計要素を整理し、優先順位と責任境界を明示する。

---

## 1. エグゼクティブサマリ

現状のリポジトリは **「安全な I/O 境界とゴールデンパスの skeleton」** として整っているが、自由文設計意図から自律的に仕様・DSL・CAD・検証・修正を回す **実運用の CADAGENT ではない**。

最優先で決めるべきは以下の 5 要素である。これらが固まらないまま Phase 2/Production v1 の要素を拡張しても、安全な設計プラットフォームにはならず「stub をつなげた PoC」が肥大化するだけである。

| 順位 | 決めるべき要素 | 理由 |
|---|---|---|
| 1 | **MVP スコープ** | 現在の golden path（単一部品・pipe clamp・FDM）を超えて何を目指すかを固定しないと、DSL/Validation/CAD の拡張方向が散る |
| 2 | **DSL v1 正式仕様** | `box`/`cylinder`/`through_hole` だけでは実用的形状を作れない。op セット、座標系、parameter reference、feature order、versioning を固定しないと自由コード生成への回帰リスクがある |
| 3 | **CAD Runtime contract** | surrogate / CadQuery / FreeCAD / OCCT の責任境界、sandbox、artifact 正本形式、failure reason code を決めないと、生成形状の信頼性を説明できない |
| 4 | **Validation contract** | 現在は bbox/volume/最小壁厚/穴径など PoC 判定に留まり、本当のトポロジ・製造性・組立性を保証できない |
| 5 | **Orchestrator / Human Approval Workflow** | 検証失敗後の修正ループ、max revision loops、escalation、仕様変更・validation override・regulated/export-controlled・新規 DSL op の承認状態機械を実装する必要がある |

---

## 2. 現状の実装成熟度

### 2.1 実装済み（ skeleton 含む）

| 領域 | 内容 | 主要ファイル |
|---|---|---|
| Phase 1 PoC | Requirement/Specification/DSL/Validation Report の JSON Schema、AST validator、golden pipeline | `cad_agent/platform_poc.py`, `schemas/phase1/*.json` |
| Phase 2 Pilot | DFM/AM catalog、worker probe、review diff HTML、audit log、Model Gateway trial | `cad_agent/phase2_pilot.py` |
| Production v1 skeleton | stdlib API server、in-memory project/job service、sync job queue、security/observability stubs | `cad_agent/api_server.py`, `cad_agent/job_queue.py`, `cad_agent/project_service.py` |
| Production v2 stubs | static material catalog、BOM aggregation、AABB assembly interference | `cad_agent/material_catalog.py`, `cad_agent/bom.py`, `cad_agent/assembly_checks.py` |

### 2.2 未実装 / 未決定

- 実体の LLM エージェント（Requirement Extractor / Spec Composer / DSL Compiler）
- 本物の CAD worker pool（FreeCAD/OCCT/Blender の native execution）
- 本格的なトポロジ・製造性・組立性検証
- Orchestrator と revision loop
- 永続化（DB、オブジェクトストレージ）
- 人間承認ワークフロー
- 非同期ジョブキュー
- 認証・認可・テナント分離
- 完全な監査ログ不変化
- 実材料 DB、部品ライブラリ、PLM/ERP/MES 連携
- FEA、接触、運動解析
- glTF/PNG/PDF export worker

---

## 3. 未決定設計要素の詳細

### 3.1 LLM / エージェント層

**現状の問題**:

- `/v1/requirements/extract`、`/v1/specifications/generate` は golden stub を返すだけ（`cad_agent/api_server.py:290-293`）
- Requirement Extractor / Spec Composer / DSL Compiler のプロンプト、LLM routing、出力検証、修正ループが未実装

**決めるべきこと**:

1. Requirement JSON への分解ルール（functional requirement の粒度、unknowns/assumptions の分離基準）
2. Specification JSON のドラフト生成方針（製造条件・公差を「提案」で終わらせ、人間承認を必須にする境界）
3. DSL 生成のプロンプト設計と output schema enforcement（jsonschema 検証後にのみ CAD Runtime へ渡す）
4. 修正ループ：Validation Report をフィードバックして DSL Compiler が修正案を出す仕組み
5. 各 LLM エージェントの model route（public/internal/confidential/regulated/export-controlled）

**主担当エージェント**: Requirement Extractor / Spec Composer / DSL Compiler  
**補佐**: Model Gateway（routing 実行）、Policy/Audit（法規タグ）

### 3.2 CAD Runtime 層

**現状の問題**:

- DSL op は `box`, `cylinder`, `through_hole` のみ（`cad_agent/platform_poc.py:19-23`）
- FreeCAD/OCCT/Blender は probe するだけで、実 worker pool ではない（`cad_agent/phase2_pilot.py:146-155`）
- STEP は surrogate text、STL/OBJ も surrogate（`cad_agent/platform_poc.py:210-222`, `cad_agent/phase2_pilot.py:158-182`）
- sandbox、worker isolation、kernel failure handling が未確定

**決めるべきこと**:

| 設計要素 | 選択肢 | 推奨 |
|---|---|---|
| CAD kernel | CadQuery/OCCT vs FreeCAD vs Blender vs 商用 kernel | まず CadQuery（OCCT）を本格化し、FreeCAD/Blender は adapter として利用 |
| Surrogate 境界 | ライブラリ不在時のフォールバックをどこまで許容するか | 単純形状の volume/bbox 確認用に限定し、最終 artifact は native kernel 必須とする |
| DSL op セット | box/cylinder/through_hole → ? | フェーズ的に追加：fillet/chamfer/loft/sweep/pattern/assembly_constraint |
| Sandbox | コンテナ、seccomp、ネットワーク分離、容量制限 | まず Docker + 読み取り専用 artifact ディレクトリ + タイムアウト |
| 正本形式 | STEP AP242 / B-Rep を厳密に | native kernel 時は実 AP242、surrogate 時は「surrogate」タグを必須付与 |
| エラーコード | kernel 失敗を Validation が解釈可能に | CAD_BUILD_FAILED, NO_ADDITIVE_FEATURE, NON_POSITIVE_VOLUME, KERNEL_TIMEOUT 等を機械可読化 |

**主担当エージェント**: CAD Runtime  
**補佐**: Validation（error code 解釈）、Policy/Audit（sandbox 監査）

### 3.3 Validation 層

**現状の問題**:

- `cad_agent/platform_poc.py:357-450` は bbox/volume/artifact 存在/units/FDM 最小壁厚・穴径のみ
- `cad_agent/assembly_checks.py` は AABB stub のみ
- 非流形、自己交差、B-Rep 健全性、組立干渉、接触、運動、FEA は未実装

**決めるべきこと**:

1. Validation Report の check 一覧と reason code 体系
2. 各 check の閾値と tolerance（例：bbox 0.1 mm、壁厚 2.0 mm、穴径 3.0 mm）
3. Validation override の条件（Reviewer 承認時のみ条件付き許容）
4. 将来拡張としての FEA / 接触 / 運動の扱い（現時点では「将来拡張候補」として report に記録するか、fail するか）
5. topology check の本格化（mesh 水密性、自己交差、非流形エッジ）

**主担当エージェント**: Validation  
**補佐**: CAD Runtime（形状・topology 情報提供）、Orchestrator（fail 時の修正ループ）

### 3.4 Orchestrator / Workflow 層

**現状の問題**:

- Orchestrator エージェントが未実装
- `record_human_approval`（`cad_agent/platform_poc.py:540-565`）は JSONL 書き込みのサンプルで、承認ワークフロー本体ではない
- Validation fail 後の自動修正ループがない

**決めるべきこと**:

1. ワークフロー状態機械：design_intent → requirement → spec → dsl → cad → validation → approval → export
2. `max_revision_loops`（例：3 回まで）
3. 3 回以上の検証失敗時の人間へのエスカレーション
4. 承認待ち状態の job 管理（`pending_approval`）
5. 仕様変更、新規 DSL op、regulated/export-controlled タグ付与時の必須承認フロー

**主担当エージェント**: Orchestrator  
**補佐**: Policy/Audit（承認記録）、人間（最終判断）

### 3.5 Infrastructure / Persistence 層

**現状の問題**:

- `api_server.py` は stdlib `http.server`
- `project_service.py` は in-memory dict
- `security_policy.py` はハードコード API key `local-dev-key`
- `job_queue.py` は同期 simulation
- `/v1/validation/jobs`, `/v1/revisions`, `/v1/exports` は 501 未実装

**決めるべきこと**:

| 設計要素 | 現状 | 決めるべきこと |
|---|---|---|
| Project/Job 永続化 | in-memory | SQLite/PostgreSQL + マイグレーション方針 |
| Artifact ストレージ | ローカルファイル + jsonl index | S3/MinIO 等オブジェクトストレージ + 署名付き URL |
| 認証・認可 | ハードコード API key | JWT/OIDC + tenant 分離 + RBAC |
| Job Queue | 同期 | 非同期 worker pool（Celery/RQ/K8s Job） |
| テナント分離 | なし | project_id / tenant_id による完全分離 |
| API 未実装エンドポイント | 501 | `/v1/validation/jobs`, `/v1/revisions`, `/v1/exports` の仕様 |
| 観測性 | Prometheus text counters | 分散 tracing、構造化ログ |

**主担当エージェント**: Orchestrator / Policy/Audit  
**補佐**: CAD Runtime / Validation（worker 接続）

---

## 4. エージェント責任対応表

| 意思決定 | 主担当エージェント | 補足 |
|---|---|---|
| 自然文から要件項目へどう分解するか | Requirement Extractor | unknowns/assumptions の分離、functional requirement の粒度 |
| Requirement schema の必須項目・曖昧性表現 | Requirement Extractor | Spec Composer と共同で cross-document contract 化 |
| 仕様変更案の形式 | Spec Composer | 仕様そのものは人間承認が必要 |
| material / manufacturing profile / validation plan のドラフト方針 | Spec Composer | 製造条件や公差を独断で確定してはいけない |
| DSL operation allowlist と versioning | DSL Compiler | 新規 operation は人間承認対象 |
| parameter reference / feature order / derivative outputs contract | DSL Compiler | 現在の schema は Phase 1 用で狭い |
| CAD backend 選択、sandbox、artifact 生成責任 | CAD Runtime | surrogate と native kernel の境界を明確化 |
| CAD failure reason code | CAD Runtime | Validation が解釈可能な機械可読エラーにする |
| Validation check 一覧、閾値、reason code、pass/fail 判定 | Validation | 不合格を合格扱いにしない品質ゲート |
| Revision loop、max loop、escalation、approval gate | Orchestrator | 現在最も不足している制御層 |
| data classification、retention、audit schema、compliance tag | Policy/Audit | regulated/export-controlled の判定と記録 |
| commercial / onprem / hybrid routing policy | Model Gateway | Policy/Audit が policy を持ち、Gateway が routing 実行 |
| 仕様変更、validation override、regulated/export-controlled、新規 DSL operation の最終判断 | 人間 | エージェントは提案のみ |

---

## 5. 推奨する段階的実装方針

### Phase A（今すぐ）：コア契約の固定（2〜4 週間目標）

1. **MVP スコープを宣言**  
   当面は「単一部品・非安全重要・FDM/CNC 3軸プロトタイプ」のみを対象とする。これ以外は「将来拡張」と明記する。

2. **DSL v1 仕様を定義**  
   - op セットを固定：box, cylinder, through_hole, fillet, chamfer, linear_pattern（当面）
   - 座標系、parameter reference（`$name`）、feature order の実行可能性を schema + 静的検証
   - 新規 op 追加時は人間承認

3. **Validation contract v1**  
   - dimensions_check: bbox ± tolerance, volume > 0
   - topology_check: 水密性 proxy（surrogate 時は注記）、native kernel 時は実メッシュ検証
   - manufacturing_profile_rules: プロファイル別 min_wall / min_hole / build_volume
   - unit_consistency: mm 固定
   - reason code 体系を固定

4. **Orchestrator 状態機械**  
   - job status: pending → running → completed/failed/pending_approval
   - max_revision_loops = 3
   - 承認が必要なイベントを明確化

### Phase B（次）：CAD Runtime と LLM エージェントの実体化

5. **CAD Runtime 本格化**  
   - CadQuery/OCCT を優先実装
   - surrogate 時は artifact に `surrogate=true` メタデータを必須付与
   - sandbox コンテナ化

6. **LLM エージェント実装**  
   - Requirement Extractor プロンプト + schema enforcement
   - Spec Composer プロンプト + 人間承認待ち
   - DSL Compiler プロンプト + AST 検証

7. **非同期 Job Queue**  
   - Redis + worker（まず 1 worker、スケールは後）
   - `/v1/validation/jobs`, `/v1/revisions`, `/v1/exports` を実装

### Phase C（その後）：本番運用準備

8. 永続化（PostgreSQL + S3/MinIO）
9. 認証・認可・テナント分離
10. 不変監査ログ（署名、保持期間ポリシー）
11. 材料 DB、部品ライブラリ、PLM/ERP/MES 連携
12. FEA、接触、運動、精密組立検証

---

## 6. 後回しでよい判断

以下は、コア契約が固まってから取り組むべきである。

| 判断 | 理由 |
|---|---|
| Kubernetes / KServe / vLLM / Argo CD / Cosign / Trivy | Production v1 readiness 以降。PoC/Pilot の契約が固まる前に投入すると複雑化しやすい |
| 実材料 DB、部品ライブラリ、PLM/ERP/MES 連携 | material catalog と BOM は skeleton_stub のため、まず Phase 1/2 contract を固定すべき |
| FEA、接触、運動、精密組立検証 | 現状は AABB stub / DFM minimal rule の段階。先に Validation contract を決めるべき |
| glTF/PNG/PDF 本格 export | STEP/STL/OBJ surrogate が未確定の段階では export worker 拡張より artifact contract が先 |
| 完全な tenant isolation / immutable audit storage | 監査ログの形式と保持ポリシーを先に決めるべき |
| 商用 LLM endpoint 実接続 | Model Gateway policy はあるが、実プロンプト/agent contract が未確定なので後回し可 |

---

## 7. リスク：決めない場合

1. **Skeleton を本番と誤認する**  
   golden pipeline が通ることと、任意設計意図を安全に CAD 化できることは別である。

2. **LLM が仕様や DSL を実質的に独断変更する**  
   DSL/Spec contract と human approval workflow が弱いまま拡張すると、安全原則が崩れる。

3. **CAD Runtime の真偽判定が曖昧になる**  
   surrogate、CadQuery、FreeCAD/OCCT の境界を決めないと、生成形状の信頼性を説明できない。

4. **Validation が品質ゲートとして機能しない**  
   現在の Validation は PoC rule に近く、実形状・製造性・組立性を保証できない。

5. **監査・法規対応が後付けになる**  
   confidential / regulated / export-controlled の routing と audit log が弱いまま運用すると、機密漏洩や保持ポリシー違反の可能性がある。

6. **API / job / artifact が運用不能になる**  
   in-memory project、同期 job、ローカル artifact index では、複数ユーザー・複数ジョブ・長期運用に耐えられない。

7. **DSL 拡張が自由コード生成に戻る**  
   DSL grammar と operation governance を先に決めないと、LLM が Python/FreeCAD macro 生成へ逃げる構造になる。

---

## 8. 結論と次のアクション

**結論**:  
現状のリポジトリは「安全な設計プラットフォームの骨格」として優秀だが、実際の CADAGENT として機能させるには、まず **コア契約（MVP スコープ、DSL v1、CAD Runtime、Validation、Orchestrator/承認）を固定** する必要がある。これらを決めてから、非同期化、永続化、マルチパーツ、FEA、法規対応を段階的に追加していくべきである。

**次のアクション**:

1. `SPEC.md` または新しい `DSL_V1_SPEC.md` 草案を作成し、DSL v1 の op セット、座標系、parameter reference、feature order、versioning を人間レビュー可能な形で文書化する。
2. `CAD_RUNTIME_CONTRACT.md` または同等の文書を作成し、surrogate/native の境界、正本形式、error code、sandbox 要件を固定する。
3. `VALIDATION_CONTRACT.md` または同等の文書を作成し、check 一覧、reason code、閾値、override ルールを固定する。
4. `ORCHESTRATOR_WORKFLOW.md` を作成し、job 状態機械、revision loop、human approval workflow を定義する。
5. 上記 4 文書をレビュー・承認した後、Phase B の実装（LLM エージェント、CAD Runtime 本格化、非同期 job queue）に着手する。
