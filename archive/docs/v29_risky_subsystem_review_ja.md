# V29 Risky Subsystem Review

## 目的

full sculpture geometry に進む前に、V29 の高価な未知を 3 つの局所モジュールへ分解して先に潰す。

## 今回の 3 モジュール

| Module | 先に潰す未知 | 今回の到達 |
| --- | --- | --- |
| autonomous power module | hidden motor / visible macro motion / storage / output を分離できるか | 役割を分けた concept geometry を契約化 |
| spatial riser | 平面外へ力を本当に持ち上げられるか | 低い入力軸と高い出力軸を持つ concept geometry を契約化 |
| canted cage sightline | 傾けても fine-motion zone を開けておけるか | 30° の bounded tilt と開放 envelope を持つ concept geometry を契約化 |

## この段階で証明すること

1. full CAD 前に、重い未知が shape-only でなく **learning objective** として定義されている。
2. 各モジュールに required role、pass criterion、non-claim がある。
3. `STEP` / `STL` / contact sheet / review report が同一パッケージで揃う。

## この段階でまだ証明しないこと

- full assembly の比率・トルク・寿命
- 最終 cage 支持剛性
- fabrication complete
- 最終 object-value pass

## 次へ進む条件

`scripts/validate_v29_risky_subsystems.py` が pass し、  
`manifests/tourbillon_v29_risky_subsystems_contract.json` から各モジュールの意味を追えること。

その後にのみ、V29 full assembly contract へ進む。
