# V29 Full Assembly Contract Review

## 目的

V29 を full sculpture geometry へ進める前に、  
採用案・局所モジュール・モジュール間 interface を 1 つの geometry-ready contract に畳み込む。

## この contract が閉じるもの

1. **claim**
   - stationary-autonomous-winding
   - spatial-kinetic-sculpture-object
2. **module**
   - autonomous power module
   - spatial riser
   - canted cage display
3. **motion hierarchy**
   - slow macro
   - medium transfer
   - fast fine
4. **spatial transition**
   - 20 mm の低い X 軸から 62 mm の Z 軸へ
   - さらに 30° 傾斜 carrier へ
5. **future evidence**
   - stationary autonomous winding
   - spatial drive
   - object value
   - mechanical truth
   - deliverable package

## まだ閉じないもの

- full CAD geometry
- 実トルク
- 歯数確定
- fabrication package
- 実機寿命

## geometry へ進む条件

`scripts/validate_v29_full_assembly_contract.py` が pass し、  
その中で次の 3 契約がすべて接続済みであること。

1. selected concept contract
2. risky subsystem contract
3. system interface control contract

`selected-design feasibility closure` が pass した後にのみ、  
`mechanically_viable_pre_cad` と呼ぶ。
