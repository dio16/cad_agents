# platform_implementation_ja.md

この文書は、原案 `docs/Origen/Design_document_for_a_machine_design_platform.md` に基づく実装ロードマップの索引・要約です。

## 現在の範囲

- Phase 1 PoC: Requirement JSON、Specification JSON、Parametric DSL、Validation Report の JSON Schema、DSL AST、単一部品 golden pipeline、artifact hash index、human approval sample
- Phase 2 Pilot: FreeCAD/OCCT と Blender の executable probe、DFM/AM profile catalog、review diff HTML、audit JSONL、Model Gateway route trial
- Production v1 skeleton: API server、Project Service、同期 job queue simulation、security/observability tests、CI/SBOM/provenance stubs を追加済み。
- Production v2 stub: 静的 material catalog、BOM aggregation、AABB assembly interference/separation/adjacency を Phase 1/2 pipeline から分離して追加済み。
- Deferred: Kubernetes、KServe/vLLM、Argo CD、Cosign/Trivy、実 worker pool、実 LLM endpoints、PLM/ERP/MES adapter、実材料DB、部品ライブラリ、BOM連携、接触/運動/FEA。

## ローカル検証コマンド

```bash
bash ./run_cad_agent.sh status
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh phase1-contract-test
bash ./run_cad_agent.sh phase1-golden-pipeline
bash ./run_cad_agent.sh phase2-pilot-run
bash ./run_cad_agent.sh serve --dry-run
bash ./run_cad_agent.sh sbom --output /tmp/cad_agent_sbom.json
bash ./run_cad_agent.sh provenance --output /tmp/cad_agent_provenance.json
uv run pytest -q
```

## 実装順序

1. スキーマと AST contract を固定する。
2. 単一部品の PoC pipeline を通す。
3. DFM/AM catalog、review diff、audit、Model Gateway の Pilot contract を通す。
4. Native CAD/render worker の executable を probe して記録する。存在しない場合は deterministic surrogate adapter を使う。PoC/Pilot の contract は surrogate から native への切替を前提としない。
5. Production v1 で API、認証、非同期ジョブ、sandbox worker、observability を追加する。

## 品質ゲート

- Schema Gate: JSON Schema pass
- AST Gate: Parametric DSL が allowlist、parameter 参照、feature order を通過
- Validation Gate: dimensions、topology proxy、unit consistency、DFM/AM rule が pass
- Compliance Gate: data classification、regulated/export-controlled tag が確定
- Human Approval Gate: 仕様変更、Validation override、regulated/export-controlled、新規 DSL operation は記録必須
