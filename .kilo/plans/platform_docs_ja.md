# Platform documentation plan

この計画ファイルは、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` に基づく文書整理結果を記録します。

## 維持対象

- `README.md` / `README_JA.md`
- `GOAL.md`
- `SPEC.md`
- `TASKS.md`
- `AGENTS.md`
- `docs/architecture_ja.md`
- `docs/api_contracts_ja.md`
- `docs/validation_security_ja.md`
- `docs/operations_ja.md`

## 削除対象

旧個別成果物のレビュー文書、運用レポート、成果物README、生成・検証スクリプトは、AI機械設計プラットフォームの原案と目的が異なるため削除しました。

## チェック

`bash ./run_cad_agent.sh validate-docs` で正本文書と runner の整合性を検証します。
