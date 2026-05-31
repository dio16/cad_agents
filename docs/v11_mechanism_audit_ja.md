# V11 Mechanism Audit

## 結論

V11は本当に動くTourbillon機構としては不合格です。
Onshape上で部品姿勢をAPI変換して見せることはできますが、機械拘束、駆動伝達、軸受、歯車転がりの条件を満たしていません。

## 監査結果

`audit`コマンドを追加し、`tourbillon_v11.json`で以下を検証しました。

- Onshape assembly has functional mates: fail
  - Assembly feature count is 0.
  - Revolute Mate、固定、Gear Relationが存在しません。
- hand crank drives the model: fail
  - `hand_crank`にmotion定義がなく、`pose`でも動きません。
- hand crank is mechanically coupled to cage: fail
  - 見た目のロッドは中心へ向かいますが、回転ケージへトルクを伝えるキー、ギア、軸受、Mate Relationがありません。
- orbit pinion internal rolling ratio: fail
  - 固定内歯車内を転がるピニオンの期待自転比は`-center_distance / pinion_pitch_radius = -39.5 / 13.5 = -2.9259`です。
  - V11のmanifestは`-4.0`で、物理的な転がり比と一致しません。
- orbit pinion bore clears cage axle: fail
  - ピニオン穴R2.05 mmに対し、ケージ側軸R2.2 mmで、 nominal clearance は -0.15 mmです。
  - 3Dプリントで自由回転する軸受として成立しません。

## 機械として成立させるためのV12必須条件

- Onshape Assemblyに最低限の合致を作る。
  - Base and fixed ring: fixed
  - Cage around central post: revolute
  - Orbit pinion around cage axle: revolute
  - Driver crank/drive gear: revolute
  - Pinion/ring relation or surrogate gear relation: verified ratio
- クランクを飾りではなく駆動源にする。
  - 手回しノブ、入力軸、ピニオン、ケージ駆動ギアのいずれかを実体接続する。
- 軸受クリアランスを設計値に入れる。
  - FDM想定なら半径方向0.25から0.4 mm程度を最小値にする。
- 歯車比を転がり式に合わせる。
  - 固定内歯車内を公転するピニオンは、現状寸法なら自転比を約-2.926にする。
  - 24T/96Tを使うなら、pitch radiusとcenter distanceも整合させる。
- Balance wheelとescape wheelを単なる表示部品から機構要素へ昇格する。
  - 少なくともケージ上の軸に対する独立回転と、見える連動関係を定義する。

## 判定

V11は「機構鑑賞用の静的/疑似運動モック」としては改善しています。
ただし「本当に動くTourbillon機構」ではありません。
次の設計改善は、見た目の装飾ではなく、Mate Connectorと軸受・歯車列の成立を最優先にします。
