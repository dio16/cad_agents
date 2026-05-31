# V18 Onshape Mate API Review

## 目的

V18をOnshape上で「見た目の部品配置」ではなく、Assembly Mateで機械的な自由度を持つモデルとして検証する。
最終確認で初めて不成立が見つかる状態を避けるため、CAD投入前とAssembly生成直後にAPI監査を挟む。

## 確認結果

- 旧Mated Assembly: `be5bc64f2a46927c56d97d81`
  - インスタンス5件、合致フィーチャー19件。
  - Mate connector 8件とMate 4件はOK。
  - Gear relationとRelation probeはOnshape上でERROR。
  - Onshape UI上で `Codex Revolute hand crank` のAnimateダイアログは開けたため、Revolute Mateの回転自由度自体は認識されている。
- 新Clean Mated Assembly: `d06eca291d4b92e8e6634fa4`
  - URL: <https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/d06eca291d4b92e8e6634fa4>
  - インスタンス5件、合致フィーチャー12件。
  - Mate connector 8件とMate 4件は `mate-audit` で全件OK。
  - Gear relationは未作成。Onshape APIでのRelation schemaが確定するまで、最終モデルにERRORフィーチャーを混ぜない。

## 根本原因

1. STEPインポート後のbody選択を最終Assembly生成まで検証していなかった。
   `rotating_cage` のように複数bodyを持つSTEPでは、正しい `partId` を選ばないと軸や歯車が成立しない。
2. Onshape APIのレスポンス成功を、Feature作成成功と同一視していた。
   `addAssemblyFeature` が返っても、`featureState.featureStatus` がERRORになるケースがある。
3. Gear relationのAPI schemaが未確定な段階で、実験用Relationを本番Assemblyに投入していた。
   結果として、軸拘束の可否とGear relationの失敗が同じ最終確認画面で混ざって見えていた。

## 設計スキーム改善

- `geometry-audit` を追加した。
  - `getBodyDetails` で、各roleが選択している `partId` のedge/face数を確認する。
  - Mate connectorに使う `deterministic_id` が実在し、円エッジまたは円筒面であることを確認する。
- `mated-assembly` はAssembly生成前に必ず `geometry-audit` を実行する。
  - ここで失敗した場合、Mate作成へ進まない。
- `mated-assembly --fresh` を追加した。
  - 既存のERROR Relationが混ざったAssemblyではなく、クリーンな検証用Assemblyを作る。
- Gear relation作成は `create_relations: false` を既定にした。
  - Relation schemaがAPIで検証できるまでは、検証ステータスを `blocked` として明示する。
  - 失敗するRelationを最終Assemblyへ入れない。
- `mate-audit` を受け入れ基準として維持する。
  - Mate connector / Mate / RelationのFeature stateをOnshapeから読み戻して判定する。

## 現在の成立範囲

- 成立:
  - 正しいbodyを使ったOnshape Assembly生成。
  - Mate connector 8件。
  - Fastened Mate 1件。
  - Revolute Mate 3件。
  - Onshape UI上で回転MateのAnimate対象が見えること。
- 未成立:
  - OnshapeネイティブGear relationによる完全な連動アニメーション。
  - これはV18の機械設計が完全成立したという意味ではなく、Relation API schemaの確定待ちとして分離した状態。

## 実行コマンド

```powershell
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v18.json geometry-audit
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v18.json mated-assembly --fresh
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v18.json mate-audit
```

## 次の判断

次の改善は、Onshape UIで手作成したGear relationを1件だけ作り、`Assembly/getFeatures` で正しい `mateRelation` JSONを回収すること。
そのschemaをワークフローへ反映できた時点で、`create_relations: true` に戻し、Gear relation込みの `mate-audit` を最終受け入れ条件にする。
