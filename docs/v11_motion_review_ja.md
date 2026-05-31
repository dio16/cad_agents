# V11 Motion Review

## 自動チェック結果

`tourbillon_v11.json`に設計チェックを追加し、`check`コマンドで以下を検証しました。

- orbit pinion to fixed ring pitch: pass, pitch error 0.0 mm
- central sleeve bearing clearance: pass, radial clearance 0.65 mm
- front crank connected to center drive: pass
- fixed ring visibility: pass

## V8からの改善

- クランク未接続: V11ではクランク部品側に入力ノブから中心側へ向かうリンクを保持し、ベース側の重複リンクを削除しました。
- ギアずれ: 固定リング pitch radius 53.0 mm、ピニオン中心距離 39.5 mm、ピニオン pitch radius 13.5 mmにし、理論ピッチ誤差を0.0 mmにしました。
- 干渉: ギア面を上げ、ケージ上面との重なりを減らしました。重複していたクランクリンクも削除しました。
- 歯面: 角の立った矩形歯から、丸みのある外歯とピン状内歯へ変更しました。厳密なインボリュートではありませんが、卓上オブジェとして噛み合いが視覚的に読みやすくなっています。

## Onshape目視レビュー

V11 Assembly:
https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/47455c94128d905048aeb521

0度から180度姿勢へAPIで切り替えてOnshape表示を確認しました。
固定リングのピン列、軌道ピニオン、ケージ、バランスホイールの前後関係はV10より明確です。
ピニオンがリング内歯列に沿っていることも確認できます。

## 残課題

Onshape上の合致フィーチャーはまだ0です。
現在はAPIによるInstance Transform姿勢検証であり、Onshape Mateを使った連続駆動ではありません。
次の改善では、生成部品に安定したMate Connector候補を持たせ、Revolute MateとGear RelationをAssembly Feature APIで生成するところまで進めます。
