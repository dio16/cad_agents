# API・スキーマ契約

原案: `docs/Origen/Design_document_for_a_machine_design_platform.md`

## エンドポイント

| エンドポイント | 用途 | 同期/非同期 |
|---|---|---|
| `POST /v1/projects` | 案件作成 | 同期 |
| `POST /v1/requirements/extract` | 自然文から Requirement JSON を生成 | 同期 |
| `POST /v1/specifications/generate` | Requirement から Specification JSON を生成 | 同期 |
| `POST /v1/cad/jobs` | CAD 生成ジョブを起動 | 非同期 |
| `GET /v1/cad/jobs/{job_id}` | CAD ジョブ状態を取得 | 同期 |
| `POST /v1/validation/jobs` | 既存 artifact を再検証 | 非同期 |
| `POST /v1/revisions` | Validation failure に基づき修正案を作成 | 非同期 |
| `POST /v1/exports` | STEP/STL/OBJ/PDF 等を出力 | 同期 |
| `GET /v1/artifacts/{artifact_id}` | 成果物を取得 | 同期 |

## Requirement JSON 要点

```json
{
  "traceability_id": "tr_req_001",
  "product_type": "single_part",
  "functional_requirements": ["pipe fixation"],
  "dimensions": {"pipe_outer_diameter_mm": 25},
  "manufacturing": {"primary_process": "FDM"},
  "unknowns": ["allowable displacement"],
  "assumptions": ["desktop FDM printer"]
}
```

## Specification JSON 要点

```json
{
  "traceability_id": "tr_spec_001",
  "requirement_id": "req_001",
  "parameter_table": {"pipe_od_mm": 25.0, "hole_d_mm": 4.3},
  "constraints": ["hole_d_mm >= 4.2"],
  "material_candidates": ["PLA", "PETG"],
  "manufacturing_profile": "fdm_standard",
  "validation_plan": ["dimensions_check", "topology_check", "dfm_am_check"],
  "unresolved_risks": ["service temperature unknown"]
}
```

## Parametric DSL 要点

```json
{
  "traceability_id": "tr_dsl_001",
  "units": "mm",
  "parameters": {"pipe_od": 25.0, "wall_t": 4.0},
  "features": [
    {"op": "extrude", "sketch": "base_profile", "distance": 8.0},
    {"op": "hole_pattern", "count": 2, "diameter": 4.3, "pitch": 42.0}
  ],
  "derivative_outputs": ["step_ap242", "stl", "obj"]
}
```

## Validation Report 要点

```json
{
  "traceability_id": "tr_val_001",
  "specification_id": "spec_001",
  "artifact_ids": ["art_step_001"],
  "dimensions_check": {"status": "pass"},
  "topology_check": {"status": "pass"},
  "unit_consistency": {"status": "pass"},
  "manufacturing_profile_rules": {"status": "pass"},
  "pass": true,
  "failures": []
}
```

## Traceability

全I/O、プロンプト、モデルルート、CAD artifact、Validation Report は同一 generation identity に束ねます。最低限、`traceability_id`、`requirement_id`、`specification_id`、`prompt_version`、`model_route`、`artifact_hash` を記録します。
