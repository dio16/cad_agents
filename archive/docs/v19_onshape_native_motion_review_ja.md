# V19 Onshape Native Motion Review

## 対応した残課題

- V19のMate connector計画をマニフェスト化した。
- Onshapeのbodydetailsから実在する円形エッジだけをMate connector参照に使うようにした。
- クリーンなOnshape Assembly `29286d9c8528b2dc3a4ec78a` を再生成した。
- Mate connector 8件、Mate 4件をAPIで作成し、`mate-audit` で全件OKを確認した。
- Onshape UIで `Codex V19 Revolute hand crank` の「合致をアニメート」を開き、360 degの再生が開始できることを確認した。

## 確認結果

- 機械構成としてのV19は、固定リング、回転ケージ、遊星ピニオン、手回しクランクの軸定義が分離されている。
- STEP実体の干渉監査は `solid-audit --sample-step-deg 15` で通過済み。
- Onshape上の拘束は、固定リング-ベースのFastened、ケージ中心Revolute、手回しRevolute、遊星ピニオンRevoluteまで成立した。
- 手回しクランク単体のOnshapeネイティブ回転アニメーションは成立した。

## まだ成立していないこと

Gear Relationによる完全な連動アニメーションは、まだ成立していない。

Onshape UIでGear Relationを1件作成してAPIから読み返した結果、回転自由度の `queryData` は `Rz` であることが分かった。これを `cad_agent/workflow.py` に反映し、今後のAPI生成は `matesQuery.queryData = "Rz"` と `relationLength` を含められるようにした。

ただし、そのUI生成Gear Relation自体がOnshape上でERRORになったため、最終アセンブリには赤フィーチャーを残さず、`create_relations: false` のまま保持している。これは「連動未完成」を見逃さないための明示的なブロック状態である。

ベースをOnshape UIでFixしてから同じGear Relationを再試行したが、ERRORは解消しなかった。このため、原因は単純な未固定Assemblyではなく、選択Mateの組み合わせ、Relation過拘束、またはOnshape側のGear Relation解釈にある。

## 設計スキームへの反映

- `geometry-audit` でMate connector参照の実体と円形種別を先に検査する。
- `mated-assembly --fresh` は、作成前にsolid interferenceとgeometryを必ず通す。
- `mate-audit` は、Relation作成を有効にした場合、必要Relation数がOKにならない限り失敗する。
- Gear RelationのAPIスキーマとして `Rz` を保存し、空の `queryData` でRelationを作ってしまう旧問題を解消した。
- 最終のクリーンAssemblyではベースインスタンスをFixし、赤いGear Relationは残していない。

## 次の判断

V19は「軸拘束と手回し単体アニメーション」まではOnshape上で成立した。美しい連動動作として完成させるには、次はGear RelationのOnshape ERROR原因を潰す必要がある。現時点の候補は、選択Mateの組み合わせ、Relationの過拘束、またはOnshape側のGear Relationがこの多段参照Mate構成を受け付けない可能性である。
