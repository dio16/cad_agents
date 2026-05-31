# V30 機械成立優先アーキテクチャ

## 目的

V29 の false-positive を踏まえ、まず **実体軸・支持・噛み合い・力伝達** を持つ案だけを残す。

## 候補比較

| 案 | 概要 | 判定 |
| --- | --- | --- |
| A | 下段の自律巻上げモジュールから、実体の vertical lift shaft で上段の V28 機構へ給力する二層案 | 採用 |
| B | V29 のように bevel riser + canted cage まで一気に行う案 | 棄却。立体性は高いが、歯形・軸交差・支持の未知が多く、前回の失敗を再発しやすい |
| C | V28 を自動化するだけの完全平面案 | 棄却。機械成立は近いが、立体駆動価値を満たさない |

## 採用案 A

### 力の流れ

`motor pinion -> visible winding drum gear -> spring barrel output gear -> lower transfer pinion -> vertical lift shaft -> upper transfer pinion -> carrier drive gear -> internal ring / orbit pinion -> escape -> pallet -> balance`

### なぜ成立しやすいか

1. 時計側は、すでに geometry-derived gate を通した V28 機構を再利用できる。
2. 新規リスクは `低層給力モジュール` と `vertical lift shaft` に限定される。
3. 立体駆動は、異なる高さをまたぐ実在の軸伝達で満たす。
4. 軸方向を変える bevel gear を使わず、まずは確実に機械成立を取り戻せる。

### 必須の実体

- motor output shaft
- winding arbor
- spring barrel output axis
- vertical lift shaft
- upper transfer pinion
- V28 由来の carrier / orbit / escapement axes
- lower support seats
- upper deck / columns

### 非主張

- watch-grade escapement
- native CAD animation
- physical endurance
- bevel / canted display

## 50 観点スイープ後の採用理由

- load-bearing fail を 0 件にできる最小案である
- spatial-drive の要件を、最も少ない新規自由度で満たす
- 失敗時に再利用可能な切り分けがしやすい
- V29 の失敗を正面から回避する
