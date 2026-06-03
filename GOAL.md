# Repository Goal

## 目的

このリポジトリの目的は、[`docs/Origen/Design_document_for_a_machine_design_platform.md`](docs/Origen/Design_document_for_a_machine_design_platform.md) を原案として、AI活用機械設計プラットフォームの仕様、運用規則、検証ゲート、実装ロードマップを一貫した形で管理することです。

## 成功状態

次の状態を成功とします。

- 自由文の設計意図を `Requirement JSON` に構造化できる。
- `Requirement JSON` から、人間承認可能な `Specification JSON` を生成できる。
- `Specification JSON` から、任意コードではなく `Parametric DSL` を生成する。
- DSL は AST/schema validator を通過するまで CAD Runtime に渡さない。
- CAD Runtime は OCCT / FreeCAD 系の決定論的実行器として、STEP AP242 / B-Rep を正本にし、STL / OBJ / glTF / PNG / PDF を派生物として生成する。
- Validation は寸法、トポロジ、単位、DFM/AM、組立干渉、必要に応じた FEA を pass/fail と reason code で報告する。
- すべての生成物に `traceability_id`、要件ID、仕様ID、モデルルート、プロンプト版、artifact hash を保持する。
- 仕様変更、regulated / export-controlled 案件、新規 DSL operation は人間承認ゲートを必須にする。

## 非目的

- LLM が自由形式 Python、FreeCAD macro、shell script を直接生成して実行すること。
- 検証不合格を合格扱いに書き換えること。
- 仕様矛盾をエージェントが独断で解消すること。
- 旧個別成果物の継続生成・検証を、このリポジトリの中心目的として維持すること。

## 優先順位

1. **スキーマ契約**: Requirement / Specification / DSL / Validation Report の JSON Schema を固定する。
2. **責任分離**: LLM、CAD Runtime、Validation、Human Approval の境界を明文化する。
3. **安全な実行**: raw code を既定禁止し、CAD Runtime をサンドボックス化する。
4. **監査可能性**: traceability と不変ログを全工程に付与する。
5. **段階導入**: PoC → Pilot → Production v1 → Production v2 の順に拡張する。
