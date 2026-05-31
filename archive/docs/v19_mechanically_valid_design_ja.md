# V19 Mechanically Valid Design

## 目的

V18で見つかった決定的欠陥を、監査だけでなく設計そのものへ反映する。
対象は以下。

- 歯形が丸ピン/角棒で、歯車として成立しない。
- 歯先同士、支持部、クランクが干渉する。
- STEP上で複数solidに分離し、Onshape Assemblyへ正しく挿入できない。

## 設計変更

- 歯形をバックラッシュ付きの台形インボリュート風プロファイルへ変更。
  - 厳密なインボリュートではないが、歯先、歯元、歯面の区別を持つ。
  - 歯根を母体へ0.35 mm重ね、STEP上で単一solid化されるようにした。
- 固定内歯車と遊星ピニオンを上段へ配置。
  - fixed ring: 72T, pitch R54.0 mm, Z38-42
  - orbit pinion: 18T, pitch R13.5 mm, center R40.5 mm, Z37-43
  - 内歯車による遊星ピニオン絶対自転比: -3.0
- 手回しピニオンとケージ駆動歯車を中段へ配置。
  - cage drive: 60T, pitch R45.0 mm, Z25-29
  - hand crank pinion: 18T, pitch R13.5 mm, center distance 58.5 mm, Z24-34
  - 手回し入力比: -3.3333
- ケージの遊星軸支持を下段ボスに整理。
  - 駆動歯車平面を貫通する支持塔を廃止し、手回しピニオンの通過域を空けた。
- 手回しハンドルを固定リングより下に戻した。
  - 軸/ハンドルが固定リング平面を貫かない。
- ケージ表示体を中央スリーブとブリッジで接続。
  - Onshape上で `rotating_cage` が1 solidとして入る。

## 検証結果

実行コマンド:

```powershell
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v19.json check
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v19.json audit
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v19.json motion
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v19.json solid-audit --sample-step-deg 15
```

結果:

- `check`: pass
- `audit`: pass
- `motion`: pass
- `solid-audit --sample-step-deg 15`: pass, failure_count 0

Onshape body count:

- fixed_base: 1 solid
- fixed_ring: 1 solid
- rotating_cage: 1 solid
- orbit_pinion: 1 solid
- hand_crank: 1 solid

Onshape Assembly:

<https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/a50ffc5c9de9cde026cc6ee4>

## 残タスク

V19はSTEP実体としての機械成立性を優先して更新した。
OnshapeネイティブMate/Relationアニメーションはまだ未設定。
次段階では、V19の新しい1-solid部品からMate connector候補を抽出し、Revolute MateとGear Relationを再構築する。
