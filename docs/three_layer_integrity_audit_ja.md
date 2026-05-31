# 三層総点検レポート

## 判定

2026-05-18 の総点検では、現行 V30 の `goal_state = pass` を最終完了証拠としては信頼できないと判定した。  
理由は、最上位の closeout chain、中間の状態遷移、最下層の implementation evidence の 3 層すべてに、**弱い pass が強い claim へ昇格する抜け道**が残っていたためである。

## 発見した穴

### 1. 最上位ルール / closeout

- live `TASKS.md` が動いた後でも古い `goal_state.json` が pass のまま残れた。
- `goal_state_freshness.json` の同ターン確認が turn-end rule に明示されていなかった。
- same-generation coherence、current-delivery parity、README entrypoint parity が machine gate になっていなかった。
- ledger closeout が `Active Tasks` の一部構文だけを見ていた。

### 2. 中間の設計ワークフレーム

- `front_loaded_design_framework` は強かったが、実務導線の `mechanical_design_workflow` が `selected concept -> CAD` を完全には塞いでいなかった。
- `tourbillon-cad-completion` skill が selected concept から manifest / CAD へ直行できた。
- 大規模出力の案数、`feasible selected design`、`geometry-ready` の責任分界が全 skill に浸透していなかった。

### 3. 実装レイヤー

- V30 には selected-design feasibility artifact と geometry-contract handoff artifact が無いのに generator が走っていた。
- winding / spatial / object-value validators は存在確認中心で、semantic claim を閉じていなかった。
- V30 固有の role manifest、sampled-motion、declared-contact、visibility、DFAM、evidence-binding gate が無かった。
- V28 コアの再利用 pass を借りて、新規 lower train / vertical lift の全体系再検証を省略していた。

## その場で canonical 化した対策

- `AGENTS.md` / `GOAL.md`
  - same-turn freshness、same-generation coherence、current-delivery parity を closure 要件へ昇格。
- `docs/mechanical_design_workflow_ja.md`
  - `candidate concept -> selected concept -> feasible selected design -> geometry-ready -> implemented geometry` を正本化。
- `docs/skill_governance_ja.md`
  - 状態遷移ごとの責任分界を追加。
- `docs/design_rule_register_ja.md`
  - `DR-P-015` semantic-claim evidence chain
  - `DR-P-016` derivative full-system recertification
  - `DR-P-017` closeout coherence
- skills
  - CAD completion / concept feasibility / gear / motion / DFAM の handoff 条件を強化。

## 結論

V30 は **完成品ではなく、監査で再格付けされた candidate** と扱う。  
次の実行は、欠けていた selected-design feasibility closure と geometry-ready handoff を先に閉じ、そこからのみ新しい実装へ進む。
