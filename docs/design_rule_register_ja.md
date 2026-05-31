# 設計ルール台帳

この文書は、版別レビューで得た機械設計上の学びを、再利用可能な現在規範へ昇格するための正本である。  
`v*` 文書、manifest、report は証拠であり、この台帳に採用されるまで永続ルールそのものにはならない。

## 1. 台帳の使い方

### 1.1 分類

| 分類 | 意味 | 扱い |
| --- | --- | --- |
| `evergreen` | 対象物が変わっても長く効く機械設計の規範 | 既定で新設計へ適用する |
| `project-level` | この卓上トゥールビオン系列では長く効く制約 | この repo の設計で既定適用する |
| `version-specific` | 特定版の契約値・実装事実 | 証拠として残すが一般則へ混ぜない |
| `hypothesis` | 有望だが、採用に必要な証拠が不足している候補 | 実験または外部証拠を待つ |

### 1.2 状態

| 状態 | 意味 |
| --- | --- |
| `accepted` | 採用済み。設計・manifest・gate に反映してよい |
| `candidate` | 候補。規範化の材料はあるが採用条件を満たしていない |
| `rejected` | 永続ルールにしないと判断済み。理由を残す |

### 1.3 1 件のルールに必須の項目

採用済みルールは、最低限つぎを持つ。

1. `ID`
2. `分類`
3. `状態`
4. 判定可能な規範文
5. 防ぐ失敗モード / 理由
6. 証拠
7. 検証方法
8. 例外条件と例外時の代替検証
9. 関連する workflow / manifest / gate

## 2. 採用済みルール

### 2.1 Evergreen / accepted

| ID | 規範 | 防ぐ失敗モード / 理由 | 証拠 | 検証 | 例外 | 関連 |
| --- | --- | --- | --- | --- | --- | --- |
| `DR-E-001` | 可動ロールは、支持、親フレーム、運動関係をすべて持たなければならない。浮遊する可動部品や、支持されない装飾マーカーを置いてはならない。 | 見た目だけ成立し、組立不能または機構として説明不能になることを防ぐ。 | `AGENTS.md` の `Completion Language` / `Mechanical Design Scheme`、`docs/v25_mechanical_design_workflow_ja.md` §§1,3,5、`docs/v26_final_work_plan_and_confidence_ja.md` の支持グラフ改善、`reports/progress_ledger.jsonl` の 2026-05-08 監査 | role manifest、support graph、no-floating-role gate、軸支持レビュー | 単なるレンダリング用参照形状は可。ただし completion claim から除外し、role manifest に非機能物として明記する。 | `Mechanical Design Scheme`、support graph gate、role manifest |
| `DR-E-002` | CAD 完了前に、各歯車噛み合いは単一の共有 module を持ち、歯数、圧力角または歯形、ピッチ半径、中心距離、比率、backlash を明示し、整合検証を通さなければならない。外歯車は、別 contract が明示しない限り involute 20° を既定とする。 | 見た目は噛んでいても運動比・中心距離・歯形が破綻することを防ぐ。 | `docs/v25_mechanical_design_workflow_ja.md` §§3-5、`AGENTS.md` の `Completion Language` / `Mechanical Design Scheme`、`manifests/tourbillon_v27_connected_contract.json` の `gear_meshes` | gear pitch/module/ratio check、center-distance check、backlash check、declared mesh contact audit | 非歯車駆動を選ぶ場合は mesh 欄を不要にできるが、代替の伝達契約と検証を manifest に置く。別歯形を選ぶ場合は、その profile と検証法を contract に明記する。 | manifest `gear_meshes`、`required_gates` |
| `DR-E-003` | 機械的な動作を主張するロールには、視覚アニメーションではなく物理的な駆動経路を宣言しなければならない。物理経路が未実装なら、主張をブロックして限定語を明記する。 | viewer の動きだけで、接触・伝達・拘束が存在するかのように誤認することを防ぐ。 | `reports/progress_ledger.jsonl` の 2026-05-09 独立監査、`scripts/independent_mechanical_truth_audit.py`、`manifests/tourbillon_v27_connected_contract.json` の `escapement_drive_model`、`reports/fabrication_v27_connected_package/v27_independent_connected_audit.json` | physical drive model check、mechanical truth audit、sampled motion audit | 単なる展示モーションは可。ただし「display」「visual」「not regulating」等の限定語を明記し、未検証 claim を列挙する。 | escapement drive model、mechanical truth audit |
| `DR-E-004` | 印刷対象の構造部品は、完成 claim の対象にする前に、意図した単一連結ソリッドとして検証しなければならない。 | 複数 shell の見かけ上の集合体を、実際に造形・支持できる一体部品と誤認することを防ぐ。 | `reports/progress_ledger.jsonl` の 2026-05-09 監査、`docs/local_first_cad_backend_strategy_ja.md`、`reports/current_gate_summary.json` の V27 connected-solid audit | single-solid / connected-solid audit、STEP import、part-level topology check | 意図的な assembly 出力は可。ただし印刷部品ではなく assembly artifact と分類し、BOM と組立順へ逃がす。 | connected-solid audit、fabrication package |
| `DR-E-005` | 静止姿勢だけでなく、必要な運動範囲全体で干渉と接触を検証しなければならない。 | 0 度では成立するが、途中姿勢で支持やつまみが衝突する設計を防ぐ。 | `AGENTS.md` の `Required Gates`、`reports/progress_ledger.jsonl` の 2026-05-16 V27 監査、`reports/current_gate_summary.json` の sampled motion audit / STEP interference audit | static interference audit、sampled full-cycle motion audit、declared contact audit | 完全固定機構では sampled motion は不要。ただし静的干渉 gate は残す。 | `solid-audit`、sampled motion audit、declared mesh contact audit |
| `DR-E-006` | 物理ロールの所有権は一意でなければならない。同じ機械ロールを複数 STL に重複実装してはならない。 | escape wheel や knob が二重に存在し、BOM・組立・干渉判定が壊れることを防ぐ。 | `docs/v26_final_work_plan_and_confidence_ja.md` の重複ロール所有修正、`reports/progress_ledger.jsonl` の 2026-05-08 監査 | role ownership gate、BOM closure、part-role mapping review | 意図的な冗長部品は可。ただし別 role ID を持ち、機能上の冗長性を manifest で説明する。 | role manifest、BOM、package validation |
| `DR-E-007` | completion claim は、最新の独立検証から導かなければならない。生成器自身の自己申告や古い validation だけで完了を名乗ってはならない。 | 自己肯定的 validation、古い report、混在ランタイムによる誤完了を防ぐ。 | `AGENTS.md` の `WSL-Only Validation Policy`、`reports/progress_ledger.jsonl` の 2026-05-09、`reports/current_gate_summary.json`、`reports/validation_quarantine.json` | independent validator、freshness check、artifact provenance、current gate summary | 実験メモ段階では completion claim をしない前提で省略可。 | independent audit、artifact provenance、current gate summary |
| `DR-E-008` | 力を伝える可動リンク部品は、完成 claim の前に「印刷部品として単一連結ソリッドであること」と「同一世代の declared-contact audit で意図した接触だけを持つこと」を同時に満たさなければならない。 | 出力ピンだけが別シェルになる、または古い report と新しい geometry を混ぜて linkage 成立を誤認することを防ぐ。 | V27 の freshness 再監査、V28 pallet output-pin の再接続修正、`reports/fabrication_v28_mechanism_package/v28_mechanical_truth_audit.json`、`reports/fabrication_v28_mechanism_package/v28_declared_contact_audit.json` | single-solid / connected-solid audit、same-generation freshness check、declared-contact audit | 純粋な表示部品では linkage claim を外す代わりに省略可。 | connected-solid audit、declared-contact audit、artifact provenance、claim-transition closeout |

### 2.2 Project-level / accepted

| ID | 規範 | 防ぐ失敗モード / 理由 | 証拠 | 検証 | 例外 | 関連 |
| --- | --- | --- | --- | --- | --- | --- |
| `DR-P-001` | この卓上トゥールビオン系列で固定四番車相当を主張する場合、固定要素は実体を持つ内歯リングとして設計・検証し、外歯車を内側に描いて代用してはならない。 | トゥールビオンの伝達トポロジーを見た目だけで偽装することを防ぐ。 | `AGENTS.md` の `Mechanical Design Scheme`、`docs/v25_mechanical_design_workflow_ja.md` §§2-3、`reports/current_gate_summary.json` の V27 design claim | internal-ring geometry audit、ring/orbit relation check | 別トポロジーを採用する設計は可。ただし fixed fourth-wheel analogue の claim を外し、新しい topology contract を作る。 | topology contract、internal-ring gate |
| `DR-P-002` | この repo の completion wording は、卓上デモ、機械駆動された卓上機構、watch-grade、native CAD、物理試作を必ず分離しなければならない。未検証範囲を混同してはならない。 | 見せる機構、balance まで物理経路が閉じた卓上機構、時計級脱進機、Onshape mate、実機造形を同じ完了語で混同することを防ぐ。 | `AGENTS.md` の `Completion Language`、`docs/mechanism_claim_taxonomy_ja.md`、`docs/v26_final_work_plan_and_confidence_ja.md`、`manifests/tourbillon_v27_connected_contract.json`、`reports/current_gate_summary.json` | completion-status、claim-boundary gate、blocked-claim check、limitation review | ユーザーが別スコープを指定した場合は新しい completion class を先に定義する。 | `docs/mechanism_claim_taxonomy_ja.md`、completion-status、goal admission |
| `DR-P-003` | 表示性を価値に含む卓上オブジェでは、主要可動ロールが代表姿勢で見えることを、静止画または viewer evidence で確認しなければならない。 | 機構は成立しても、展示物として見せ場が隠れることを防ぐ。 | `AGENTS.md` の `Completion Language`、`docs/v25_mechanical_design_workflow_ja.md` §5、`reports/fabrication_v25_engineered/v25_visibility_contact_sheet.svg`、`manifests/tourbillon_v21.json` の visibility gate | visibility contact sheet、viewer smoke、sampled-pose review | 非展示用途の派生版では不要。ただし object class を manifest に変える。 | visibility gate、viewer artifacts |
| `DR-P-004` | この系列の manifest は、標準部品、軸支持、BOM、組立順を geometry と同格の設計契約として持たなければならない。 | 部品モデルはあるが、買える・組める・支持できる状態へ落ちないことを防ぐ。 | `docs/v26_scheme_and_workflow_review_ja.md`、`docs/v26_final_work_plan_and_confidence_ja.md`、`manifests/tourbillon_v27_connected_contract.json` の `standard_hardware` / `axes_and_supports` | BOM closure、standard-hardware gate、assembly-sequence review、support/BOM closure | 研究用の概念モデルでは可。ただし fabrication completion を名乗らない。 | fabrication package、standard hardware audit |
| `DR-P-005` | この系列で「機械駆動された卓上トゥールビオン機構」を名乗るには、少なくとも `hand -> carrier -> ring/orbit -> escape -> pallet -> balance` の物理駆動経路を持ち、balance を visual-only のまま残してはならない。 | pallet までしか閉じていない display mechanism を、balance まで連結された機構として過大 claim することを防ぐ。 | `docs/mechanism_claim_taxonomy_ja.md`、`manifests/tourbillon_v27_connected_contract.json`、`reports/fabrication_v27_connected_package/v27_role_manifest.json` の `balance_wheel.motion = supported visual hardware only`、`DR-E-003` | drive-chain continuity gate、balance-drive geometry gate、sampled balance motion audit、claim-boundary gate | `demonstrator` claim では balance の visual-only 表現を許す。ただし completion wording に限定語を入れ、上位 claim を blocked に置く。 | `docs/mechanism_claim_taxonomy_ja.md`、future balance-drive contract、mechanical truth audit |
| `DR-P-006` | fabrication / object-completion claim は、内部 report だけでなく、ユーザーが直接開ける stable deliverable package を持たなければならない。そこには printable STL、viewer entrypoint、preview、BOM / assembly 情報、relative-path manifest、handoff validation が含まれる。 | 証拠は存在するのに、実際に印刷・確認できる成果物が見つからない false positive completion を防ぐ。 | `GOAL.md` の `Goal Closure Gate`、`AGENTS.md` の `User-Consumable Deliverable Rule`、2026-05-17 の user report | user-deliverable validation、README handoff check、goal-state check | 内部実験では省略可。ただし fabrication / object-completion claim を名乗らない。 | deliverable package、goal-state、README entrypoint |
| `DR-P-007` | 完成した卓上オブジェを名乗る設計は、機構成立とは別に value brief を持ち、遠景の彫刻性、中景の運動可読性、近景の時計的精緻さ、時間的リズム、空間価値を満たさなければならない。 | 機構が動くだけの試作を、置く価値のある完成品と誤認することを防ぐ。 | `GOAL.md` の `Object Value Standard`、`docs/kinetic_object_value_framework_ja.md`、2026-05-17 user review | object-value brief review、hero-view review、kinetic-object review | 研究用 mechanism prototype では省略可。ただし completed object を名乗らない。 | kinetic-object framework、goal-state |
| `DR-P-008` | この系列で立体駆動を価値として名乗るには、異なる高さまたは異なる軸方向をまたぐ実在の力伝達が必要である。単なる段積みや斜視配置を立体駆動と呼んではならない。 | 平面時計を厚くしただけの形を spatial mechanism と過大評価することを防ぐ。 | `GOAL.md`、`docs/kinetic_object_value_framework_ja.md`、2026-05-17 user brief | spatial-drive map、force-path review、axis-transition review | 立体駆動を claim しない派生版では不要。 | spatial-drive gate、concept-feasibility package |
| `DR-P-009` | 出力規模が大きい設計ほど、CAD 前に複数案比較、motion graph、dimension budget、failure pre-mortem、選定理由を残さなければならない。重い 3D を探索に使ってはならない。 | 大規模出力ほど高価な後戻りが増え、token と時間を浪費することを防ぐ。 | `docs/front_loaded_design_framework_ja.md`、2026-05-17 user instruction | concept-option review、pre-CAD feasibility package、selection record | 小さな局所試験は省略可。ただし大物全体には適用しない。 | front-loaded workflow、mechanical-concept-feasibility skill |
| `DR-P-010` | この系列で自律給力を名乗る場合、外部エネルギー源、巻上げ経路、蓄力要素、表示機構への出力経路をすべて契約化しなければならない。単なる可視ドラムや decorative rotor を自律給力と呼んではならない。 | 卓上で静止して動くという claim を、実際には給力経路のない見せ物で過大評価することを防ぐ。 | 2026-05-17 user clarification、`docs/v29_pre_cad_feasibility_package_ja.md`、`manifests/tourbillon_v29_selected_concept_contract.json` | autonomous-winding architecture review、force-path review、storage/output review | 純手動モデルでは不要。ただし autonomous-winding claim を外す。 | V29 concept contract、goal-state、autonomous-winding evidence |
| `DR-P-011` | full-object CAD に進む設計は、整った architecture contract だけでなく、power / torque / energy、control、tooth-profile、hero-view、buildability の selected-design feasibility closure を通過していなければならない。 | 紙上で筋が良いだけの案を「成立済み」と誤認し、大きな 3D 反復で高価に失敗することを防ぐ。 | 2026-05-17 V29 re-audit、`docs/front_loaded_design_framework_ja.md`、`docs/pre_cad_design_readiness_checklist_ja.md`、`reports/progress_ledger.jsonl` | selected-design feasibility validation、power-path review、tooth-profile review、hero-view layout review、pre-CAD buildability review | 純粋な visual concept は可。ただし geometry-ready / feasible-selected-design を名乗らない。 | front-loaded workflow、goal admission、V29 feasibility package |
| `DR-P-012` | `geometry-ready` を名乗る設計は、`feasible selected design` の成立性前提を落とさず geometry contract へ写した handoff gate を通過していなければならない。下流の geometry generator は、gate 名の宣言ではなく、fresh pass artifact を実際に消費する。 | ルールだけが整っても、後段が pass artifact を読まなければ paper gate になり、古い設計のまま geometry が走る。 | 2026-05-17 V29 enforcement audit、`scripts/validate_v29_sculpture_geometry_contract.py`、`scripts/create_v29_sculpture_package.py` | geometry-contract validation、feasibility artifact freshness、generation precondition check | visual-only sketch は可。ただし object package / completion path には使わない。 | front-loaded workflow、goal admission、geometry generation entrypoints |
| `DR-P-013` | object-level completion は、viewer animation、役割ラベル、object-value evidence だけでは許可しない。実体軸、支持ソリッド、実在する力伝達、宣言済み mesh role、未宣言干渉ゼロを geometry-derived mechanical-truth gate で独立に通さなければならない。 | V29 で、見える運動と名称整合だけが pass し、軸も噛み合いもない visual study を completion と誤認した。 | 2026-05-17 user screenshot / V29 false-positive audit、`scripts/validate_v29_mechanical_truth.py` | geometry-derived shaft/support audit、mesh-role coverage、joint-relative motion audit、collision audit | purely visual concept は可。ただし deliverable / goal closure には使わない。 | completion gates、front-loaded workflow、viewer governance |
| `DR-P-014` | 設計案を要求定義や geometry contract として外へ出す前に、選定案は 50 観点成立性スイープを通過しなければならない。出力は思考列ではなく、50 件の pass / fail / residual-risk artifact とする。load-bearing fail が 1 件でもあれば設計案を公開しない。 | V29 では整った案を早く formalize しすぎ、後段でしか見抜けないようにしてしまった。反証の密度を CAD 前へ戻す。 | 2026-05-17 user direction、`docs/front_loaded_design_framework_ja.md`、`docs/pre_cad_design_readiness_checklist_ja.md` | 50-point feasibility sweep validation、selected-design package validation | 小規模な局所試験は 50 件未満でも可。ただし full-object proposal では不可。 | front-loaded workflow、goal admission、design proposal output |
| `DR-P-015` | semantic claim（例: 自律給力、立体駆動、object value、fabrication complete）は、部品名やファイル存在の確認だけでは pass させない。契約、生成ジオメトリ、独立検証が同じ claim を閉じる evidence chain を持たなければならない。 | V30 で、motor / shaft / gear の存在確認だけが winding / spatial / object-value pass に昇格し、意味論的 claim が過大化した。 | 2026-05-18 three-layer audit、`scripts/validate_v30_stationary_winding.py`、`scripts/validate_v30_spatial_drive.py`、`scripts/validate_v30_object_value.py` | contract-traceability gate、claim-strength gate、evidence-binding gate | visual candidate / concept review では存在確認を許す。ただし completion claim には使わない。 | claim taxonomy、goal closeout、semantic validators |
| `DR-P-016` | 既検証コアを再利用しても、新規 train / 新規 frame / 新規高さ遷移を追加した full-object 派生版は、全体系の role / motion / declared-contact / collision / visibility gate を同一世代で再実行しなければならない。 | V30 は V28 の pass を借りて新規 lower train と vertical lift の motion proof を省略した。 | 2026-05-18 three-layer audit、`scripts/validate_v30_mechanical_truth.py`、V28 gate bundle | full-system sampled-motion audit、declared-contact audit、visibility contact sheet、role manifest parity | 部品単体の再利用レビューでは省略可。ただし object completion には不可。 | derivative-design workflow、motion verification、completion gates |
| `DR-P-017` | closeout artifact は、同一 generation identity、current-delivery parity、task-ledger freshness を機械的に照合できなければ completion へ昇格しない。 | V30 で stale `goal_state.json` が pass のまま残り、same-generation / current-delivery の整合も top-layer で強制されていなかった。 | 2026-05-18 three-layer audit、`scripts/write_goal_state.py`、`scripts/write_current_goal_summary.py`、`deliverables/current_delivery.json` | independent freshness validation、completion coherence gate、current-delivery parity gate | 歴史閲覧では不要。ただし最終 claim には必須。 | goal-state、deliverable validation、README sync |

## 3. 仮説 / 未昇格候補

この節の全項目は `status = candidate` とする。

| ID | 分類 | 仮説 | 現在の根拠 | 採用に必要な証拠 | 現在の扱い |
| --- | --- | --- | --- | --- | --- |
| `DR-H-001` | `hypothesis` | FDM 卓上オブジェでは、V26/V27 の `module 1.5` と `running backlash 0.3 mm` が、V25 より造形安定性に有利である。 | `docs/v26_scheme_and_workflow_review_ja.md`、`manifests/tourbillon_v26_mechanical_package.json`、`manifests/tourbillon_v27_connected_contract.json` | プリンタ・材料別の試験片、噛み合い抵抗、組立再現性、摩耗観察 | 版固有の採用値。printer tuning なしで evergreen 化しない。 |
| `DR-H-002` | `hypothesis` | eccentric pin-slot pallet display は、卓上デモ用途で「物理駆動あり」と呼べる最小構成として再利用できる。 | `manifests/tourbillon_v27_connected_contract.json`、`reports/fabrication_v27_connected_package/v27_mechanical_truth_audit.json`、`reports/fabrication_v27_connected_package/v27_sampled_motion_audit.json` | 別版または別レイアウトでの再利用、摩耗 / ガタ / 組立許容差の確認、失敗モード整理 | V27 の有効 contract としては採用済み。ただし系列の一般則にはまだしない。 |
| `DR-H-003` | `hypothesis` | 608ZZ 中央軸受と 3 mm 軸を、この系列の標準ハードウェア既定値として固定すると設計速度が上がる。 | `docs/v26_scheme_and_workflow_review_ja.md`、`manifests/tourbillon_v26_mechanical_package.json`、`manifests/tourbillon_v27_connected_contract.json` | 複数版での組立性、供給性、剛性、DFAM 実績 | 現在は project candidate。寸法自体は evergreen へ上げない。 |
| `DR-H-004` | `hypothesis` | watch-grade escapement を claim するには、lock / drop / impulse の接触物理を gate 化すれば、卓上デモや非調速の卓上機構と同じ repo 内で扱える。 | `docs/mechanism_claim_taxonomy_ja.md`、`scripts/independent_mechanical_truth_audit.py`、`manifests/tourbillon_v27_connected_contract.json` の `blocked_claims` | 接触幾何、拘束、荷重、時系列検証、失敗判定を持つ新 workflow | 現在は blocked claim。実装されるまで「watch-grade」を名乗らない。 |

## 4. Version-specific として隔離する事実

この節の全項目は `classification = version-specific` であり、採用済み規範ではなく証拠保持用の事実である。

以下は重要な証拠だが、永続ルールではない。

| ID | 事実 | 参照 | 隔離理由 |
| --- | --- | --- | --- |
| `DR-V-001` | V26/V27 の歯車値は `module 1.5`、`72T / 18T / 60T / 18T`、backlash `0.3 mm`。 | `manifests/tourbillon_v26_mechanical_package.json`、`manifests/tourbillon_v27_connected_contract.json` | 設計版の数値であり、別スケールへ移れば変わりうる。 |
| `DR-V-002` | V27 の pallet display は eccentric pin-slot で、予測半振れ角は `11.941 deg`。 | `manifests/tourbillon_v27_connected_contract.json` | V27 の具体寸法であり、駆動原理の一般則ではない。 |
| `DR-V-003` | V26 の support split は特定の Z 範囲で pinion / escape wheel と分離した。 | `docs/v26_final_work_plan_and_confidence_ja.md` | 再利用すべきなのは「支持と回転積層を干渉させない」規範であり、座標値ではない。 |

## 5. 昇格 / 改訂 / 棄却の基準

### 5.1 採用条件

候補を `accepted` に上げるには、すべてを満たすこと。

1. `evergreen` / `project-level` / `version-specific` / `hypothesis` の分類が明記されている。
2. `must` / `must not` に相当する、検証可能な規範文で書かれている。
3. 防ぐ失敗モードが説明されている。
4. defect、audit、report、または manifest から一次証拠を引ける。
5. 自動 gate か、人手 checklist に接続されている。
6. 例外条件と、例外時の代替検証がある。
7. workflow、manifest、gate のどこへ効くかが追跡できる。
8. 複数版で再利用できるか、または project-level 制約として固定する意図が明確である。

### 5.2 昇格の流れ

1. 新しい機械的発見が出たら、実行タスクと rule-review タスクを対で起票する。
2. その発見が版固有値だけなら `version-specific` に隔離し、規範へ上げない。
3. 同じ失敗モードが 2 版以上で現れた、または独立監査で重大 defect として再現したら、`candidate` としてこの台帳へ追加する。
4. 採用条件を満たしたら、workflow / manifest schema / gate catalog のどれを変えるかまで同時に記録して `accepted` にする。
5. 物理試作や外部 CAD 証拠が要るものは、証拠が入るまで `hypothesis` のままにする。

### 5.3 改訂・降格・棄却

1. 新しい証拠が例外を広げる場合は、規範より先に例外条件と gate を改訂する。
2. 採用済みルールが別設計で破れる場合は、即時に削除せず、適用範囲を狭めるか `project-level` へ降格する。
3. 候補が一回限りの座標修正、ファイル名、版番号、または生成都合にすぎない場合は、`rejected` として理由を残す。
4. `no durable rule` と判断する場合も、なぜ永続化しないかの証拠を残す。

## 6. 次回レビューで見るべき未解決点

1. `DR-H-001`: 実プリンタ / 材料が決まったら、軸穴・軸受ポケット・backlash coupon を回し、FDM 既定値を昇格できるか判定する。
2. `DR-H-002`: pin-slot display が次版でも使われたら、摩耗・ガタ・組立公差を含む project-level rule に上げるか評価する。
3. `DR-H-003`: 標準ハードウェアの supply / stiffness / assembly 実績を集め、既定値化が設計自由度を損ねないか確認する。
4. `DR-H-004`: watch-grade claim を本当に目指す時だけ、脱進機専用 workflow と gate を別立てする。
