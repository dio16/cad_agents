# platform_design_ja.md

この文書は、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` に基づく設計の索引・要約です。詳細は原案と `docs/architecture_ja.md`、`docs/api_contracts_ja.md`、`docs/validation_security_ja.md`、`docs/operations_ja.md` を参照してください。

## 設計方針

- LLM は設計計画器であり、CAD カーネルは実行器、Validation は品質ゲートです。
- 自由文を直接 CAD コードに流さず、Requirement JSON、Specification JSON、Parametric DSL、Validation Report の構造化境界を下流工程に置きます。
- 正本形状は STEP AP242 / B-Rep とし、STL / OBJ / glTF / PNG / PDF は派生物として扱います。
- 仕様変更、regulated / export-controlled タグ、新規 DSL operation、Validation override は人間承認またはレビュー承認ゲートを必須にします。

## 主要コンポーネント

- API Gateway / Auth: 認証、案件作成、ジョブ起動、成果物取得
- Workflow Orchestrator: 標準フロー、修正ループ、ゲート制御
- Model Gateway: commercial / onprem / hybrid のデータ分類ベースのルーティング
- Requirement Extractor / Spec Composer / DSL Compiler: 構造化出力のみを下流へ渡す
- CAD Runtime: OCCT / FreeCAD 互換の決定論的実行器
- Validation Service: 幾何、DFM/AM、将来拡張としての組立/FEA 候補の pass/fail と reason code
- Artifact Store / Policy / Audit: hash、保持期間、データ分類、traceability を記録
- Production v2 stubs: static material catalog, decoupled BOM aggregation, AABB assembly interference/separation/adjacency checks

## 現在の成熟度

このリポジトリは Phase 1 PoC と Phase 2 Pilot を検証できるローカル CLI/検証環境です。Production v1/v2 は skeleton/contract として、stdlib API server、Project Service stub、同期 job queue simulation、security/observability tests、CI/SBOM/provenance stubs、静的 material catalog、BOM aggregation、AABB assembly interference stub を追加済みです。Kubernetes、KServe/vLLM、Argo CD、実 worker pool、PLM/ERP/MES adapter、実 FEA、実材料DB、部品ライブラリ、BOM連携は将来拡張です。
