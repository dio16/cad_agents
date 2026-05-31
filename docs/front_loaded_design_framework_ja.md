# 先行成立性設計フレームワーク（正本）

## 目的

重い 3D 出力を「探索」ではなく「確認」に使うため、CAD 前に成立する案を選び切る。  
進め方は `成立する設計案の検討 -> 実装 -> 確認` とし、`設計 -> 3D 検証 -> 是正` の高コスト反復を常態化させない。

## 原則

1. **高価な検証ほど後ろへ送る前に安価な否定を済ませる。**
2. **成果物が大きいほど、CAD 前の設計証拠を厚くする。**
3. **案の数を増やすのは前段、geometry の数を増やすのは最後。**
4. **3D 検証は未知の発見より、既に選んだ仮説の確認に使う。**
5. **局所 3D 試験を使う場合も、shape exploration に戻さない。** 各モジュールは learning objective、pass criterion、non-claim を持つ。

## 規模別の設計投資

| 出力規模 | CAD 前に必須 | CAD で許す探索 |
| --- | --- | --- |
| 小 | 要求カード、1 案、寸法 sanity、失敗条件 | 局所形状 |
| 中 | 2-3 案比較、伝達経路、部品境界、寸法 budget、主要 failure review | 接続部の微調整 |
| 大 | value brief、3 案以上、選定表、運動グラフ、力の流れ、空間配置、標準部品、製造/組立、hero view、pre-mortem | ほぼ確認のみ |

## 標準フロー

### 0. 要件固定

- 何を作るか
- 何を価値とするか
- 何を名乗り、何を名乗らないか
- どの検証が最も高価か

### 1. 案の発散

最低 3 案を、3D ではなく図・表・伝達グラフで作る。

- 力の入力と出力
- 軸、面、高さの使い方
- 見せ場の位置
- 標準部品の前提
- 予想される弱点

### 1.5 50 観点成立性スイープ

設計案を外へ出す前に、main agent は各候補案について **内部で 50 観点の成立性反証** を回す。  
これは長い思考過程をそのまま公開するためではなく、安易な案を早期に落とすための義務である。

- 50 観点は `機構 / 支持 / 伝達 / 給力 / 製造 / 組立 / 視認 / 検証 / claim / 再利用性` に配分する。
- 出力するのは長い思考列ではなく、`50-point feasibility sweep` artifact の pass / fail / residual-risk 要約である。
- 1 つでも load-bearing な fail が残る案は、要求定義や geometry contract に進めない。
- 大規模出力では、選定案だけでなく棄却案にも少なくとも fail reason を残す。

### 2. 案の安価な否定

各案に対し、CAD 前に次を潰す。

- 運動連鎖の閉包
- ratio / tooth / center-distance の一次整合
- 支持、軸受、保持
- 自律給力入力の成立
- 立体駆動の必然
- DFAM / 組立 / メンテナンス
- hero view での可読性
- 最も起こりそうな 5 失敗

### 3. 選定

選定表は、少なくとも次を含む。

| 項目 | 例 |
| --- | --- |
| 機構成立性 | 伝達閉包、支持、トルク、比率 |
| 価値一致 | 彫刻性、精緻さ、立体性、楽しさ |
| 製造性 | 印刷、標準部品、組立 |
| 検証負荷 | 重い 3D 反復をどれだけ減らせるか |
| リスク | 新規難所、未知の接触、後戻り |

### 4. 設計案パッケージ

CAD 前に 1 つの設計案へ次を揃える。

- value brief
- claim / non-claim
- motion graph
- spatial-drive map
- dimension budget
- component / hardware list
- failure-mode review
- gate matrix
- 50-point feasibility sweep summary
- 受け入れられなかった案と棄却理由

### 5. システム境界の閉包

大規模な複数モジュール機構では、full CAD 前にさらに 1 段置く。

- module input / output
- handoff axis / frame / centerline
- reserved envelope
- keep-out / contact zone
- hero-view occlusion budget
- assembly order dependency

個別モジュールが成立しても、ここが閉じていなければ full CAD へ進まない。

### 6. 選定案の成立性閉包

ここまでで案が美しく整っていても、まだ「成立済み」とは呼ばない。  
full CAD 前に、少なくとも次を **数値または判定可能な契約** で閉じる。

- power / torque / energy budget
- winding control、clutch、end-stop、overwind 対策
- tooth-profile viability（undercut、tip/root clearance、必要なら profile shift）
- quantitative hero-view legibility / occlusion
- moving-role support、retention、tool access、print orientation

この段階を通過して初めて、`selected concept` ではなく `feasible selected design` と呼ぶ。

状態名は次のように使い分ける。

- `selected concept`: 価値・構成・運動の筋が通った案
- `feasible selected design`: 上記に加え、成立性閉包が pass した案
- `geometry-ready`: `feasible selected design` を落とさず geometry contract へ写し切り、その handoff gate も pass した案

### 7. 実装

設計案パッケージ、成立性閉包、geometry-contract handoff が pass してから manifest と CAD を作る。  
CAD 中の変更は、前段の前提を壊す場合のみ設計案へ戻して再審査する。

### 8. 確認

3D 検証では、案で宣言したことだけを確認する。

- geometry
- motion
- visibility
- object value
- fabrication package

## ループ削減ルール

1. 出力が 2 倍重くなる時、CAD 前の比較項目も増やす。逆にはしない。
2. 同じ種類の 3D 修正が 2 回出たら、次回は pre-CAD checklist へ昇格する。
3. 「まず作ってみる」は、小規模局所試験に限る。大物全体では禁止。
4. 選定前に 3D を起こしたくなったら、まずその欲求を 2D / 数表 / motion graph で代替できないか確認する。
5. 小さな 3D モジュールを切り出す時は、その試験が **何の不確実性を消すか** を先に書く。役割・通過条件・非主張を持たない試験片は、full CAD 前進の証拠に数えない。
6. load-bearing な non-claim（例: torque reserve 未証明、clutch 未設計）が残る risky subsystem は、概念可視化としては許すが geometry readiness の証拠に数えない。
