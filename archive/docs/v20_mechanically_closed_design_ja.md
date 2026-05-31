# V20 Mechanically Closed Design

## 目的
V20は、V19の「干渉しない運動モデル」から一段進めて、卓上オブジェとして手回し入力から回転ケージ、遊星ピニオンまで力の流れが追える構成にした設計版である。歯数と運動比はV19を維持しつつ、608ZZ中央ベアリング、3mm軸、軸方向保持、支柱、クリアランスをCAD形状とmanifestへ明示した。

## 主要仕様
- 固定内歯リング: 72T、pitch R54.0 mm、Z38-42
- 遊星ピニオン: 18T、pitch R13.5 mm、center R40.5 mm、絶対自転比 -3.0
- ケージ駆動ギア: 60T、pitch R45.0 mm、Z25-29
- 手回しピニオン: 18T、pitch R13.5 mm、center distance 58.5 mm
- 手回し入力比: hand crank / cage = -3.3333333333333335
- cage poseから見た入力比: input_to_cage_ratio = -0.3

## V20で入れた機械設計改善
- 中央ベアリングは608ZZを前提にし、ベース側にOD 22 mm用ポケット、ケージ側に中央ジャーナルを追加した。
- ケージ駆動ギアは中央ジャーナルへ印刷ウェブで接続した。これにより、手回しピニオンからケージへトルクが伝わる実体経路ができた。
- 遊星ピニオンは3mm軸を前提にし、ケージ側に下段支持、上段リテーナ、上下スペーサを追加した。
- 手回しクランクは3mm軸を前提にし、ベース側支持穴、クランク側ボア、スラストカラーを追加した。
- クランク腕と遊星軸支持柱の動作包絡干渉を避けるため、遊星軸支持柱を上下分割し、Z30-34のクランク腕通過面を空けた。
- 固定リング支持はベース支柱をZ38まで伸ばし、リング下面に印刷座面を追加した。以前の2mm浮きは解消した。
- 手回し軸は上側ブッシュと外側支持ブリッジを追加し、片持ちで噛み合いが逃げる問題を軽減した。
- 608ZZについてはODポケットだけでなく、実内径8mmとケージ中央ジャーナルR3.95のクリアランスをmanifest上の検査対象にした。
- 歯形は6点台形から、丸みを持たせた多点のinvolute-inspiredプロファイルへ変更した。厳密なインボリュートではないが、歯先・歯元の角張りと噛み合い時の干渉リスクを下げる。
- Onshape Mate planは再生成時に消えないよう生成スクリプトへ埋め込み、connector基準も部品の絶対Z位置が一致する円エッジへ更新した。
- 608ZZ、3mm軸2本、M3リング固定ねじ群は市販部品の参照STEPとして生成し、印刷部品とは別のOnshape Assemblyへ挿入した。

## 検証結果
WSL Ubuntu-24.04のCadQuery環境でSTEPを生成し、以下を実行した。

```bash
python scripts/generate_tourbillon_v20_mechanically_closed.py
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json validate
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json check
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json audit
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json motion
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json solid-audit --sample-step-deg 15
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json motion-preview
python cad_agent_cli.py --manifest manifests/tourbillon_v20.json completion-status
```

結果はすべてpass。`solid-audit` は15度刻み360度で `failure_count: 0`。
一度、手回し軸上側支持をX±40mmに置いた版ではクランク腕が135度姿勢で固定ベースに干渉したため、支持柱をX±50mmへ逃がし、再度 `solid-audit` を通している。

## Onshape確認
V20の5 STEPをOnshapeへAPIインポートし、Assemblyへ挿入した。さらに `pose --theta 45` を実行し、運動契約に基づく決定論的transformをOnshape Assemblyへ反映した。

その後、V20専用のMate planを追加し、Onshape mated assemblyを作成した。

- mated assembly: `https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/b314f24d08f8848233fc9d75`
- latest mated assembly: `https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/74bd78f9b92709f38b620900`
- pose snapshots assembly: `https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/677036e90ac35e607ff5a33a`
- standard hardware reference assembly: `https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/71082fad2ecbb26f6b474b06`
- Mate Connector: 8件すべてOK
- Fastened Mate: 1件OK
- Revolute Mate: 3件OK
- Gear Relation: 未作成。V19/V20 probeでは `relationLength` 除去後もOnshape API作成FeatureがERRORになったため、成功条件を確定するまで本番Assemblyには入れない。

Gear Relationによる完全なOnshapeネイティブ連動は未解決である。現時点のV20は「ローカル干渉検証済み、Onshapeインポート済み、Onshape基本Mate検証済み、fallback transform animation検証済み」である。

`completion-status` の判定は以下。

- `local_design_passed`: pass
- `mechanism_audit_passed`: pass
- `motion_contract_passed`: pass
- `solid_interference_passed`: pass
- `onshape_imported`: pass
- `geometry_audit_passed`: pass
- `basic_mates_passed`: pass
- `gear_relation_probe_passed`: blocked
- `fallback_animation_passed`: pass
- `onshape_pose_snapshots_passed`: pass
- `standard_hardware_instantiated`: pass

厳密なステータス文言は `fallback motion verified with Onshape pose snapshots and standard hardware references; native Gear Relation blocked`。

fallback animation:
`reports/tourbillon_v20_mechanically_closed_motion_preview.html`

## 残る設計ゲート
- Onshape imported bodyが意図した単一solidとして入っていることを、bodydetailsで監査する。この問題はV20修正中に検出し、回転ケージを1 solidとして再importできる状態にした。
- Gear Relationは本番Assemblyに赤Featureを残さず、最小probeでschemaと比率向きを確定してから適用する。
- 市販部品の608ZZ、3mm軸、M3ねじは参照solidとしてOnshapeへ挿入済み。ただしnative Gear Relationはまだprobe未通過のため、本番Assemblyには入れない。
