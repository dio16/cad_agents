# CAD Agents: AI機械設計プラットフォーム

このリポジトリは、生成AIを使った機械設計プラットフォームの設計・実装準備リポジトリです。原案は [`docs/Origen/Design_document_for_a_machine_design_platform.md`](docs/Origen/Design_document_for_a_machine_design_platform.md) であり、維持対象のドキュメントとスクリプトはこの原案に合わせて整理されています。

## 中核方針

自由文を直接 CAD コードに変換しません。必ず次の境界を通します。

1. 人間の設計意図
2. `Requirement JSON`
3. `Specification JSON`
4. スキーマ検証済み `Parametric DSL`
5. OCCT / FreeCAD 系の決定論的 CAD Runtime
6. 幾何、DFM/AM、組立、必要に応じた FEA の Validation Report
7. STEP AP242、STL、OBJ、glTF、PNG、PDF などの版管理成果物

LLM は設計計画器、CAD カーネルは実行器、検証器は品質ゲートです。

## 正本文書

| ファイル | 目的 |
|---|---|
| [`GOAL.md`](GOAL.md) | リポジトリの目的、非目的、受入条件 |
| [`SPEC.md`](SPEC.md) | アーキテクチャとデータ契約 |
| [`TASKS.md`](TASKS.md) | 原案ベースの実装ロードマップ |
| [`AGENTS.md`](AGENTS.md) | エージェント責任境界と安全ルール |
| [`docs/architecture_ja.md`](docs/architecture_ja.md) | アーキテクチャ要約 |
| [`docs/api_contracts_ja.md`](docs/api_contracts_ja.md) | API、スキーマ、traceability 契約 |
| [`docs/validation_security_ja.md`](docs/validation_security_ja.md) | 検証、監査、セキュリティゲート |
| [`docs/operations_ja.md`](docs/operations_ja.md) | CI/CD、ランタイム、運用モデル |

旧トゥールビヨン個別成果物向けのドキュメントとスクリプトは、原案と無関係なため削除しました。

## チェック実行

```bash
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh status
```

`run_cad_agent.sh` は、プラットフォーム文書チェック、Phase 1 PoC の contract/golden pipeline、Phase 2 Pilot 検証を提供します。Phase 1 PoC は Requirement JSON、Specification JSON、Parametric DSL AST、決定論的 STEP/STL 生成、Validation Report、artifact hash index、Human Approval Gate 記録を検証します。Phase 2 Pilot は FreeCAD/OCCT と Blender の adapter probe、DFM/AM profile catalog、review diff HTML、audit retention/data classification、Model Gateway ルート判定を検証します。

## ライセンス

Apache-2.0。詳細は [`LICENSE`](LICENSE) を参照してください。
