# Repository Goal

## Goal

このリポジトリのゴールは、**机上で静止していても自律的に巻き上がる給力機構を持ち、全体は大胆なキネティック・スカルプチャーとして成立し、速く細かな部分は時計のように精緻で、通常は平面内で閉じる時計機構を立体空間へ解放した、3Dプリンタで製作可能な卓上トゥールビオン機構オブジェを完成させること**である。

ただし、このリポジトリは単発の形状完成だけを追わない。ゴール達成まで止まらず進むために、まず正しい状態を保ち、再利用可能な設計システムを育て、そのうえで継続的に成果物を前進させる。

## Priority Order

競合がある場合は、原則として次の順で優先する。

1. **P1: Operational Integrity / Truth**
   - 正本、台帳、文書同期、実行経路、壊れた gate、証拠の信頼性を守る。
2. **P2: Reusable Design System**
   - workflow、skill、checklist、design rule、manifest schema、gate definition を一体の再利用資産として整える。
3. **P3: Goal Delivery / Evidence Production**
   - 設計反復、CAD 実装、生成、検証実行、fabrication package を進め、ゴールとの差分を証拠付きで縮める。
4. **P4: Optional Optimization / Exploration**
   - 直近のゴール達成を直接進めない polish、将来実験、任意改善を扱う。

## Decision Rule

- `P1` は、正本や証拠が信頼できない時に必ず割り込む。
- `P2` は、現在の `P3` を壊す再発 defect、missing workflow、missing rule、missing gate がある時に `P3` より先行する。
- 将来価値だけの `P2` 改善は台帳へ残すが、現在の `P3` delivery を飢えさせてはならない。
- `P3` は readiness floor を満たしたら継続して進め、実装で得た知見を次の `P2` へ戻す。
- `P4` は `P1`-`P3` に進めるべき未解決タスクがない時だけ実行する。
- 例外は、ユーザーが明示的に優先順位を上書きした場合のみ認める。

## Definition of Done by Layer

### P1: Operational Integrity / Truth

- 正本の階層、タスク台帳、文書同期、Bash-only 実行経路、サブエージェント運用が明文化されている。
- どの成果物が最新か、どの主張が repo 内で証明済みか、どの gate が信頼できるかを追跡できる。
- truth drift、stale evidence、壊れた gate が残っていない。

### P2: Reusable Design System

- 再利用可能な canonical workflow があり、版別文書の知見が必要に応じて昇格している。
- 繰り返し出現する作業には skill または checklist があり、trigger / input / output / gate / failure mode が定義されている。
- design rule は `evergreen` / `project-level` / `version-specific` / `hypothesis` に分類され、scope、根拠、失敗モード、検証方法、例外を持つ。
- manifest schema と gate definition が、workflow / skill / rule と矛盾せず再利用できる。
- 実装上の発見は、必要に応じて workflow / skill / rule / contract / gate へ昇格される。

### P3: Goal Delivery / Evidence Production

- 生成された 3D model は、上位レイヤーで定めた workflow、rule、gate に従っている。
- 完了主張は、manifest、独立検証、viewer、BOM、組立、制限事項の証拠に裏付けられている。
- 現在の成果物が最終ゴールより弱い claim しか持たない場合、その差分が次の実行可能タスクへ分解されている。

### P4: Optional Optimization / Exploration

- 実験や polish は、`P1`-`P3` の信頼性と前進を損なわない。
- 将来価値は記録されるが、現在のゴール差分を閉じる仕事と混同しない。

## Continue-Until-Goal Rule

- `reports/current_gate_summary.json` が pass でも、その claim が最終ゴールより狭い場合、リポジトリはまだ完了していない。
- 未解決の goal gap は、外部入力、利用不能な認証情報、UI 専用証拠、またはユーザー判断を要する blocker でない限り、`TASKS.md` の active work として残す。
- 各反復では、最終ゴールとの差分を最も小さく縮める実行可能な `P3` task を必ず選ぶ。必要な reusable gap がその task を壊す時だけ、先に `P2` で直す。
- 「locally complete」「package complete」などの部分完了は、最終ゴール達成の代替ではなく、次の差分を決めるための中間証拠である。

## Goal Closure Gate

このリポジトリは、自然言語の満足感ではなく、次をすべて満たした時だけゴール達成とみなす。

1. 最新の goal-state artifact が `status = pass` である。
2. `reports/goal_state_freshness.json` が pass し、goal-state が現在の `TASKS.md` と同一 revision に束縛されている。
3. 最新の信頼済み claim が、少なくとも `spatial-kinetic-sculpture-object` 階層に達している。
4. 机上静止時にも成立する自律給力入力からトゥールビオン機構までの力の流れが実在し、`stationary_autonomous_winding_evidence = pass` である。
5. 少なくとも一度、異なる高さまたは異なる軸方向へ必然的に力を渡す立体駆動があり、`spatial_drive_evidence = pass` である。
6. object-value evidence が同一世代で pass し、遠景の彫刻性、中景の運動可読性、近景の時計的精緻さ、時間的リズム、立体機構としての必然を満たしている。
7. geometry-derived mechanical-truth evidence が同一世代で pass し、実体軸、支持ソリッド、実在する力伝達、mesh / axis 整合、未宣言干渉ゼロを宣言文ではなく生成ジオメトリから独立に示している。
8. object-level completion に必要な viewer / role / numeric / visibility / closeout evidence が同一世代で pass している。
9. ユーザーが直接受け取れる stable deliverable package が存在し、printable STL、viewer entrypoint、preview、BOM / assembly 情報、package manifest が同一世代で検証済みである。
10. completion-critical な report / viewer / deliverable が 1 つの generation identity に束縛され、異世代 artifact の混在がない。
11. README から 1 手で辿れる current-delivery index があり、最新 viewer と printable package を明示している。
12. `TASKS.md` に未解決の unblocked `P1`-`P3` mission work が、`Active Tasks` だけでなく queue / inbox / conditional sections にも残っていない。
13. 残る work がある場合は、外部 blocker とその証拠だけである。

`reports/current_gate_summary.json`、版別 summary、または部分 claim の pass は、`reports/goal_state.json` が pass しない限り最終ゴール達成の代替にならない。

## Completion Includes

このリポジトリにおける「完成」は、3D成果物だけを意味しない。次を含む。

- 再利用可能な設計ルール
- 検証ゲート
- 設計契約
- 制限事項
- 次回以降の設計が前回より良く始まるための運用改善

## Object Value Standard

この repo でいう完成品は、機構が成立するだけでなく、**置く価値と見続ける価値**を持つ。

1. **遠景価値 / sculptural presence**
   - 離れて見ても輪郭、余白、高低差、重心に存在感があり、机上で作品として成立する。
2. **中景価値 / motion legibility**
   - 初見でも、入力から carrier、歯車列、脱進機までの因果が hero view で追える。
3. **近景価値 / watch-like precision**
   - 速く細かい運動部ほど薄く、緻密で、近づくほど情報量が増える。
4. **時間価値 / layered rhythm**
   - 遅い大運動、中速の伝達、速い微小運動が同時に見え、1 周期内に繰り返し見たくなる見せ場がある。
5. **空間価値 / spatial mechanism**
   - 単なる平面時計の拡大ではなく、異なる高さまたは軸方向をまたぐ駆動が、構造上も視覚上も価値を生む。

## Scope / Non-Claims

### Repo 内で証明するもの

- 3D model と生成系の再現性
- manifest / generator / report / viewer の整合
- user-consumable deliverable package と、そこから直接開ける viewer / printable STL の存在
- object-value brief、hero-view evidence、kinetic-object review、stationary-autonomous-winding / spatial-drive evidence
- 比率、支持、干渉、視認性、BOM、組立順、局所的な機械成立性
- local-first / WSL-first の検証経路

### Repo 外の証拠が必要なもの

- 実プリンタ、材料、スライサー依存の最終クリアランス
- 長時間運転時の摩耗、反り、耐久性
- 実物組立後の操作感
- 外部 CAD ソルバや物理試作を必要とする最終証明

## Sources of Truth

1. `GOAL.md`
2. `SPEC.md`
3. `AGENTS.md`
4. `TASKS.md`
5. canonical workflow / design-rule / gate documents under `docs/`
6. `manifests/*.json`
7. generator scripts under `scripts/`
8. generated reports under `reports/` and viewer artifacts under `deliverables/`

版別文書は歴史と根拠であり、現在の慣行を定義する正本ではない。永続化すべき学びは canonical artifact へ昇格する。

## Environment

- **OS:** WSL 2 (Linux), Bash-only active work
- **Python:** 3.12+, managed by UV
- **Package manager:** UV (required), pnpm (auxiliary, Node.js only)
- **CAD backends:** CadQuery + build123d (both supported, manifest-driven)
- **License:** Apache-2.0

## Review Cadence

- 新しい版、重大な失敗、完了主張、または 2 回以上再発した不具合の後に、`P1`-`P3` の見直しを必ず行う。
- `P1` の truth gap または現在の delivery を壊す `P2` gap を残したまま `P3` を続けてはならない。
- 最終ゴールに未解決差分がある限り、外部 blocker でない差分を active task に保ち、部分完了の報告だけで終了してはならない。
- 各反復の最後に、次の 3 問を確認する。
  1. 何が前より繰り返しやすくなったか。
  2. 何が前より間違えにくくなったか。
  3. どの学びを履歴から再利用可能な資産へ昇格できたか。
