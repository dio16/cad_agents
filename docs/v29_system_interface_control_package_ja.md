# V29 System Interface Control Package

## 目的

個別に成立する risky subsystem を、そのまま full sculpture geometry に拡大して失敗しないよう、  
**モジュール間の受け渡しだけを先に閉じる**。

## なぜ必要か

局所モジュールがそれぞれ pass しても、

- 出力軸と入力軸の高さが違う
- riser の envelope が cage の見せ場を塞ぐ
- 組立順がモジュール境界で破綻する

なら、大物 CAD で高価な手戻りになる。  
そこで full assembly contract の前に、`cross_module_integration_pass` を置く。

## 管理する項目

1. module input / output
2. handoff axis / centerline / transition
3. reserved envelope
4. hero-view occlusion budget
5. declared contact zone
6. assembly order dependency

## 今回の閉包

| Handoff | 条件 |
| --- | --- |
| power -> riser | X 軸、centerline height 20 mm |
| riser -> canted cage | 62 mm 高さから 30° 傾斜 carrier へ渡す |

この 2 つが閉じない限り、full sculpture geometry へ進まない。

## 次へ渡すもの

- `manifests/tourbillon_v29_system_interface_control_contract.json`
- `scripts/validate_v29_system_interface_control.py`
- full assembly contract に引き継ぐ frame / envelope / handoff 定義
