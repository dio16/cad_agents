# Pre-CAD 設計成立性チェックリスト

この文書は、`candidate concept -> selected concept -> feasible selected design -> geometry-ready` の go / no-go を判定する唯一の checklist 正本である。  
大規模な 3D 生成へ進む前に、選定済み案が次を満たすことを確認する。

## 1. Claim / value

- [ ] 何を名乗り、何を名乗らないかが明示されている
- [ ] value brief があり、遠景 / 中景 / 近景の価値が定義されている
- [ ] 自律給力、立体駆動など、価値として名乗る要素が contract 化されている

## 2. Mechanism

- [ ] drive chain が入力から出力まで閉じている
- [ ] 各可動ロールに predecessor / successor / physical relation がある
- [ ] DOF と拘束が説明できる
- [ ] 支持、軸、保持、親フレームが全可動ロールにある
- [ ] 歯数、ratio、center distance、backlash の一次整合が済んでいる
- [ ] 入力源から出力までの torque / power / energy budget が一次閉包している
- [ ] 自律給力を名乗る場合、winding control、clutch / end-stop、overwind 対策が説明できる
- [ ] 歯形の undercut / tooth thickness / tip-root clearance の一次成立が確認されている

## 3. Spatial / form

- [ ] 立体駆動を名乗る場合、異なる高さまたは軸方向への実在の伝達がある
- [ ] hero view で力の流れが追える
- [ ] 大きな構造が見せ場を隠していない
- [ ] 高速微小部と大きな彫刻形状の hierarchy が意図的である

## 4. Buildability

- [ ] 標準部品、軸受、ねじ、保持方法が仮決定されている
- [ ] print orientation、壁厚、support risk、assembly access を一次確認した
- [ ] 組立順が概念段階で成立する
- [ ] swept envelope と主要な衝突予約を 2D / symbolic に確認した

## 5. Selection hygiene

- [ ] full-object / 大規模出力では 3 案以上、中規模では 2 案以上を比較した
- [ ] 選定案に 50-point feasibility sweep artifact があり、50 観点の結果が記録されている
- [ ] load-bearing な fail が 0 件である
- [ ] 棄却案と棄却理由が残っている
- [ ] 採用案の top 5 failure modes が書かれている
- [ ] 重い 3D で初めて分かることと、CAD 前に潰せたことを分けた
- [ ] 局所 3D モジュールを使う場合、各モジュールに learning objective / pass criterion / non-claim がある

## 6. Cross-module integration

- [ ] 複数モジュールを組む場合、module 間の input / output handoff が 1 対 1 で閉じている
- [ ] 共有する axis / frame / centerline / height が一致している
- [ ] reserved envelope、contact zone、hero-view occlusion budget が full CAD 前に宣言されている
- [ ] 組立順が module 境界をまたいでも成立する

## 7. Selected-design feasibility closure

- [ ] power-path feasibility contract が pass している
- [ ] tooth-profile feasibility が pass している
- [ ] hero-view layout / occlusion review が pass している
- [ ] pre-CAD buildability review が pass している
- [ ] load-bearing な未解決 non-claim が geometry readiness から除外されている
- [ ] geometry contract handoff が pass し、`feasible selected design` の前提を落としていない

## Go / No-go

- 1 つでも重大未了があれば、full CAD へ進まない。
- 小さな局所モジュール試験は可。ただし全体形状の探索を 3D に押し付けない。
