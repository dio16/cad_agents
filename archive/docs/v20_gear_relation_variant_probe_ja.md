# V20 Gear Relation Variant Probe

## 結論

Onshape native Gear Relation は、現時点では `featureStatus: ERROR` のままです。本番 assembly には赤い relation を追加していません。すべて disposable probe assembly で検証しました。

## 実行した候補

| Variant | 変更内容 | 結果 |
| --- | --- | --- |
| `baseline` | `queryData: "Rz"`, ratio expression | `ERROR` |
| `no_query_data` | `queryData: ""` | `ERROR` |
| `ratio_value` | `relationRatio.value` を数値で渡し、expression空 | `ERROR` |
| `ratio_value_expression` | `relationRatio.value` と expression を併記 | `ERROR` |

## 証跡

- `reports/gear_relation_probe_no_query_data.json`
- `reports/gear_relation_probe_ratio_value.json`
- `reports/gear_relation_probe_ratio_value_expression.json`
- `reports/probe_gear_relation_features_latest.json`
- `reports/probe_gear_relation_feature_specs_latest.json`

## 判断

`queryData` と `relationRatio` の渡し方だけでは解決しない可能性が高いです。既存の本番 mated assembly には UI 作成済みの正常な `mateRelation` が存在しないため、API readback 同士だけでは正常 schema 差分を確定できません。

次の合理的な経路は、V20 の完成判定を fallback transform motion + Onshape pose snapshots + basic mates + hardware references として固定し、V21 で hardware-in-context の製造監査へ進めることです。UI で正常な Gear Relation を1つ作成できた場合は、その readback と比較して native relation 実装を再開します。
