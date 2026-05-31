# V26 設計スキーム / Codex ワークフロー改善レビュー

## 結論

V25 で「設計契約を先に作る」方向は成立していたが、卓上オブジェとして AM 造形に渡すには、成果物が組立表示寄りで、部品別 STL、購入品 BOM、組立順、現物クリアランス確認までが弱かった。

V26 では、V21 の標準部品・軸支持・クリアランス設計と、V25 の機構先行・検証先行スキームを統合した。最新の完了判定は `local fabrication complete` とし、ネイティブ Onshape Gear Relation は引き続き未検証として扱う。

## 既存スキームの成立性

成立している点:

- 固定内歯リング、回転キャリア、遊星ピニオン、手回し入力のトポロジーは機械要素として筋が通っている。
- V21 で 608ZZ、3 mm 軸、M3 ねじの寸法文脈が入り、単なる見た目モデルから機械構成へ進んでいる。
- V25 で歯数、モジュール、中心距離、比率、Lewis 応力、支持ロール、モーション契約を CAD 前に定義する流れになった。
- Onshape Gear Relation が通らない場合に、ネイティブ完了とローカル完了を分ける運用は正しい。

不足していた点:

- V25 は部品別 AM データではなく、単一 assembly STL/GLB と viewer が中心だった。
- エスケープメントが「支持された見せ場」ではあるが、印刷部品、軸、組立順への落とし込みが不足していた。
- 完了判定が viewer と契約レポートに寄り、印刷部品セット・購入品 BOM・組立順のゲートが弱かった。
- Codex の設計ループとして、レビュー結果から次の fabrication package を自動生成する道筋が明文化されていなかった。

## V26 改善

- `manifests/tourbillon_v26_mechanical_package.json` を新設し、設計意図、標準部品、歯車メッシュ、軸支持、エスケープメントの限界、必要ゲートを 1 つの契約にまとめた。
- `scripts/create_v26_mechanical_package.py` を追加し、manifest から AM 用の部品別 STL、BOM、組立順、検証 JSON、視認性 SVG、連続モーション viewer、ZIP bundle を生成する。
- V26 は module 1.5、72T 内歯リング、18T orbit/escape ピニオン、60T carrier drive、18T hand pinion とし、FDM 卓上オブジェ向けに V25 より太い歯・大きなクリアランスを優先した。
- orbit/escape shaft、hand shaft は 3 mm 軸の二点支持とし、中央は 608ZZ で受ける。
- エスケープメントは carrier-mounted visual lever escapement demonstrator と明記した。調速時計としての接触物理は未検証であり、卓上デモの見せ場として完結させる。

## Codex ワークフロー改善

次回以降の期間設計は、次の順序で進める。

1. 要求を `object_class`、完了語、未検証の限界に分ける。
2. manifest で機構トポロジー、歯車、軸、標準部品、エスケープメントの親子関係を固定する。
3. CAD 生成前に、中心距離、比率、バックラッシュ、応力、軸支持、浮遊部品、BOM/組立順のゲートを作る。
4. 生成スクリプトは manifest だけを入力にし、部品別 STL と検証レポートを同時に出す。
5. 完了判定は `v*_completion_status.json` の語をそのまま使い、viewer だけ、色だけ、ポーズだけでは完了にしない。
6. Onshape は共有・最終レビュー用に限定し、Gear Relation が通るまで native complete は名乗らない。

## V26 完了成果物

- 契約: `manifests/tourbillon_v26_mechanical_package.json`
- 生成スクリプト: `scripts/create_v26_mechanical_package.py`
- 部品 STL: `reports/fabrication_v26_mechanical_package/stl/`
- 印刷部品 CSV: `reports/fabrication_v26_mechanical_package/printed_parts.csv`
- 購入品 CSV: `reports/fabrication_v26_mechanical_package/purchased_parts.csv`
- 組立順 CSV: `reports/fabrication_v26_mechanical_package/assembly_sequence.csv`
- 検証: `reports/fabrication_v26_mechanical_package/v26_package_validation.json`
- モーション: `reports/fabrication_v26_mechanical_package/v26_motion_validation.json`
- 3D CAD メッシュ viewer: `reports/fabrication_v26_mechanical_package/v26_3d_cad_motion_viewer.html`
- 完了ステータス: `reports/fabrication_v26_mechanical_package/v26_completion_status.json`
- bundle: `reports/fabrication_v26_mechanical_package/v26_mechanical_package_bundle.zip`

`v26_3d_cad_motion_viewer.html` は標準レビュー viewer とする。STL ファイルを `file://` から fetch するのではなく、生成スクリプトが STL 出力に使った三角形メッシュを HTML に埋め込む。これにより、ローカルで開くだけで実データ由来の 3D 部品と fallback transform motion を確認できる。

## 残る限界

- 現時点の歯形は AM デモ向けの近似歯形であり、時計用の高精度 involute 接触や脱進機の lock/impulse 接触解析ではない。
- ネイティブ Onshape Gear Relation は未検証で、V26 完了は fallback transform motion に基づく。
- 実機造形後はプリンタ別に、3 mm 軸穴、608ZZ ポケット、内歯リングと orbit ピニオンのバックラッシュを試験片で補正する必要がある。
