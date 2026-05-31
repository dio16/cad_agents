# V18 Solid Interference Gate

## 判断

V18はトゥールビヨン機構として不合格。
以前の設計スキームは、ピッチ円距離とMate状態だけを確認していたため、歯先・ピン歯・支持塔・クランク軸などの実体干渉を検出できなかった。

## 根本原因

1. `gear_mesh` がピッチ円の一致だけを見ていた。
   ピッチ円が一致しても、実体歯のaddendum、歯幅、ピン半径、位相、Z重なりを見なければ、歯同士の衝突は検出できない。
2. `geometry-audit` はMate connectorの参照形状が存在するかだけを見ていた。
   これはAssembly拘束用の監査であり、部品同士がぶつからないことの証明ではない。
3. Onshape投入を受け入れゲートにしていた。
   機械成立性はOnshape投入前にSTEP実体で落とすべきだった。

## 実装した改善

`solid-audit` コマンドを追加した。

```powershell
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v18.json solid-audit --sample-step-deg 90
```

この監査は各STEPをCadQuery/OpenCascadeで読み込み、姿勢サンプルごとに部品ペアのブーリアン交差体積を計算する。
交差体積が `0.01 mm^3` を超える場合は失敗とする。

また、`mated-assembly` はOnshape Assemblyを作る前に `solid-audit` を必ず実行する。
したがって、V18のように実体干渉を含む設計はOnshape拘束工程へ進めない。

## V18の検出結果

`solid-audit --sample-step-deg 90` の結果は `fail`。
主な失敗:

- `fixed_base` × `rotating_cage`: 2643.713 mm^3
- `fixed_base` × `hand_crank`: 1519.102 mm^3
- `fixed_ring` × `orbit_pinion`: 539.505 mm^3
- `rotating_cage` × `orbit_pinion`: 520.661 mm^3
- `rotating_cage` × `hand_crank`: 23.461 mm^3
- `fixed_ring` × `hand_crank`: 7.069 mm^3

これはユーザー指摘どおり、V18が機械設計として成立していないことを意味する。

## 新しい受け入れ順序

1. `check`
2. `audit`
3. `motion`
4. `solid-audit`
5. `geometry-audit`
6. `mated-assembly`
7. `mate-audit`
8. Onshape UIでAnimate確認

`solid-audit` が通らない限り、Onshape上でMateやRelationを作っても完成扱いにしない。
