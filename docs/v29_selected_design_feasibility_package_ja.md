# V29 Selected Design Feasibility Package

## 結論

V29 は、architecture が整っただけの状態から一段進み、  
full CAD 前に次の 4 点を閉じて初めて `feasible selected design` と呼ぶ。

1. power / torque / energy / control
2. tooth-profile viability
3. quantitative hero-view layout
4. pre-CAD buildability

## 1. Power-path closure

- motor family: 20D metal gearmotor
- winding stage: 18T -> 108T, module 0.8, ideal torque ratio 6:1
- storage candidate: torsion spring barrel
- working band: 200-800 Nmm
- target holdover: 60 s
- control: one-way ratchet + low/high angle sensing + slip clutch

## 2. Tooth-profile closure

- external pinions are no smaller than 18T at 20°
- the old 12T pinion path is rejected before geometry
- speed ratio and torque ratio are kept as different fields
- internal ring / orbit relation uses carrier-relative spin semantics

## 3. Hero-view closure

- slow macro / medium transfer / fast fine are all visible in the same hero view
- module overlap is bounded before CAD
- the force path is readable through three explicit projected regions

## 4. Buildability closure

- main loaded roles have support, retention, print orientation, and tool access declared
- assembly order is explicit before sculpture surfacing begins

## 5. この段階でまだ主張しないこと

- final tooth clearance
- physical torque measurement
- printer-specific fit
- endurance / wear

これらは後段 gate で確認する。  
ただし、ここまで閉じないまま full CAD へ進むことは禁止する。
