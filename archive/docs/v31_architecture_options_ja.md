# V31 アーキテクチャ候補比較

## 目的

三層総点検後の再出発として、`stationary-autonomous-winding spatial kinetic sculpture object` を本当に閉じられる案だけを比較する。

## 候補

| 案 | 構成 | 長所 | 棄却 / 採用理由 |
| --- | --- | --- | --- |
| A | 低層 motor -> ratchet winding wheel -> spring barrel -> lower compound train -> vertical lift shaft -> elevated V28-derived core | stationary autonomous winding、蓄力、立体駆動、可視性を最小の新規自由度で両立 | **採用**。新規難所を lower power module に閉じ込められる |
| B | motor direct drive -> vertical shaft -> elevated core | 最も簡単 | 棄却。自律駆動はできても「巻き上げる給力機構」の価値を満たさない |
| C | motorized weight rewind -> descending weight train -> canted upper core | 彫刻性が強い | 棄却。机上高さと巻上げ制御の制約が大きく、現時点では検証コストが高い |

## 採用案 A の主張

- external motor が ratchet winding wheel を巻く
- ratchet / one-way clutch が barrel から motor への逆流を遮断する
- slip clutch / current-limit stop が過巻きを防ぐ
- spring barrel output gear が lower compound train を駆動する
- vertical lift shaft が異なる高さへ実トルクを渡す
- elevated core は細密な fast-motion zone として見せる

## 採用案 A の非主張

- watch-grade escapement
- regulating balance
- native CAD animation
- physical endurance
- 最終製品レベルの電子制御

## 次の停止線

この文書だけでは `selected concept` でしかない。  
`feasible selected design` へ上げるには、power / energy / control、tooth-profile、hero-view、DFAM、geometry handoff を別 artifact で閉じる。
