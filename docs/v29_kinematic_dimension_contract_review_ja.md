# V29 Kinematic Dimension Contract Review

## 目的

full CAD 前に、V29 の運動骨格を **数値で** 閉じる。  
ここでは美しい形より先に、歯数、比率、中心距離、backlash、支持スパンを決める。

## 初期採用値

| Mesh | 初期値 |
| --- | --- |
| motor -> winding drum | 18T -> 108T, module 0.8, 6:1 減速 |
| barrel -> transfer | 36T -> 18T |
| horizontal -> vertical riser | 20T -> 20T bevel equivalent |
| riser -> carrier | 18T -> 54T |
| fixed ring -> orbit pinion | internal 72T -> 18T、carrier に対する絶対 spin ratio は -3.0 |

## 支持前提

- 主要 shaft は 3 mm
- drum / transfer / riser / carrier はすべて二点支持
- printed bore の一次 clearance は radial 0.20 mm
- canted carrier は 18 mm の初期支持スパンから始める

## まだ確定しないもの

- 実トルク
- tooth clearance の sampled 検証
- 最終 backlash の printer 依存調整
- barrel / clutch の最終構造

## ここで得る価値

CAD に入る前に、

1. 目で追える遅い大運動
2. 立体遷移を担う中速伝達
3. tourbillon らしい細かい回転関係

が、互いに矛盾しない first-pass 数値として存在する。
