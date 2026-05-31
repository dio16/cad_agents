# Codex Agentic CAD Workflow

> この文書は Onshape 中心期の履歴説明を含む。現行の運用判断では、`AGENTS.md` の `Local-First CAD Backend Policy` と `docs/local_first_cad_backend_strategy_ja.md` を優先する。

## 結論

Codexが外部CADと連携してエージェンティックモデリングを行う基盤としては、現時点では Onshape API + CadQuery/FeatureScript + Codex in-app browser の組み合わせが最も強い。

## 採用構成

- 形状生成: CadQuery または FeatureScript
- CAD投入: Onshape REST API translations
- アセンブリ作成: Onshape REST API assemblies
- 動作姿勢検証: Onshape assembly transform API
- 視覚レビュー: Codex in-app browser
- 成果物管理: JSON manifest

## なぜOnshape中心か

- 公式REST APIがあり、ブラウザ座標操作を避けられる。
- STEP投入、Assembly作成、Instance追加、Transform変更がAPI化できる。
- クラウドCADなので、Codexが作った変更をユーザーが同じドキュメントで即確認できる。
- CAD履歴がOnshape側に残る。

## 他候補

- FreeCAD: ローカルで完全自動化できるが、ユーザー確認と共同レビューが重い。
- Fusion/SolidWorks: 高機能だがGUI/ライセンス/ローカル状態に依存し、Codexの安定操作が難しい。
- OpenSCAD/CadQueryのみ: 生成は速いが、クラウドCAD上での組立・レビュー・共有が弱い。

## 標準ループ

1. 仕様を `manifest` に定義する。
2. CadQuery/FeatureScriptで部品を生成する。
3. `cad_agent_cli.py import` でOnshapeへ投入する。
4. `cad_agent_cli.py assembly` で検証Assemblyを作る。
5. `cad_agent_cli.py pose --theta 90` などで代表姿勢を作る。
6. in-app browserで視覚確認する。
7. 問題を設計スクリプトに戻す。

## 現在の対応範囲

- Manifest検証
- APIキー認証
- STEP個別インポート
- インポート完了ポーリング
- Assembly作成
- Part挿入
- Instance ID取得
- Z軸回転姿勢
- 公転+自転姿勢
- 姿勢検証履歴のmanifest記録
- Assembly Feature API呼び出し基盤

## 次に拡張する範囲

- Mate Connector作成
- Revolute mate作成
- Gear relation作成
- Appearance設定
- 干渉検査のAPI/近似ジオメトリチェック
- FeatureScript生成バックエンド
- Part Studio Features APIによるネイティブ履歴生成

## Transform Rule

Onshape Assembly TransformはトップレベルAssembly座標系に対する絶対4x4行列として扱う。CAD生成側はmmで設計しやすいが、Onshape APIへ渡す平行移動はmeterに変換する。

## Mate Automation Rule

Onshape公式APIではAssembly Feature APIでMate ConnectorとMateを作れる。ただし実体面/稜線に安定してMate Connectorを置くには、対象面のdeterministicIdが必要になる。今後の完全自動Mateは、生成CAD側に軸・面・Mate Connector候補を明示的に設け、それをmanifestに記録してから作成する。
