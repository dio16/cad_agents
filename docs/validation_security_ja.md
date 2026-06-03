# 検証・セキュリティ・法規対応

## Validation Gate

Validation は品質ゲートです。見た目ではなく、仕様一致性と製造可能性を判定します。

| チェック | 内容 |
|---|---|
| `dimensions_check` | 仕様寸法、公差、bbox、volume の一致 |
| `topology_check` | watertight、self-intersection、non-manifold の検出 |
| `unit_consistency` | mm / deg / N / MPa の単位混在検出 |
| `manufacturing_profile_rules` | 壁厚、穴径、overhang、clearance などの DFM/AM 規則 |
| `assembly_interference_check` | 組立干渉、接触、運動範囲の検証 |
| `optional_fea` | 最大変位、応力、固有値などの工学要件 |

不合格時は `reason_code` と `failure_location` を返し、Orchestrator が修正ループに渡します。3回以上の検証失敗は人間判断へエスカレーションします。

## セキュリティ原則

- Prompt Injection、schema escape、code escape をテスト対象にする。
- LLM 出力は JSON Schema / AST validator を通過するまで下流へ渡さない。
- raw code は `allow_raw_code=false` を既定にする。
- CAD Runtime はネットワーク分離サンドボックスで実行する。
- 監査ログは改ざん不能ストレージへ保存する。

## データ分類

| 分類 | ルート |
|---|---|
| `public` | commercial / onprem / hybrid 可 |
| `internal` | policy に従い commercial または hybrid |
| `confidential` | 原則 onprem、例外承認時のみ commercial |
| `regulated` | onprem + human approval 必須 |
| `export-controlled` | onprem + legal/export review 必須 |

## Human Approval Gate

次の条件では人間承認を必須とします。

- 仕様矛盾の解消。
- 仕様変更。
- regulated / export-controlled タグの付与または変更。
- 新規 DSL operation の追加。
- Validation Gate の条件付き override。
- 3回以上の validation failure。
