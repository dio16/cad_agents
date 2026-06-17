# CADAGENT 設計仕様書・実装計画書

**対象**: 生成AI活用型 機械設計・3D CAD生成・3Dプリント出力プラットフォーム  
**初期ターゲット**: ジャイロ・トゥールビヨン風 卓上キネティック・オブジェ  
**作成日**: 2026-06-17  
**想定リポジトリ**: `cad_agent_framework` / `cad_agent` 系実装  
**目的**: これまでの検討、未決定設計要素レポート、OSS CADカーネル調査、3Dプリンタ製造制約を踏まえ、実装に移れるレベルの設計仕様と段階的実装計画を定義する。

---

## 0. エグゼクティブサマリ

本プラットフォームは、ユーザーが自然文で機械の目的・機能要件・制約を入力し、LLMエージェントが要求・仕様・機構構成・CAD DSLを生成し、CAD RuntimeがネイティブCAD形状を生成し、Validationが幾何・製造性・組立性・可動干渉を検証したうえで、STEP / STL / 3MF / glTF 等のartifactを出力するシステムである。

最終的には汎用機械設計プラットフォームを目指す。ただし、初期MVPでは対象を広げすぎず、以下に限定する。

> **MVP対象**: 3Dプリンタで製作可能な、非安全重要・卓上サイズ・低速可動・複数部品アセンブリの機械オブジェ。

初号機は、実用時計ではなく、**ジャイロ・トゥールビヨン機構の動作を楽しむ卓上キネティック・オブジェ** とする。時計精度、長時間耐久性、実用脱進機、全樹脂ゼンマイ駆動はMVP対象外とし、まずは低速手回しまたは低速モーター駆動で、回転軸・歯車・ケージ・ジンバル・ベアリング座・組立性・3Dプリント性を検証できる状態を目標とする。

CADカーネルは **OCCT（Open CASCADE Technology）** を正本カーネルとし、実装入口は **CadQuery** を採用する。LLMに自由なPython/CadQueryコードを直接生成させず、LLMはJSON Schemaで制約された **Mechanism DSL** のみを生成する。DSL CompilerがCadQuery APIへ変換し、CadQuery経由でOCCT B-Repを生成する。

---

## 1. ゴールと非ゴール

### 1.1 ゴール

1. 自然文から機械設計意図を抽出し、要求仕様へ変換する。
2. 要求仕様から、人間が確認可能な設計仕様を生成する。
3. 設計仕様から、制約されたCAD DSLを生成する。
4. CAD DSLから、OCCT/CadQueryによりネイティブB-Rep CAD形状を生成する。
5. 3Dプリンタ製造性、組立性、幾何妥当性、可動干渉を検証する。
6. STEPを正本artifact、STL/3MFを3Dプリント用artifact、glTF/PNGをプレビューartifactとして出力する。
7. Validation失敗時に、最大3回まで自動修正ループを回す。
8. 仕様確定、製造条件変更、Validation override、新規DSL operation追加、印刷用export前には人間承認を必須とする。

### 1.2 非ゴール

MVPでは以下を対象外とする。

- 安全重要部品、人体保護部品、車両・航空・医療・法規制対象部品。
- 実用時計精度を持つ時計機構。
- 長時間耐久保証、摩耗寿命保証。
- 高速回転機構。
- 完全な機械式脱進機・ゼンマイ・調速機の設計保証。
- 商用CADと同等の自由曲面設計。
- PLM / ERP / MES 連携。
- 高精度FEA、接触解析、摩耗解析、熱変形解析。
- 完全自動の製造可否保証。

---

## 2. MVPスコープ定義

### 2.1 MVP名称

**CADAGENT MVP v1: Parametric 3D-Printed Kinetic Mechanism Platform**

### 2.2 MVP対象物

| 項目 | 仕様 |
|---|---|
| 対象 | 3Dプリンタで作る非安全重要の卓上機構 |
| 初号機 | ジャイロ・トゥールビヨン風キネティック・オブジェ |
| 構成 | 複数部品アセンブリ |
| 製造 | FDM標準、SLA高精度オプション |
| 使用部品 | 3Dプリント部品 + 市販ベアリング + 金属シャフト + M2/M3ねじ + 熱圧入インサート |
| サイズ | 目安: 幅120〜180 mm、高さ120〜220 mm |
| 駆動 | v1: 手回しまたは低速ギアモーター、v2以降: ゼンマイ/重錘/疑似脱進機 |
| 可動 | 2軸以上の回転ジョイント、可能なら外側ジンバル + 内側ケージ + 装飾回転体 |
| 正本 | STEP / 内部B-Rep |
| 派生 | STL / 3MF / glTF / PNG / PDF簡易レポート |

### 2.3 初号機の設計思想

初号機は「本物の時計」ではなく、「機械の動作を見るオブジェ」である。

したがって、以下を優先順位とする。

1. 動作が見えること。
2. 3Dプリンタで部品が作れること。
3. 組み立て可能であること。
4. 低速で滑らかに回ること。
5. 干渉せず、破損しにくいこと。
6. CAD DSLから再生成可能であること。
7. 将来の汎用機械設計へ拡張できること。

---

## 3. システム全体アーキテクチャ

### 3.1 全体パイプライン

```text
User Natural Language Intent
  ↓
Requirement Extractor
  ↓ requirement.json
Spec Composer
  ↓ specification.json
Mechanism Planner
  ↓ mechanism_plan.json
DSL Compiler
  ↓ mechanism_dsl.json
DSL Static Validator
  ↓ validated_dsl.json
CadQuery Adapter
  ↓ CadQuery script, internal only
OCCT / CadQuery Runtime
  ↓ B-Rep / STEP / STL / 3MF / glTF
Validation Engine
  ↓ validation_report.json
Orchestrator
  ├─ pass → human approval → export
  └─ fail → revision loop → retry / escalation
```

### 3.2 正本と派生artifact

| 種別 | 形式 | 位置づけ |
|---|---|---|
| 要求正本 | `requirement.json` | ユーザー意図の構造化 |
| 仕様正本 | `specification.json` | 人間承認対象 |
| DSL正本 | `mechanism_dsl.json` | CAD生成の制約済み入力 |
| CAD正本 | `model.step` / internal B-Rep | 他CAD連携・設計正本 |
| 3Dプリント | `model.stl`, `model.3mf` | スライサー投入用 |
| Web表示 | `model.glb`, `preview.png` | UI確認用 |
| 検証 | `validation_report.json` | pass/fail, reason code |
| 監査 | `audit_log.jsonl` | 変更履歴・承認履歴 |

### 3.3 設計原則

1. **LLMは提案者であり、設計正本の所有者ではない。**
2. **LLM出力は必ずJSON Schemaで検証する。**
3. **LLM生成コードを直接実行しない。**
4. **CAD生成はallowlist化されたDSL経由のみとする。**
5. **STEP/B-Repを正本、STL/3MFは派生とする。**
6. **surrogate artifactは開発時のみ許可し、本番exportでは禁止する。**
7. **Validationがfailしたartifactを印刷用にexportしない。**
8. **人間承認なしに仕様変更、製造条件変更、Validation overrideを行わない。**

---

## 4. CADカーネル選定仕様

### 4.1 採用方針

| 役割 | 採用 |
|---|---|
| 正本CADカーネル | OCCT |
| 実装API | CadQuery |
| GUI確認・手修正 | FreeCAD |
| メッシュmanifold検証 | Manifold |
| 計算幾何補助 | CGAL |
| 可視化・レンダリング | Blender |

### 4.2 OCCT採用理由

OCCTは、B-Rep、曲線・曲面、トポロジ、STEP/IGES/STL/glTFデータ交換、Shape Healingを備えるOSS CADカーネルである。今回のような機械部品、回転軸、ベアリング座、歯車、ケージ、ねじ穴、フィレット、面取り、STEP正本管理には、mesh専用ライブラリよりB-Rep CADカーネルが適している。

### 4.3 CadQuery採用理由

OCCTを直接C++ APIで扱うと実装負荷が高い。CadQueryはOCCTをPythonから扱える高水準APIであり、JSON DSLからの変換先として実装しやすい。

### 4.4 Manifold/CGALの位置づけ

Manifoldは3Dプリント向けのmanifold mesh検証、mesh boolean、3MF/mesh品質確認に使う。CGALは距離計算、AABB tree、幾何判定、将来の衝突判定強化に使う。ただし、どちらもSTEP/B-Rep正本の主カーネルにはしない。

---

## 5. LLMエージェント設計

### 5.1 エージェント一覧

| エージェント | 入力 | 出力 | 主責任 |
|---|---|---|---|
| Requirement Extractor | 自然文 | `requirement.json` | 要求・制約・未知点の抽出 |
| Spec Composer | requirement | `specification.json` | 設計仕様案の作成 |
| Mechanism Planner | specification | `mechanism_plan.json` | 機構構成案の作成 |
| DSL Compiler | mechanism plan | `mechanism_dsl.json` | DSL生成 |
| Validation Interpreter | validation report | `revision_request.json` | fail理由の解釈 |
| Revision Agent | DSL + fail reason | `revised_dsl.json` | 修正案生成 |
| Policy/Audit Agent | 全イベント | audit log | 承認・監査・ポリシー適用 |

### 5.2 LLM出力制約

すべてのLLM出力は以下を満たす。

- JSON Schemaに準拠する。
- `additionalProperties: false` を原則とする。
- enumはallowlist化する。
- 未知・曖昧な点は `unknowns` または `assumptions` に分離する。
- 仕様確定が必要な項目は `requires_human_approval: true` を付与する。
- CAD実行コード、OSコマンド、任意Pythonコードを出力してはならない。

### 5.3 Requirement JSON仕様

```json
{
  "schema_version": "1.0",
  "project_id": "string",
  "title": "string",
  "user_intent": "string",
  "functional_requirements": [
    {
      "id": "FR-001",
      "description": "string",
      "priority": "must|should|could"
    }
  ],
  "non_functional_requirements": [],
  "manufacturing_intent": {
    "process": "fdm|sla|unknown",
    "material_preference": "pla|petg|asa|resin|unknown",
    "printer_profile": "string"
  },
  "constraints": [],
  "unknowns": [],
  "assumptions": [],
  "requires_human_approval": true
}
```

### 5.4 Specification JSON仕様

```json
{
  "schema_version": "1.0",
  "project_id": "string",
  "product_profile": "desktop_kinetic_mechanism",
  "target_object": "gyro_tourbillon_kinetic_object",
  "unit": "mm",
  "manufacturing_profile": "fdm_standard_0p4_nozzle",
  "design_envelope": {
    "max_width": 180,
    "max_depth": 180,
    "max_height": 220
  },
  "motion_policy": {
    "max_rpm": 10,
    "default_rpm": 3,
    "drive_type": "manual_crank|gear_motor|spring_placeholder"
  },
  "materials": [],
  "standard_hardware": [],
  "validation_plan": [],
  "approval_state": "draft|approved|rejected"
}
```

---

## 6. Mechanism DSL v1.1仕様

### 6.1 DSL設計方針

DSLは、LLMが自由なCADコードを生成することを防ぎ、CAD Runtimeが安全に解釈可能な中間表現とする。

DSLは以下の4層に分ける。

1. Geometry DSL
2. Mechanism DSL
3. Assembly DSL
4. Motion DSL

### 6.2 Geometry DSL

| 分類 | operation |
|---|---|
| 基本形状 | `box`, `cylinder`, `cone`, `torus`, `tube`, `ring` |
| スケッチ | `circle`, `arc`, `polyline`, `slot`, `rectangle`, `regular_polygon` |
| ソリッド操作 | `extrude`, `revolve`, `sweep`, `loft` |
| 加工 | `cut`, `through_hole`, `counterbore`, `countersink`, `pocket`, `slot_cut` |
| 仕上げ | `fillet`, `chamfer`, `shell` |
| パターン | `linear_pattern`, `circular_pattern`, `mirror` |

### 6.3 Mechanism DSL

| 分類 | operation |
|---|---|
| 歯車 | `spur_gear`, `ring_gear`, `pinion`, `gear_pair` |
| 軸 | `shaft`, `axle_bore`, `bearing_seat`, `bushing_seat` |
| 回転体 | `rotor_cage`, `gimbal_ring`, `tourbillon_cage`, `balance_wheel_visual` |
| フレーム | `base_frame`, `support_bridge`, `spoke_ring`, `decorative_bridge` |
| 締結 | `screw_hole`, `heatset_insert_boss`, `nut_trap` |
| クリアランス | `clearance_envelope`, `swept_volume` |

歯車は自由形状で生成させない。`module`, `teeth`, `pressure_angle`, `backlash`, `bore_diameter` などを指定し、決定論的gear generatorで形状を生成する。

### 6.4 Assembly DSL

| 分類 | operation |
|---|---|
| 部品 | `part`, `subassembly` |
| 配置 | `place`, `transform`, `align_axis` |
| 拘束 | `mate_coaxial`, `mate_planar`, `mate_distance`, `mate_angle` |
| ジョイント | `revolute_joint`, `fixed_joint`, `gear_constraint` |
| 可動範囲 | `rotation_limit`, `clearance_check_region` |

### 6.5 Motion DSL

| 分類 | operation |
|---|---|
| 入力 | `manual_crank`, `gear_motor`, `spring_barrel_placeholder` |
| 運動 | `rotational_axis`, `axis_chain`, `gear_ratio`, `rpm_range` |
| 検証 | `motion_sweep_check`, `collision_over_time`, `min_dynamic_clearance` |

### 6.6 DSL例

```json
{
  "schema_version": "1.1",
  "unit": "mm",
  "parts": [
    {
      "id": "outer_gimbal_ring",
      "type": "part",
      "features": [
        {
          "op": "gimbal_ring",
          "outer_diameter": 140,
          "inner_diameter": 118,
          "thickness": 8,
          "width": 10
        },
        {
          "op": "bearing_seat",
          "bearing_type": "MR83",
          "axis": "X",
          "position": [70, 0, 0]
        },
        {
          "op": "bearing_seat",
          "bearing_type": "MR83",
          "axis": "X",
          "position": [-70, 0, 0]
        }
      ]
    }
  ],
  "joints": [
    {
      "op": "revolute_joint",
      "id": "outer_axis",
      "parent": "base_frame",
      "child": "outer_gimbal_ring",
      "axis": [1, 0, 0],
      "rpm_range": [0, 10]
    }
  ],
  "validations": [
    {
      "op": "motion_sweep_check",
      "joint": "outer_axis",
      "range_deg": [0, 360],
      "min_clearance": 0.6
    }
  ]
}
```

---

## 7. CAD Runtime Contract

### 7.1 Runtime責任

CAD Runtimeは以下を行う。

1. DSLを受け取る。
2. DSL opをCadQuery関数へ変換する。
3. CadQuery経由でOCCT shapeを生成する。
4. B-Rep妥当性を確認する。
5. STEP/STL/3MF/glTFを出力する。
6. 生成失敗時に機械可読エラーコードを返す。

### 7.2 禁止事項

- LLM生成Pythonコードの直接実行。
- 任意import。
- 任意ファイルアクセス。
- ネットワークアクセス。
- CAD worker外からのOSコマンド実行。
- Validation未通過artifactの印刷用export。

### 7.3 Artifact正本ルール

| artifact | 必須 | 条件 |
|---|---|---|
| STEP | 必須 | native OCCT生成のみ |
| STL | 必須 | STEP/B-Repから派生 |
| 3MF | 推奨 | printable mesh用 |
| glTF/GLB | 推奨 | viewer用 |
| CadQuery script | 内部保持のみ | ユーザー正本ではない |
| surrogate STEP | 本番禁止 | 開発テストのみ |

### 7.4 CAD error code

| code | 意味 |
|---|---|
| `CAD_BUILD_FAILED` | CAD生成失敗 |
| `UNSUPPORTED_DSL_OP` | 未対応operation |
| `INVALID_PARAMETER_REFERENCE` | 未定義パラメータ参照 |
| `NON_POSITIVE_VOLUME` | 体積が0以下 |
| `BOOLEAN_FAILED` | ブーリアン失敗 |
| `FILLET_FAILED` | フィレット失敗 |
| `GEAR_GENERATION_FAILED` | 歯車生成失敗 |
| `ASSEMBLY_CONSTRAINT_FAILED` | アセンブリ拘束失敗 |
| `KERNEL_TIMEOUT` | カーネル実行タイムアウト |
| `EXPORT_FAILED` | artifact出力失敗 |

---

## 8. Validation Contract

### 8.1 Validation層

Validationは以下の5層で構成する。

1. Schema Validation
2. CAD Geometry Validation
3. Manufacturing Validation
4. Assembly Validation
5. Motion Validation

### 8.2 必須チェック一覧

| check | 内容 | fail例 |
|---|---|---|
| `schema_check` | JSON Schema準拠 | 未定義op、型不一致 |
| `unit_check` | mm固定 | inch混入 |
| `parameter_check` | `$param`参照解決 | 未定義パラメータ |
| `feature_order_check` | CAD生成順序 | cut対象が存在しない |
| `brep_validity_check` | B-Rep健全性 | 非閉シェル、自己交差 |
| `mesh_watertight_check` | STL水密性 | 穴、反転面 |
| `dfm_fdm_check` | FDM造形性 | 壁厚不足、穴径不足、過大ブリッジ |
| `assembly_clearance_check` | 組立隙間 | ベアリング座干渉 |
| `motion_axis_check` | 回転軸整合 | 軸ずれ、拘束不足 |
| `motion_sweep_collision_check` | 回転時干渉 | ケージと外枠が接触 |
| `gear_mesh_check` | 歯車整合 | 中心距離不一致、バックラッシュ不足 |
| `export_check` | STEP/STL/3MF生成 | native artifactなし |

### 8.3 FDM標準プロファイル

| 項目 | 初期値 |
|---|---:|
| 単位 | mm |
| ノズル | 0.4 mm |
| 積層ピッチ | 0.16〜0.20 mm |
| 最小機能壁厚 | 1.2 mm以上推奨 |
| 最小装飾壁厚 | 0.8 mm以上 |
| 最小穴径 | 2.0 mm以上 |
| 可動部クリアランス | 0.6 mm以上 |
| 静的部品間クリアランス | 0.3 mm以上 |
| オーバーハング | 45°以上を原則 |
| ブリッジ | 10 mm以下を原則 |
| 底面 | 45°面取りでエレファントフット対策 |

### 8.4 初号機合格条件

| 項目 | 合格条件 |
|---|---|
| Native CAD | CadQuery/OCCTでSTEP生成成功 |
| STL | 水密、自己交差なし |
| 部品数 | 5〜30部品 |
| 可動軸 | 2軸以上の回転ジョイント |
| 動的干渉 | 指定回転範囲で干渉なし |
| 最小可動隙間 | FDM標準で0.6 mm以上 |
| ギア | 歯数、モジュール、中心距離、バックラッシュが整合 |
| 製造性 | 各部品が指定build volume内 |
| 組立性 | シャフト・ベアリング・ねじの挿入方向が存在 |
| 人間承認 | spec freeze と print export 前に必須 |

---

## 9. Orchestrator / Human Approval Workflow

### 9.1 状態機械

```text
created
  → requirement_extracted
  → spec_drafted
  → pending_spec_approval
  → spec_approved
  → mechanism_planned
  → dsl_generated
  → cad_built
  → validation_running
  → validation_passed
  → pending_export_approval
  → exported
```

失敗時は次のループを使う。

```text
validation_failed
  → revision_requested
  → dsl_revised
  → cad_built
  → validation_running
```

### 9.2 自動修正ループ

| 項目 | 仕様 |
|---|---|
| 最大自動修正回数 | 3回 |
| 3回失敗後 | `needs_human_review` |
| 仕様変更が必要な場合 | `change_request` として停止 |
| 新規DSL opが必要な場合 | 人間承認必須 |
| Validation override | reviewer権限のみ |
| regulated/export-controlled | MVPでは停止 |

### 9.3 承認必須イベント

- 仕様確定。
- 製造プロファイル変更。
- 材料変更。
- 駆動方式変更。
- 新規DSL operation追加。
- Validation override。
- 印刷用artifact export。
- regulated / export-controlled / safety-critical タグ検出。

---

## 10. 初号機: ジャイロ・トゥールビヨン風オブジェ仕様

### 10.1 製品定義

| 項目 | 仕様 |
|---|---|
| 名称 | Gyro Tourbillon Desk Kinetic Object v1 |
| 目的 | 多軸回転するトゥールビヨン風機構を鑑賞する |
| 時計精度 | 対象外 |
| 駆動 | v1は手回しまたは低速ギアモーター |
| v2駆動 | ゼンマイ・重錘・疑似脱進機へ拡張 |
| サイズ | 幅120〜180 mm、高さ120〜220 mm |
| 回転軸 | 外側ジンバル1軸 + 内側ケージ1軸 + 装飾回転体1軸 |
| 速度 | 1〜10 rpm程度の低速鑑賞用 |
| 構成 | ベース、外枠、内枠、トゥールビヨンケージ、歯車列、支持フレーム |
| 使用部品 | 3Dプリント部品、金属シャフト、ミニチュアベアリング、M2/M3ねじ |

### 10.2 サブアセンブリ

| サブアセンブリ | 内容 |
|---|---|
| `base_module` | 台座、モーター/手回し入力、固定フレーム |
| `outer_gimbal_module` | 外側リング、左右支持軸、ベアリング座 |
| `inner_cage_module` | 内側回転ケージ、中心軸、装飾スポーク |
| `gear_train_module` | 入力ギア、減速/増速ギア、リングギア |
| `visual_balance_module` | 脱進機風の見える装飾回転体 |
| `cover_optional` | 透明カバーや展示用支柱 |

### 10.3 標準パラメータ

```json
{
  "product_profile": "desktop_kinetic_mechanism",
  "first_target": "gyro_tourbillon_object",
  "unit": "mm",
  "manufacturing_profile": "fdm_standard_0p4_nozzle",
  "max_build_volume": [180, 180, 180],
  "motion_policy": {
    "max_rpm": 10,
    "default_rpm": 3,
    "allow_motor_drive": true,
    "allow_spring_drive": "v2_only",
    "require_guard_for_high_speed": true
  },
  "mechanism_defaults": {
    "min_moving_clearance": 0.6,
    "min_static_clearance": 0.3,
    "min_wall_functional": 1.2,
    "min_hole_diameter": 2.0,
    "default_shaft_diameter": 3.0,
    "default_fasteners": ["M2", "M3"],
    "default_bearing_series": ["MR83", "MR93", "625", "608"]
  },
  "approval_required_for": [
    "spec_freeze",
    "manufacturing_profile_change",
    "new_dsl_operation",
    "validation_override",
    "export_for_print"
  ]
}
```

---

## 11. API設計

### 11.1 MVP API一覧

| method | endpoint | 内容 |
|---|---|---|
| POST | `/v1/projects` | project作成 |
| POST | `/v1/requirements/extract` | 自然文から要求抽出 |
| POST | `/v1/specifications/generate` | 仕様案生成 |
| POST | `/v1/specifications/{id}/approve` | 仕様承認 |
| POST | `/v1/mechanisms/plan` | 機構構成生成 |
| POST | `/v1/dsl/compile` | DSL生成 |
| POST | `/v1/cad/build` | CAD生成job作成 |
| GET | `/v1/jobs/{id}` | job状態取得 |
| POST | `/v1/validation/jobs` | Validation実行 |
| POST | `/v1/revisions` | 修正ループ実行 |
| POST | `/v1/exports` | artifact export |
| GET | `/v1/artifacts/{id}` | artifact取得 |

### 11.2 Job状態

| status | 意味 |
|---|---|
| `pending` | 待機中 |
| `running` | 実行中 |
| `completed` | 完了 |
| `failed` | 失敗 |
| `pending_approval` | 人間承認待ち |
| `needs_human_review` | 自動修正不可 |
| `cancelled` | 中止 |

---

## 12. インフラ・永続化設計

### 12.1 MVP構成

| 領域 | MVP | Production候補 |
|---|---|---|
| API | FastAPI | FastAPI / gateway |
| DB | SQLite | PostgreSQL |
| Object Storage | local filesystem | S3 / MinIO |
| Queue | RQ / Celery + Redis | Celery / Temporal / Kubernetes Jobs |
| CAD worker | Docker container | isolated worker pool |
| Auth | local API key | OIDC/JWT/RBAC |
| Audit | JSONL | append-only store / signed log |
| Observability | structured log | OpenTelemetry + Prometheus |

### 12.2 Sandbox要件

CAD workerは以下を満たす。

- Docker containerで実行。
- ネットワーク遮断。
- 入出力ディレクトリ限定。
- CPU/メモリ/時間制限。
- 実行ログ保存。
- LLMから直接到達不可。
- artifact生成後にhashを記録。

---

## 13. セキュリティ・安全設計

### 13.1 LLM安全設計

- prompt injectionを前提にする。
- RAGやfine-tuningでは完全に防げない前提で設計する。
- LLM出力は必ずschema validationする。
- LLM出力にコード実行権限を与えない。
- tool呼び出しはOrchestratorが明示的に許可する。
- external contentとsystem instructionを分離する。

### 13.2 CAD安全設計

- 安全重要用途はMVP対象外。
- 高速回転部品はfailまたは人間承認。
- バネ、圧縮エネルギー、飛散リスクはv2以降。
- 鋭利形状、薄肉破損リスクはValidationで警告。
- 3Dプリント材料強度は保証しない。

### 13.3 監査ログ

記録対象は以下。

- ユーザー入力。
- LLM出力。
- schema validation結果。
- DSL差分。
- CAD生成設定。
- Validation結果。
- 人間承認者、承認時刻、承認対象。
- artifact hash。

---

## 14. 実装計画

## Phase 0: 設計契約固定

**目的**: skeletonから実CADAGENTへ進む前に、契約を固定する。

### タスク

1. `MVP_SCOPE.md` を作成。
2. `MECHANISM_DSL_V1.md` を作成。
3. `CAD_RUNTIME_CONTRACT.md` を作成。
4. `VALIDATION_CONTRACT.md` を作成。
5. `ORCHESTRATOR_WORKFLOW.md` を作成。
6. JSON Schemaを `schemas/v1/` に配置。
7. 全API endpointのrequest/response schemaを定義。

### 完了条件

- 主要5文書がレビュー可能。
- DSL op allowlistが固定。
- human approval対象が明確。
- surrogate/native境界が明確。

---

## Phase 1: Native CAD golden path

**目的**: stub/surrogateではなく、CadQuery/OCCTで実STEP/STLを生成する。

### タスク

1. CadQuery worker containerを作成。
2. `box`, `cylinder`, `through_hole`, `fillet`, `chamfer` を実装。
3. STEP/STL/3MF exportを実装。
4. B-Rep volume/bbox取得を実装。
5. artifact manifestを生成。
6. timeout/error codeを実装。

### 完了条件

- DSLから実STEPが生成される。
- surrogate artifactを使わない。
- artifact hashが記録される。

---

## Phase 2: 3DプリントDFM validation

**目的**: 印刷できない形状を自動検出する。

### タスク

1. FDM profileを実装。
2. build volume check。
3. min wall proxy check。
4. min hole diameter check。
5. overhang/bridge proxy check。
6. bottom chamfer recommendation。
7. 3MF export検証。

### 完了条件

- FDM標準プロファイルでpass/failが出る。
- fail reasonが機械可読。
- LLM Revision Agentへ渡せるreportになる。

---

## Phase 3: Assembly DSL

**目的**: 複数部品の配置・同軸・平面・距離拘束を扱う。

### タスク

1. `part`, `subassembly` 実装。
2. `place`, `transform`, `align_axis` 実装。
3. `mate_coaxial`, `mate_planar`, `mate_distance` 実装。
4. AABB干渉チェック。
5. ベアリング座・シャフト挿入方向check。
6. assembly STEP export。

### 完了条件

- 5部品以上のアセンブリSTEPが生成される。
- AABB干渉が検出できる。
- 部品ごとのSTLが出力できる。

---

## Phase 4: Mechanism DSL

**目的**: ジャイロ・トゥールビヨンに必要な機構opを実装する。

### タスク

1. `bearing_seat` 実装。
2. `shaft` / `axle_bore` 実装。
3. `gimbal_ring` 実装。
4. `tourbillon_cage` 実装。
5. `spoke_ring` 実装。
6. `spur_gear` generator実装。
7. `gear_pair` validation実装。

### 完了条件

- 外側ジンバルリング、内側ケージ、軸受け座がDSLから生成される。
- 歯車の中心距離・モジュール・バックラッシュが検証される。

---

## Phase 5: Motion validation

**目的**: 可動干渉を検証する。

### タスク

1. `revolute_joint` 実装。
2. `rotational_axis` 実装。
3. 回転スイープサンプリング実装。
4. 最小動的クリアランス算出。
5. `motion_sweep_collision_check` 実装。
6. glTFで軸・可動範囲を可視化。

### 完了条件

- 360°回転または指定範囲で干渉有無を確認できる。
- 可動部最小クリアランスがreportに出る。
- UIで回転軸が見える。

---

## Phase 6: LLMエージェント実装

**目的**: 自然文からRequirement/Spec/DSLを生成する。

### タスク

1. Requirement Extractor prompt実装。
2. Spec Composer prompt実装。
3. Mechanism Planner prompt実装。
4. DSL Compiler prompt実装。
5. Structured Outputs / JSON Schema enforcement。
6. LLM出力のschema retry。
7. unknowns/assumptions分離。

### 完了条件

- 自然文からrequirement/spec/dslが生成される。
- schema不適合時に自動retryされる。
- spec approval前にCAD生成されない。

---

## Phase 7: Revision loop / Human approval

**目的**: 検証失敗時に安全に修正し、限界時に人間へ戻す。

### タスク

1. Validation Interpreter実装。
2. Revision Agent実装。
3. max revision loop = 3。
4. job state machine実装。
5. `pending_approval` 実装。
6. approval API実装。
7. audit log実装。

### 完了条件

- Validation failから最大3回修正できる。
- 3回失敗で人間レビューへ移行。
- 承認ログが保存される。

---

## Phase 8: 初号機完成

**目的**: ジャイロ・トゥールビヨン風卓上オブジェを生成・検証・出力する。

### タスク

1. 初号機テンプレートDSL作成。
2. parameter setを複数用意。
3. base_module生成。
4. outer_gimbal_module生成。
5. inner_cage_module生成。
6. gear_train_module生成。
7. visual_balance_module生成。
8. motion validation実施。
9. STEP/STL/3MF/glTF出力。
10. 組立説明簡易Markdown出力。

### 完了条件

- 初号機の全主要部品が生成される。
- 部品別STLが出る。
- assembly STEPが出る。
- 動的干渉チェックが通る。
- 人間承認後にprint exportできる。

---

## 15. リポジトリ構成案

```text
cad_agent/
  api/
    server.py
    routes_projects.py
    routes_requirements.py
    routes_specs.py
    routes_cad.py
    routes_validation.py
    routes_exports.py
  agents/
    requirement_extractor.py
    spec_composer.py
    mechanism_planner.py
    dsl_compiler.py
    validation_interpreter.py
    revision_agent.py
  schemas/
    v1/
      requirement.schema.json
      specification.schema.json
      mechanism_dsl.schema.json
      validation_report.schema.json
      artifact_manifest.schema.json
  dsl/
    validator.py
    resolver.py
    op_registry.py
  cad_runtime/
    cadquery_worker.py
    adapters/
      geometry_ops.py
      mechanism_ops.py
      assembly_ops.py
      gear_generator.py
    exporters.py
    error_codes.py
  validation/
    geometry_checks.py
    dfm_fdm_checks.py
    assembly_checks.py
    motion_checks.py
    gear_checks.py
  orchestrator/
    workflow.py
    job_service.py
    revision_loop.py
    approval_service.py
  storage/
    db.py
    artifact_store.py
    audit_log.py
  configs/
    manufacturing_profiles.yaml
    hardware_catalog.yaml
  examples/
    gyro_tourbillon_v1/
      intent.md
      requirement.json
      specification.json
      mechanism_dsl.json
  docs/
    MVP_SCOPE.md
    MECHANISM_DSL_V1.md
    CAD_RUNTIME_CONTRACT.md
    VALIDATION_CONTRACT.md
    ORCHESTRATOR_WORKFLOW.md
```

---

## 16. テスト計画

### 16.1 Unit tests

- JSON Schema validation。
- DSL op validation。
- parameter reference解決。
- gear parameter validation。
- FDM profile rule。
- error code mapping。

### 16.2 Golden tests

| golden | 内容 |
|---|---|
| `single_bracket` | 単一部品、穴、フィレット |
| `bearing_block` | ベアリング座、ねじ穴 |
| `spur_gear_pair` | 歯車2個、中心距離検証 |
| `gimbal_ring` | 外側リング、左右軸 |
| `tourbillon_cage` | 内側ケージ、スポーク |
| `gyro_tourbillon_assembly` | 初号機アセンブリ |

### 16.3 Regression tests

- STEP生成成功。
- STL水密性。
- bbox/volume安定性。
- hash変化検出。
- 同一DSLから同一artifactが生成されること。
- revision loopの停止条件。

---

## 17. リスクと対策

| リスク | 対策 |
|---|---|
| LLMが仕様を勝手に確定 | spec approval必須 |
| LLMが危険コードを生成 | DSLのみ許可、コード実行禁止 |
| CAD kernelが失敗 | error code化、revision loop、fallback禁止 |
| STLは出るがCADとして壊れている | STEP/B-Rep正本、B-Rep validation |
| 可動部が干渉 | motion sweep validation |
| FDMで動かない | clearance rule、printer calibration profile |
| 歯車が噛み合わない | deterministic gear generator、gear mesh check |
| 初号機が難しすぎる | v1は低速手回し/モーター、ゼンマイはv2 |
| ライセンス問題 | OCCT/CadQuery/Manifold/CGALの利用形態をレビュー |
| skeleton肥大化 | Phaseごとにacceptance criteriaを固定 |

---

## 18. 受け入れ基準

### MVP v1受け入れ基準

1. 自然文からRequirement JSONが生成される。
2. Specification JSONが生成され、人間承認できる。
3. Mechanism DSLが生成される。
4. DSLからCadQuery/OCCTで実STEPが生成される。
5. STL/3MF/glTFが派生生成される。
6. FDM profile validationが動く。
7. 複数部品assemblyが生成される。
8. 回転ジョイントとmotion sweep validationが動く。
9. 初号機ジャイロ・トゥールビヨン風オブジェの主要部品が生成される。
10. Validation pass後、人間承認を経てprint artifactをexportできる。

---

## 19. 参考情報

- Open CASCADE Technology Documentation: https://dev.opencascade.org/doc/overview/html/
- OCCT Data Exchange: https://dev.opencascade.org/about/data_exchange
- CadQuery Documentation: https://cadquery.readthedocs.io/
- CadQuery Import/Export: https://cadquery.readthedocs.io/en/latest/importexport.html
- CGAL: https://www.cgal.org/
- Manifold: https://github.com/elalish/manifold
- FreeCAD: https://www.freecad.org/
- UltiMaker FDM design guidance: https://ultimaker.com/learn/design-for-fff-3d-printing-maximize-your-success/
- Formlabs design guide: https://formlabs.com/global/white-papers/form-4-design-guide/
- OWASP LLM Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs

---

## 20. 次の実装アクション

直近では、以下の順に実装する。

1. `docs/MVP_SCOPE.md` を本書から分割して作成。
2. `schemas/v1/mechanism_dsl.schema.json` を作成。
3. `cad_runtime/cadquery_worker.py` を実装。
4. `dsl/op_registry.py` でallowlist管理を実装。
5. `validation/geometry_checks.py` と `validation/dfm_fdm_checks.py` を実装。
6. `examples/gyro_tourbillon_v1/mechanism_dsl.json` を作成。
7. 初号機の `outer_gimbal_ring` と `bearing_seat` を最初のnative CAD targetにする。
8. その後、`tourbillon_cage`、`gear_pair`、`motion_sweep_check` を追加する。

---

以上。
