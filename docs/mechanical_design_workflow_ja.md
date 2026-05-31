# 機械設計ワークフロー（正本）

## 位置づけ

この文書は、このリポジトリで再利用する機械設計プロセスの正本である。版別文書は当時の判断・証跡・反省を残す履歴であり、現在の標準手順はこの文書へ昇格してから効力を持つ。

このリポジトリでは、まず truth を壊さず、現在の delivery を支える再利用資産を整え、そのうえで goal gap を継続的に縮める。新しい CAD は目的そのものではなく、要求、契約、検証、学習昇格を通過した設計システムの出力である。

## 適用範囲

- 3D プリンタで製作する可動機構付き卓上オブジェ
- トゥールビオン系の歯車列、支持構造、可視機構を含む設計
- 将来の別機構にも再利用できる、manifest-first / local-first の機械設計作業

## 基本原則

1. **geometry-first を禁止する。** 見た目、色、viewer から始めず、要求から始める。
2. **contract-first で進める。** CAD 生成前に、設計契約、検証項目、制限事項を明示する。
3. **local-first で検証する。** ローカルで答えられる問いはローカル gate で処理し、Onshape は共有・最終レビュー・ローカルで答えられない確認に限定する。
4. **active work は Bash-only とする。** 生成・検証・完了判定は WSL 内の `bash ./run_cad_agent.sh ...` だけを正規入口とし、runner 外の証拠で完了を主張しない。
5. **支持と運動関係を先に閉じる。** すべての可動役割には軸、支持、親フレーム、運動関係が必要で、浮遊部品を許さない。
6. **完成主張は証拠で行う。** viewer、色、静止ポーズだけでは完了としない。数値検証、動作証跡、視認性、制限事項を伴わせる。
7. **学びを履歴に埋めない。** 版別レビューで再利用価値のある発見が出たら、workflow、skill、rule、gate のいずれかへ昇格するまでループは未完了とみなす。
8. **delivery を飢えさせない。** 将来価値だけの改善は台帳に残し、現在の実装経路を壊す reusable gap だけを geometry より先に直す。
9. **読む量ではなく、再読の回数を減らす。** 正本、task-local contract、fresh evidence を分離し、必要箇所だけを読む。詳細は `docs/context_efficiency_playbook_ja.md` に従う。
10. **配布物を証跡と混同しない。** `reports/` 内に証拠があるだけでは handoff 完了ではない。ユーザーが直接使える STL / viewer / preview / BOM / assembly / manifest を stable deliverable として出す。
11. **重い 3D ほど、前段で潰す。** 大きな成果物では `docs/front_loaded_design_framework_ja.md` に従い、成立案の比較と棄却を CAD 前へ寄せる。

## 標準フロー

### 0. 作業許可判定

新しい geometry に入る前に、次を確認する。

- 対象オブジェの種別と完了主張が明示されている。
- 適用する workflow が選択されている。
- 必要な skill / checklist、または不足している skill の作成タスクが特定されている。
- design contract に必要な欄が分かっている。
- full-object work では 50-point feasibility sweep artifact が pass している。
- load-bearing viability が閉じた `feasible selected design` まで昇格している。
- geometry-ready を名乗る場合は、fresh geometry-contract handoff が pass している。
- 検証 gate が列挙されている。
- `P1` truth gap または現在の delivery を壊す `P2` reusable gap が残っていない。

1 つでも満たさない場合は、geometry を始める前に必要な `P1` / `P2` を整える。将来価値だけの改善は queue に残してもよいが、現在の `P3` delivery を止める理由にはしない。

### 1. 要求定義 / value brief

まず、何を作るかではなく、**何を証明したいか**を定義する。

最低限、次を固定する。

- object class（例: 卓上デモ、印刷可能オブジェ、時計級機構）
- 完了語と、その語で主張しない範囲
- 必須の可動役割と見せ場
- 遠景・中景・近景で生む価値
- 立体駆動を価値とするか、その必要性
- 入力の所作（自律給力、手回し、外部駆動など）
- 製造前提、材質、標準部品、許容する簡略化
- 既知の未検証事項と外部依存

### 2. 成立する案の検討

大きな CAD を起こす前に、少なくとも次を行う。

- full-object / 大規模出力では 3 案以上、中規模では 2 案以上の architecture option を、図・表・motion graph で比較する
- 各案で、力の流れ、支持、空間遷移、自律給力入力、見せ場、製造性を一次評価する
- full-object proposal を外へ出す前に 50-point feasibility sweep artifact を pass させる
- 安価に否定できる案を CAD 前に落とす
- 採用案だけに value brief、spatial-drive map、dimension budget、failure pre-mortem、gate matrix を与える

重い 3D 検証は、選抜済み案の確認に使う。探索そのものを CAD に押し付けない。

### 2.5 状態遷移の閉包

大規模作業では、設計案を次の順でしか昇格させない。各段階の go / no-go は `docs/pre_cad_design_readiness_checklist_ja.md` を唯一の checklist 正本として判定する。

1. `candidate concept`
   - 複数案比較と cheap-before-expensive review の対象。
2. `selected concept`
   - 50-point sweep が pass し、価値・構成・運動の筋が通った採用案。
3. `feasible selected design`
   - power / torque / energy、control、tooth-profile、hero-view、buildability の load-bearing closure が pass した案。
4. `geometry-ready`
   - `feasible selected design` の前提を落とさず geometry contract へ写し切り、fresh handoff gate が pass した案。
5. `implemented geometry`
   - `geometry-ready` artifact を実際に消費して生成された CAD。

禁止遷移:

- `candidate concept -> manifest`
- `selected concept -> CAD`
- `feasible selected design -> CAD` without fresh geometry-contract handoff

### 3. 機構トポロジー

次に、部品の見た目ではなく、力と運動の流れを決める。

- 固定要素、入力、出力、回転キャリア、遊星要素などの親子関係
- 各軸の基準、拘束、支持、伝達経路
- 可動部同士の役割分担と重複禁止
- 物理的に存在する部品と、表示上の役割の一致

トゥールビオン系では、固定内歯リング、回転キャリア、軌道ピニオン、キャリア上の脱進機役割のように、内部関係を先に閉じる。

### 4. 部品設計

トポロジーが閉じた後で、部品を選ぶ。

- 歯車形式、軸、軸受、保持部品、橋、ねじ、カラー、スペーサ
- 各可動役割を支える実体部品
- 購入品と印刷品の境界
- 組立順と交換可能性

装飾的な見せ場であっても、表示部品だけを浮かせず、支持部品または明示的な省略理由を持たせる。

### 5. 寸法設計

CAD 前に、少なくとも次を contract 化する。

- 歯数、module、pressure angle
- pitch / base / root / outside dimensions
- center distance、ratio、backlash
- shaft diameter、support span、bearing pocket、retention
- thickness、clearance、tolerance、printer assumption
- material / load assumptions

ここで version 固有の数値を置くことはよいが、再利用可能な規律そのものとは分ける。

### 6. 事前成立性確認

CAD 完了を名乗る前に、必要な gate を先に用意する。

最低限の観点:

- gear pitch / ratio / center distance
- involute or chosen tooth-profile validity
- undercut / backlash / clearance
- shaft / bearing / support continuity
- support graph and no-floating-part
- collision and sampled-pose interference
- visibility / contact-sheet evidence
- object-value brief / hero-view / kinetic-object review
- spatial-drive map / autonomous-winding path
- BOM / assembly-sequence completeness
- completion wording と limitation の整合

通常は local gate を先に使う。ローカルで判定できる bbox、体積、solid interference、clearance、transform pose、snapshot、fabrication package は Onshape API に委ねない。

### 7. CAD 生成

生成は contract の後でのみ行う。

- generator は manifest / contract を入力の正とする。
- STEP / STL / GLB / HTML / report は artifact であり、契約や generator より上位ではない。
- 生成物は contract の各項目へ追跡できる必要がある。
- viewer は補助証跡であり、単独では完了証明にならない。

### 8. レビューと完了判定

レビューでは、契約と証跡の閉包に加え、value brief が実装後も失われていないか確認する。

- moving role に支持、親フレーム、運動関係があるか
- gear / shaft / bearing / clearance の数値が整合するか
- sampled motion で干渉や役割矛盾がないか
- 見せ場が sampled pose でも可視か
- 遠景の彫刻性、中景の可読性、近景の精緻さ、時間的リズム、立体駆動の必然が残っているか
- 完了語が実際の gate 範囲を超えていないか
- 制限事項が report に明記されているか

## ローカル優先の実行順

標準の流れは次の順とする。

1. value brief / concept option review
2. pre-CAD feasibility package review
3. selected-design feasibility closure review
4. geometry-contract handoff review
5. manifest contract review
6. local geometry generation
7. STEP / STL / GLB export
8. local bbox / volume / single-solid / topology checks
9. gear / clearance / support / hardware context checks
10. local transform contract and sampled poses
11. rendered snapshot / contact-sheet / kinetic-object review
12. fabrication package validation
13. user-consumable deliverable validation
14. 条件を満たす場合のみ optional Onshape review

## ループ終端と知識昇格

各反復の終わりに、次を確認する。

1. 何が再実行しやすくなったか。
2. 何が誤りにくくなったか。
3. どの学びを履歴から再利用可能な資産へ昇格したか。

昇格先は次のいずれかである。

- workflow
- skill / checklist
- design rule
- validation gate
- manifest schema / template

版別文書だけに残る学びは、まだ知識資産としては未完成である。

## ゴール差分を閉じる継続ループ

1. `reports/current_gate_summary.json` が pass でも、その claim が `GOAL.md` より狭いなら最終完了ではない。
2. 未解決の goal gap は、外部入力、認証情報、UI 専用証拠、またはユーザー判断が必要な blocker でない限り、active task として維持する。
3. 各 gate 後に、最終ゴールとの差分を最も小さく縮める次の `P3` task を選ぶ。
4. その task を壊す workflow / skill / rule / gate の不足がある時だけ、先に `P2` へ戻る。
5. 部分完了は停止理由ではなく、次に閉じる差分を選ぶための中間証拠として扱う。

## コンテキスト効率の補助ルール

詳細は `docs/context_efficiency_playbook_ja.md` を正本とする。  
この workflow では、その playbook に従い、必要な正本・task-local contract・fresh evidence だけを段階的に読む。

## 正本と履歴の分離

- この文書: 現在の再利用可能な進め方
- 版別 workflow / review 文書: その版で何が起き、なぜ改善が必要になったかの証拠
- manifest: 個別設計の契約
- scripts / reports / viewer: 実装と証跡

新しい版で手順が改善されたら、まずこの正本を更新し、そのうえで版別文書へ具体例を残す。
