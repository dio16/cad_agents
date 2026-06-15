# platform_implementation_ja.md

この文書は、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` に基づく実装ロードマップの索引・要約です。

## 現在の範囲

- Phase 1 PoC: Requirement JSON、Specification JSON、Parametric DSL、Validation Report の JSON Schema、DSL AST、単一部品 golden pipeline、artifact hash index、human approval sample
- Phase 2 Pilot: FreeCAD/OCCT と Blender の native/surrogate probe、DFM/AM profile catalog、review diff HTML、audit JSONL、Model Gateway route trial
- Production v1 / v2: 計画中。API server、auth、queue、worker pool、FEA、PLM/ERP/MES adapter は未実装

## ローカル検証コマンド

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
uv run pytest -q
```

## 実装順序

1. スキーマと AST contract を固定する。
2. 単一部品の PoC pipeline を通す。
3. DFM/AM catalog、review diff、audit、Model Gateway の Pilot contract を通す。
4. Native CAD/render worker が利用可能な環境で surrogate から native へ切り替える。
5. Production v1 で API、認証、非同期ジョブ、sandbox worker、observability を追加する。

## 品質ゲート

- Schema Gate: JSON Schema pass
- AST Gate: Parametric DSL が allowlist、parameter 参照、feature order を通過
- Validation Gate: dimensions、topology proxy、unit consistency、DFM/AM rule が pass
- Compliance Gate: data classification、regulated/export-controlled tag が確定
- Human Approval Gate: 仕様変更、Validation override、regulated/export-controlled、新規 DSL operation は記録必須
