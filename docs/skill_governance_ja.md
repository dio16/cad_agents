# スキル運用ガバナンス（正本）

## 位置づけ

この文書は、再利用可能な workflow / skill / checklist をどう作り、更新し、使い続けるかの正本である。版別レビューや一回限りの作業ログは証拠であり、再利用知として扱うには本書の基準で昇格させる。

このリポジトリの問いは「どう速く geometry を作るか」ではなく、**次の geometry を前回より迷わず、壊しにくく、少ない高コスト反復で作れるようにするには何を再利用資産へ変えるか**である。

## 保存すべき知識の種類

### 1. Workflow

複数工程をまたぐ標準の進め方。例: 機械設計全体、local-first 検証、fabrication package 作成。

### 2. Skill

繰り返し現れる判断や作業を、入力・手順・出力・gate まで含めて再実行可能にした単位。例: 歯車設計、軸受支持、motion verification。

### 3. Checklist

軽量な再発防止のための短い確認表。skill 化するほど大きくないが、見落としやすい条件を閉じる。

### 4. Rule / Gate との境界

- workflow / skill は **どう進めるか** を扱う。
- design rule は **何を満たすべきか** を扱う。
- gate は **満たしたとどう判定するか** を扱う。

同じ発見から、skill 改善と rule-review task の両方が生まれてよい。

## いつ新設・更新するか

次のいずれかに当たる場合、geometry より先に workflow / skill / checklist の新設または改善を検討する。

1. 似た推論を 2 回以上繰り返した。
2. 同種の失敗、見落とし、回避策が再発した。
3. subagent やレビューで、再利用可能な作業手順の欠落が指摘された。
4. 版別レビューの教訓が、将来の版でも使える。
5. ある判断が特定担当者の記憶に依存している。
6. geometry を進める前に、適用 skill が存在しないことが blocker になった。
7. 高価な 3D 検証に入る前に、安価な案比較や成立性確認を再利用できる形にしたい。

「今回はうまくいった」だけでは保存理由にならない。**次回も同じ品質で再現できるか**を基準にする。

## 最小仕様

すべての再利用 skill は、少なくとも次を持つ。

- trigger: いつ使うか
- intended use: 何を解くか
- required inputs: 何がそろえば始められるか
- step sequence: どう進めるか
- expected outputs: 何を残すか
- validation gates: 何で閉じるか
- common failure modes: 何を踏み抜きやすいか
- escalation / stop conditions: どこで止まり、誰へ戻すか
- cheap-before-expensive checks: 重い 3D 前に何を安価に潰すか

加えて、必要なら次も持たせる。

- 入出力のサンプル
- 関連 rule / gate / manifest field
- 使用してはいけない場面
- 依存する backend や資格情報

この最小仕様の監査には `docs/skill_spec_audit_checklist_ja.md` を使う。短い skill は歓迎するが、gate / stop / failure mode が欠けたまま短いだけの skill は未仕様と扱う。

## ライフサイクル

### 1. Capture

版別レビュー、失敗、再作業、subagent 指摘から候補を拾う。

### 2. Classify

次のどれかに分類する。

- 新規 workflow が必要
- 既存 workflow の更新で足りる
- skill 化すべき
- checklist で十分
- process ではなく design rule / gate 側の問題
- 再利用価値なし（理由を明記）

### 3. Author

最小仕様を満たす形へ整える。版番号、特定ファイル名、一時的な数値は本文の中心に置かず、必要なら例示として分離する。

### 4. Validate

次を満たすまで正本にしない。

- 他の agent が入力だけで再実行できる。
- 出力と gate が曖昧でない。
- geometry を早めるだけでなく、誤りを減らす仕組みがある。
- 現行 workflow / rule / gate と矛盾しない。
- 履歴文書ではなく、現在の実務に接続している。

### 5. Reuse

同種タスクが再発したら、まず既存 skill を呼び出す。使わなかった場合は、なぜ適用外かを説明する。

### 6. Review

少なくとも次の場面で見直す。

- 同型失敗が再発したとき
- workflow や backend 方針が変わったとき
- 完了主張の条件が変わったとき
- 版別レビューから新しい durable lesson が出たとき

### 7. Deprecate / Merge

重複、古い backend、誤誘導がある skill は、更新・統合・廃止する。古い知識を沈黙のまま残さない。

## Geometry より先に行う skill 判定

新しい CAD 作業に入る前に、次を確認する。

1. この作業に適用する canonical workflow は何か。
2. 既存 skill で十分か。
3. 足りない skill / checklist はないか。
4. 足りない場合、その不足を埋める方が geometry より優先されるか。
5. その skill が返すべき evidence と gate は何か。

不足がある場合は、skill 改善タスクを作ってから geometry に進む。

## 正本化の手順

版別文書から durable lesson を見つけたら、次の順で昇格する。

1. **抽出**: その版だけの事実と、将来も効く原理を分ける。
2. **一般化**: 特定版の数値やファイル名を外し、再利用可能な表現へ直す。
3. **配置**: workflow / skill / checklist / rule / gate のどこへ置くか決める。
4. **接続**: 必要なら関連 workflow、rule、gate、manifest schema と相互参照する。
5. **検証**: 次の作業者が迷わず使えるかを読む。
6. **履歴化**: 版別文書は削らず、正本へ昇格済みであることが分かる状態にする。

## 品質判定

良い skill は、次の 3 つを同時に満たす。

1. **繰り返しやすい**: 同じ種類の仕事を短く始められる。
2. **間違えにくい**: よくある失敗を手順か gate で先回りして潰す。
3. **学習しやすい**: 新しい発見を次の workflow / skill / rule に渡せる。

## コンテキスト効率

良い skill は、短いだけでなく**必要になった時だけ深くなる**。

1. `SKILL.md` 本体には、trigger、最小手順、gate、stop 条件だけを残す。
2. 長い説明、版別例、補助資料は `references/` へ逃がし、読む条件を `SKILL.md` から明示する。
3. 反復タスクでは、stable instruction と variable evidence を分離し、毎回同じ説明を再注入しない。
4. 既存 skill と canonical doc が同じ規範を持つなら、片方を正本、もう片方を参照にして重複を減らす。
5. 省トークン化は gate、blocker、limitation を削る理由にはならない。
6. 長時間ループの再開に必要な共通入力は各 skill が抱え込まず、`docs/operating_packet_checklist_ja.md` と operating packet artifact を参照する。

## ループ終端の問い

各作業ループの最後に、少なくとも次を確認する。

- 何が再利用可能になったか。
- 何が自動化、checklist 化、skill 化されたか。
- どの失敗が次回は起きにくくなったか。
- 残した lesson は、履歴ではなく正本へ昇格したか。

geometry だけが増え、workflow / skill 側に何も残らないループは、明示的に「再利用改善不要」と説明できない限り未完了である。

## 既存証拠から見える標準姿勢

この正本は、次の既存実践を一般化している。

- V25 で確立した requirements -> topology -> component -> dimensioning -> verification -> CAD の順序
- V26 で強化された manifest-first、BOM / assembly / fabrication package まで含めた成果物定義
- local-first 方針による、ローカル gate 優先と Onshape の補助化
- TASKS / progress ledger に残る、繰り返し発生した skill 強化、text-to-CAD 補助レビュー、長期 subagent 運用の履歴

これらは歴史の断片ではなく、以後の作業を縛る再利用資産として扱う。

## 現在この repo に必要な設計前段 skill

1. `mechanical-concept-feasibility`
   - 複数案比較、motion graph、寸法 budget、failure pre-mortem を CAD 前に閉じる。
2. `kinetic-object-value-design`
   - value brief、hero view、motion legibility、mixed-scale hierarchy、spatial mechanism を定義する。
3. 既存の gear / bearing / DFAM / motion skill
   - 選抜案の成立確認に使い、CAD 後の発見を最小化する。
4. `docs/pre_cad_design_readiness_checklist_ja.md`
   - 大規模 3D へ進む前の軽量停止線として使う。

## 状態遷移の責任分界

| 遷移 | 主責任 | 必須 artifact / gate |
| --- | --- | --- |
| `candidate concept -> selected concept` | `mechanical-concept-feasibility` | 3 案比較（大規模時）、50-point feasibility sweep、棄却理由 |
| `selected concept -> feasible selected design` | concept skill + gear / DFAM / motion / support skills | power / torque / energy、control、tooth-profile、hero-view、buildability の closure |
| `feasible selected design -> geometry-ready` | geometry-contract handoff workflow | fresh handoff artifact、前提保持、downstream consumption |
| `geometry-ready -> implemented geometry` | `tourbillon-cad-completion` | fresh handoff artifact を実際に消費した generator |
| `implemented geometry -> completion` | CAD / motion / object-value validation skills | mechanical truth、sampled motion、declared contact、visibility、deliverable、goal-state |

どの skill も、自分より前の状態遷移を暗黙に再定義してはならない。
