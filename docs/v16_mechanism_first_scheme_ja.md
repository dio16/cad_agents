# V16 Mechanism-First Scheme

## 変えた設計スキーム

従来は、CAD形状を作ってから動作を見て、問題を形状に戻す流れでした。
この方法では、見た目だけ成立した部品を作りやすく、機械としての成立性が後追いになります。

V16では順序を逆にしました。

1. Tourbillon機能を機構グラフとして定義する。
2. 市販部品を先に選ぶ。
3. 軸、ベアリング、ギア節点、ピッチ半径、回転比を数式で固定する。
4. その設計グラフからCADとmanifestを生成する。
5. CADをOnshapeへ投入し、API姿勢変更で確認する。

このため、形状は設計の起点ではなく、機構仕様の出力物です。

## V16機構グラフ

- ground
  - fixed base
  - fixed internal ring
- cage
  - central revolute axis at `[0, 0]`
  - central bearing: 608ZZ
  - external drive gear: pitch R44, 88T
- hand_crank
  - revolute axis at `[0, -55]`
  - bearing: 623ZZ
  - drive pinion: pitch R11, 22T
  - cage drive ratio: `-44 / 11 = -4.0`
- orbit_pinion
  - carried by cage at radius 44 mm
  - bearing: 623ZZ pair
  - pitch R14, 28T
  - fixed ring pitch R58, 116T
  - internal rolling ratio: `-44 / 14 = -3.1429`
- escapement_display
  - carried by cage
  - used as a visible tourbillon display module

## 標準部品

- 608ZZ bearing, 8 x 22 x 7 mm, 1 pc
- 623ZZ bearing, 3 x 10 x 4 mm, 3 pcs
- 3 mm precision round shaft, 3 pcs
- M8 shoulder bolt or 8 mm shaft, 1 pc
- M3 socket head screws, 12 pcs

## 検証結果

- `validate`: pass
- `check`: pass
- `audit`: pass
- Onshape API import: done
- Onshape Assembly: done
- `pose --theta 120`: done
- In-app browser visual inspection: done

## V16 Onshape Assembly

https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/4ec4652f29b90ba4f3b4a3e8

## 残る限界

Onshape上の合致フィーチャーはまだ0です。
公式Onshape Assembly APIはAssembly作成、Instance挿入、Transform変更、Mate/Mate Connector作成に対応しています。
ただしMate ConnectorをImported STEPの正しい円筒面へ確実に置くには、body detailsから安定した面IDを拾い、機構グラフ上の軸と対応付ける実装が必要です。

V16で完成したのは、物理設計スキームと機構グラフに基づく卓上Tourbillonオブジェクトです。
次段階は、この同じ機構グラフからOnshape Mate ConnectorとRevolute/Gear Relationを自動生成することです。
