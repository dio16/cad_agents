# V29 Pre-CAD Feasibility Package

## 0. 前提と claim

### 目標

- 全体: 大胆なキネティック・スカルプチャー
- 細部: 時計のような精緻さ
- 入力: 見える自律給力機構
- 価値: 平面時計の拡大ではなく、立体空間で力が移ること

### 現時点の限定語

- 卓上で静止したまま、低電圧外部電源を用いて自律的に巻き上がる給力機構を採用する。
- `autonomous winding` は、低電圧モータ / 巻上げ列 / 蓄力 / 出力経路を持つ機構 claim とし、物理試作での実効巻上げ量と寿命は別 gate とする。
- watch-grade 調速、自己持続振動、時間精度は別 claim とする。

## 1. Value brief

| 距離 | 体験 |
| --- | --- |
| 遠景 | 大きな winding drum と傾斜した cage が、机上彫刻としてまず目を引く |
| 中景 | winding drum → storage → 空間伝達 → carrier → escapement の因果が読める |
| 近景 | pallet / balance / fine gears が薄く細かく動き、時計的な報酬がある |

## 2. 候補案

### A. Visible winding drum + powered winding train + bevel riser + canted cage

- 大きな後方 winding drum が主役
- 低電圧ギヤードモータが巻上げ列を周期駆動
- 水平軸から bevel gear で高さ方向へトルクを持ち上げる
- tourbillon cage は 25-35° 傾斜

### B. Peripheral powered ring + stacked transfer tower

- 外周 powered ring が周囲を回る
- 周辺から中心へ複数段 gear で伝達
- 高さ方向は tower で稼ぐ

### C. Twin powered side drums + differential bridge + suspended cage

- 左右 2 つの powered drum を differential で束ねる
- cage を上部に吊る
- 立体性は最も強いが、部品数と不確実性が大きい

## 3. 比較表

| 観点 | A | B | C |
| --- | --- | --- | --- |
| 遠景の強さ | ◎ | ○ | ◎ |
| 運動可読性 | ◎ | ○ | △ |
| 立体駆動の必然 | ◎ | ○ | ◎ |
| 時計的精緻さとの対比 | ◎ | ○ | ○ |
| 機構成立性 | ○ | ○ | △ |
| DFAM / 組立 | ○ | ○ | △ |
| 高価な後戻りリスク | 低 | 中 | 高 |
| 採否 | **採用** | 棄却 | 棄却 |

## 4. 採用案 A の motion graph

```text
low-voltage gearmotor
  -> visible winding drum
  -> winding train
  -> spring barrel / energy storage
  -> horizontal transfer shaft
  -> bevel riser
  -> elevated carrier drive
  -> fixed ring / orbit pinion
  -> escape wheel
  -> pallet
  -> balance
```

## 5. Spatial-drive map

1. winding drum の大運動は背面縦面で見せる
2. 低電圧 motor は巻上げ側に置き、力の流れは drum / barrel で見せる
3. 蓄力後の水平伝達を bevel riser で上方へ折り返す
4. 傾斜 carrier 内で微細な時計運動へ解像度を上げる

これにより、力の流れは単なる積層でなく、**面を変え、軸を変え、視線も移す**。

## 6. 一次寸法 budget

| サブシステム | 予備条件 |
| --- | --- |
| winding drum | 全体 silhouette の 35-45% を占める大型可視質量 |
| power module | 低電圧ギヤードモータ + 巻上げ列 + clutch / limit 相当 |
| riser | 1 組の bevel / crown equivalent で明確な axis transition |
| carrier | rotor より小さく、escape / balance が覆われない開放 cage |
| fast-fine zone | balance / pallet / escape は hero view で occlusion されない |

## 7. 先行 failure pre-mortem

1. winding drum が大きすぎて他の見せ場を消す  
   → hero-view area budget を置く
2. bevel riser が gimmick 化し、実際の力伝達が曖昧になる  
   → force-path contract と axis-transition gate を必須化
3. cage の傾斜が増えすぎて支持と組立が難化する  
   → 30° 近傍を初期案、支持 span を先に閉じる
4. 自律給力 claim が見た目だけになる  
   → motor / winding train / storage / output の物理 contract を要求
5. 高速微小部が再び覆われる  
   → openness / occlusion budget を concept 時点から持つ

## 8. Pre-CAD go / no-go

### Go

- A 案が、価値 brief、motion graph、spatial-drive map、一次寸法、支持構想、DFAM の全てで重大矛盾なし
- B / C を採らない理由が記録済み

### No-go

- 低電圧 motor を許容しない場合
- 立体駆動を 1 回以上入れずに同等価値を名乗ろうとする場合
- hero view で winding drum 以外の主要 motion が読めない場合

## 9. 次の contract に渡すべき項目

1. low-voltage motor / visible winding drum / winding train / storage barrel
2. horizontal transfer shaft
3. bevel riser
4. canted carrier
5. open cage geometry
6. autonomous-winding evidence plan
7. spatial-drive evidence plan
8. kinetic-object evidence plan
