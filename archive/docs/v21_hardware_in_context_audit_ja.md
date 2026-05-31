# V21 Hardware-In-Context Audit

## 目的

V20 は標準部品を別 assembly で参照できるところまで確認したが、印刷部品と標準部品を同じ文脈で干渉監査していなかった。V21 は 608ZZ、3 mm 軸2本、M3リングねじを印刷部品と同じ座標系で扱い、製造・組立リスクを検出する。

## 追加ゲート

- `hardware-context-audit`: 印刷部品と標準部品の交差を検査する。
- `allowed_hardware_fit_pairs`: ベアリング、軸、ねじなど意図的な嵌合・締結は、汎用干渉ではなく専用証跡として扱う。
- `purchased_parts_bom`: 608ZZ x1、3 mm orbit shaft x1、3 mm hand shaft x1、M3 ring screws x4 を V21 の購入品として固定する。
- `assembly_sequence`: 組立順序、使用部品、対応する検査ゲートを manifest に持たせる。
- `visibility_gate`: top/isometric、0/90/180/270 deg の視認性 artifact を要求する。

## 注意

M3 ねじ数は V20 の `mechanism_spec` では8本だが、現行 reference geometry は4本である。V21 manifest では現行 geometry に合わせて4本として扱い、8本化する場合は generator とBOMを同時に更新する。
