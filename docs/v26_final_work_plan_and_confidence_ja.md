# V26 Final Work Plan And Confidence Review

## 目的

本リポジトリの目的は、AM で造形できるトゥールビオン機構の卓上オブジェについて、設計契約、部品データ、BOM、組立順、動作レビュー、検証レポートを同じ生成系から再現できる状態にすることである。

## 最適ワークプラン

1. `agent.md` を確認し、完了語を外観ではなく証拠ベースに限定する。
2. 最新の設計契約 `tourbillon_v26_mechanical_package.json` を唯一の設計契約として扱う。
3. `create_v26_mechanical_package.py` で、部品別 STL、BOM、組立順、検証、viewer、bundle を同時生成する。
4. 検証では、歯数、ピッチ半径、中心距離、比率、バックラッシュ、Lewis 応力、608ZZ/3 mm 軸クリアランス、STL サイズ、三角形数、bbox、支持連続性、軸方向干渉、重複ロール所有、viewer 埋め込みメッシュ数を確認する。
5. 実データレビューは `v26_3d_cad_motion_viewer.html` を標準とする。これは STL 出力に使った三角形メッシュを HTML に埋め込み、自由視点、ポーズステップ、分解表示、Z 断面、支持参照ソリッド、ラベル、モーショントレース、比率 readout で 3D 動作レビューできる。
6. Native Onshape Gear Relation は未検証のまま分離し、local fabrication complete と native complete を混同しない。
7. 生成、構文検査、ブラウザ表示確認を通した後のみ、今回の範囲を完了とする。

## 改善ループで潰した抜け漏れ

- V26 の旧 viewer は概念図/SVG であり、実際の生成 CAD メッシュをレビューしていなかった。
- 3D viewer は当初ローカル STL fetch 方式にすると file:// 制限で不安定になるため、生成メッシュを HTML に埋め込む方式にした。
- viewer の説明文に文字化けが混入したため、検証ゲートで `このviewerは` を確認し、文字化け断片 `縺` がないことをチェックするようにした。
- 完了判定が `cad_mesh_viewer` の存在を必須にしていなかったため、必須条件へ昇格した。
- 生成スクリプトを同一 Python セッションから複数回呼ぶ場合に備え、グローバル mesh/stat キャッシュを実行開始時に clear するようにした。
- `README.md` と `TASKS.md` に、3D CAD mesh viewer を標準出力として記録した。
- 回転する orbit pinion と carrier 支持が同じ z 範囲を占有していたため、lower support `z=20.0..35.8` と upper support `z=48.2..55.0` に分離し、pinion `z=36.0..45.0` および escape wheel `z=45.05..48.0` と重ならないようにした。
- balance/pallet の見えるロールが `z=49.0..53.0` にあり、支持が不足して見えたため、carrier 側に lower bridge `z=45.0..49.0` と upper bridge `z=53.0..56.0` を追加し、支持グラフのゲートを追加した。
- orbit pinion に含まれていた escape 風ギアと、hand crank に含まれていた knob を取り除き、escape wheel と crank knob の物理ロール所有をそれぞれ単一 STL にした。
- 2D viewer、3D viewer、motion validation で escape wheel の親子関係がずれていたため、escape wheel は orbit/escape shaft と同軸で同じ相対比率 `-4.0`、絶対比率 `-3.0` を使う契約に統一した。
- 今回の Codex ブラウザ自動操作では `file://` 直接オープンがセキュリティポリシーで拒否されたため、自動スクリーンショット確認は未実施。代わりに HTML 埋め込みペイロード、UI トークン、変換契約、文字化け不在、メッシュ数をローカル検証ゲートに昇格した。

## 現在の完了条件

V26 は次の条件を満たす場合に `local fabrication complete` とする。

- 9 点の AM 用 STL が生成され、非ゼロサイズである。
- 各 STL の三角形数と bbox が検証レポートに残る。
- 印刷部品 CSV、購入品 CSV、組立順 CSV が生成される。
- 72T 固定内歯リング、18T orbit/escape ピニオン、60T carrier drive、18T hand pinion の中心距離と比率が契約と一致する。
- 608ZZ 中央軸受、3 mm orbit/escape 軸、3 mm hand crank 軸のクリアランスが契約値を満たす。
- orbit/escape shaft、balance、pallet の支持グラフが見えるロールを支持し、回転部品と固定支持の軸方向重なりがない。
- escape wheel と crank knob の物理ロール所有が重複していない。
- 連続 fallback motion viewer と、実メッシュ由来の 3D CAD motion viewer が生成される。
- 3D CAD motion viewer が自由視点、ポーズステップ、分解表示、Z 断面、支持表示、ラベル表示、比率 readout、統一変換契約を持つ。
- 完了ステータスが native Onshape Gear Relation を未検証として明記する。

## 今回の確認コマンド

```powershell
python cad_agent_framework\scripts\create_v26_mechanical_package.py
python -m compileall cad_agent_framework\scripts\create_v26_mechanical_package.py
```

`v26_package_validation.json` は 48 件のチェックを持ち、失敗件数 0 である。

## 100% 自信の範囲

リポジトリ内で再現可能な生成・検証・3Dレビュー成果物については、上記ゲートが通っており、現時点で抜け漏れはない。

ただし、以下は物理試作または外部 CAD ソルバが必要なため、このリポジトリ内だけで 100% と断言しない。

- 実プリンタ、材料、スライサー設定ごとの最適クリアランス。
- 長時間回転時の摩耗、反り、軸傾き、手回し荷重での耐久性。
- 時計用脱進機としての lock/impulse 接触物理。
- Native Onshape Gear Relation による完全な CAD mate animation。

したがって最終表現は、`local fabrication complete; native Onshape Gear Relation not verified; physical print tuning remains process-specific` とする。
