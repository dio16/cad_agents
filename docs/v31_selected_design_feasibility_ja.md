# V31 selected-design feasibility closure

## Power / energy

- 入力: 外部給電 gearmotor family
- 巻上げ側: motor pinion -> ratchet winding wheel
- 蓄力側: spring barrel
- 出力側: spring barrel output gear -> compound transfer -> vertical lift shaft
- 逆流遮断: ratchet / one-way clutch を winding wheel と barrel 間に置く
- 過巻防止: motor 側に **slip clutch** を採用し、release torque を 0.45 N·m とする

一次 budget:

| 項目 | 仮定 |
| --- | --- |
| motor-side available torque | 0.40 N·m 以上 |
| required carrier-side torque | 0.03 N·m 以下 |
| winding reserve target | 5x 以上 |
| holdover target | 30 s 以上 |
| visible drum speed | slow macro |
| transfer shaft speed | medium |
| escapement display | fast fine |

## Gear / support

- new lower-train pinions are kept at 18T 以上
- all new meshes remain spur meshes on parallel axes
- backlash target: FDM assumption 0.25 mm equivalent running allowance
- 20° involute の minimum no-undercut threshold を 17T とし、全 pinion はこれを上回る
- tip/root clearance は各 lower-train mesh で 0.20 mm 以上を確保し、profile shift は不要
- lower train uses two-point supports on winding arbor and lift shaft
- vertical lift shaft uses lower bridge + upper deck seats
- winding arbor / spring barrel axis / vertical lift shaft は 3 mm shaft、2 点支持、washer + collar による axial retention を持つ

## Hero-view / DFAM

- large winding wheel remains below and forward
- vertical shaft remains visible as the spatial transition
- upper core remains open from the front hero view
- lower bridge, upper deck, and service openings preserve tool access
- flat decks / vertical shafts keep print orientation legible

## Residual risk

- final print clearances
- slip-clutch 摩擦材の実機係数

load-bearing な未知は geometry-ready 前に contract 化した。残るものは物理試作時の実機係数と最終クリアランスであり、CAD で初めて決める前提ではない。
