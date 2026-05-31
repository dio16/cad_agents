# 機構 claim taxonomy

この文書は、卓上トゥールビオン系列の completion claim を、見た目ではなく**物理駆動経路と検証済み範囲**で分けるための正本である。  
目的は、`demonstrator` を過小評価せず、同時に `watch-grade` を先取りして名乗らないことである。

注記: この文書は機構 claim の正本であり、完成オブジェとしての価値 claim は `docs/kinetic_object_value_framework_ja.md` が扱う。現在の repository goal は、機構 claim だけでなく object-value claim も要求する。

## 1. 基本原則

1. claim の階層は、役割名ではなく、物理経路・支持・拘束・検証 gate の深さで決める。
2. `DR-E-003` に従い、機械動作を主張するロールには視覚アニメーションではなく物理的な駆動経路が必要である。
3. `DR-P-002` に従い、卓上デモ、機械駆動された卓上機構、watch-grade、native CAD、物理試作は混同しない。
4. 上位 claim を名乗るには、下位 claim の要件に加えて、その差分を埋める追加契約と gate が必要である。
5. 物理的に閉じていないロールは、表示部品として存在してもよいが、completion wording では必ず限定語と blocked claim を併記する。

## 2. claim の 3 階層

| 階層 | 許される claim | 必須の実体 | まだ要求しないこと | 代表的 blocked claim |
| --- | --- | --- | --- | --- |
| `demonstrator` | 卓上デモ、gear-train demonstrator、visual / kinematic display | 宣言した見せ場までの物理経路、各可動ロールの支持、限定語 | balance までの閉じた駆動連鎖、時計級接触物理 | `mechanically driven tabletop mechanism`、`regulating balance`、`watch-grade escapement` |
| `mechanically-driven-tabletop-mechanism` | 非調速の実演用脱進機を備えた、機械駆動の卓上トゥールビオン機構 | `hand -> carrier -> ring/orbit -> escape -> pallet -> balance` の物理経路、balance 側受動子、全可動ロールの支持と sampled motion | 調速、自己持続振動、時計精度、lock / drop / impulse の時計級検証 | `regulating balance`、`self-sustaining oscillation`、`timekeeping accuracy`、`watch-grade escapement` |
| `watch-grade` | watch-grade escapement、regulating balance、時計機構としての claim | 上位の物理経路に加え、lock / drop / impulse、エネルギー伝達、調速挙動、接触物理の専用契約と gate | なし。追加で物理試作を名乗るなら別証拠が必要 | `physical print proven` は依然として別 claim |

### 2.1 階層の切れ目

```text
demonstrator
  hand -> carrier -> ring/orbit -> escape -> pallet
                                           balance may be visual-only

mechanically-driven-tabletop-mechanism
  hand -> carrier -> ring/orbit -> escape -> pallet -> balance
                                                       non-regulating

watch-grade
  hand -> carrier -> ring/orbit -> escape -> pallet -> balance
                                                       + lock/drop/impulse
                                                       + regulation physics
```

## 3. 現在の V27 truth

V27 は、次の理由で `demonstrator` 階層に属する。

1. `manifests/tourbillon_v27_connected_contract.json` は、`tabletop tourbillon-inspired gear-train demonstrator` と明記している。
2. 同 manifest の `escapement_drive_model` は、`escape shaft -> pallet` の eccentric pin-slot 駆動を持つ一方で、`watch-grade escapement`、`regulating balance`、`lock/drop/impulse verified` を blocked claim に置いている。
3. `reports/fabrication_v27_connected_package/v27_role_manifest.json` では、`balance_wheel.motion = supported visual hardware only` であり、balance は物理駆動経路の外にある。
4. よって V27 は強い卓上デモであるが、`balance` まで閉じた「機械駆動の卓上トゥールビオン機構」ではまだない。

## 4. V28 の受入 claim

V28 が目指すべき最小の真実な一段上の claim は、次である。

> **非調速の実演用脱進機を備えた、機械駆動の卓上トゥールビオン機構**  
> `mechanically driven tabletop tourbillon mechanism with a non-regulating demonstrative escapement`

これは `watch-grade` ではない。  
V27 との差分は、**balance を visual-only から物理駆動連鎖へ入れること**だけである。

## 5. V28 最小 contract

### 5.1 必須ロール

1. `fixed_internal_ring`
2. `hand_input_pinion`
3. `carrier_drive_gear`
4. `rotating_carrier`
5. `orbit_escape_pinion`
6. `escape_wheel`
7. `pallet_fork`
8. `balance_wheel`
9. `balance_roller_pin` または同等の balance 側受動子
10. 上記すべてに対する `axis / support / parent frame`

### 5.2 必須の物理関係

1. `hand_input_pinion -> carrier_drive_gear` は物理的な噛み合いを持つ。
2. `fixed_internal_ring -> orbit_escape_pinion` は物理的な噛み合いを持ち、carrier 回転に対する相対スピンを生む。
3. `orbit_escape_pinion -> escape_wheel` は同軸剛結である。
4. `escape_wheel -> pallet_fork` は明示的な物理接触または拘束で pallet swing を生む。
5. `pallet_fork -> balance_wheel` は明示的な物理接触または拘束で balance oscillation を生む。
6. 全可動ロールは支持され、全周期 sampled motion で未宣言干渉がない。
7. 主要可動ロールは代表姿勢で可視である。

### 5.3 最小の許容実装

V28 の最小差分としては、次を認める。

1. V27 の `eccentric pin-slot pallet display` を `escape_wheel -> pallet_fork` の駆動として継続利用する。
2. `pallet_fork` に出力アームと出力ピンを追加する。
3. `balance_wheel` に受けスロットまたは roller-pin 相当を追加し、`pallet_fork -> balance_wheel` の物理拘束を閉じる。
4. この coupling は**非調速の実演用**でよく、時計級の lever escapement である必要はない。

### 5.4 必須 gate

1. drive-chain continuity gate  
   `hand -> carrier -> orbit/escape -> pallet -> balance` が manifest 上で連続する。
2. balance-drive geometry gate  
   pallet 出力と balance 側受動子が全姿勢で bounded contact を保つ。
3. sampled full-cycle motion gate  
   pallet と balance が manifest-derived transform で動き、visual-only sine motion を使わない。
4. declared contact gate  
   `escape <-> pallet` と `pallet <-> balance` の意図した接触だけが bounded contact として存在する。
5. collision / visibility gate  
   長い pallet arm、balance、carrier 周辺の干渉がなく、主要可動ロールが代表姿勢で見える。
6. claim-boundary gate  
   `mechanically-driven-tabletop-mechanism` は許可し、`watch-grade` / `regulating balance` / `lock-drop-impulse verified` は引き続き拒否する。

### 5.5 明示的に除外する claim

V28 が満たしても、次は名乗らない。

- `watch-grade escapement`
- `regulating balance`
- `self-sustaining oscillation`
- `timekeeping accuracy`
- `lock/drop/impulse verified`
- `energy-storage / torque-transfer validated`
- `physical print proven`

## 6. claim 判定の実務ルール

1. `balance_wheel` が visual-only なら、completion wording は必ず `demonstrator` に留める。
2. `balance_wheel` が物理経路へ接続され、5.2 と 5.4 を満たした時だけ、`mechanically-driven-tabletop-mechanism` を名乗ってよい。
3. `lock / drop / impulse` の専用契約と検証 gate がない限り、`watch-grade` を名乗ってはならない。
4. 新しい claim を追加したい時は、先にこの taxonomy を更新し、次に manifest と gate を更新する。

## 7. 根拠

- `docs/design_rule_register_ja.md` の `DR-E-003`, `DR-P-002`
- `manifests/tourbillon_v27_connected_contract.json`
- `reports/fabrication_v27_connected_package/v27_role_manifest.json`
- `reports/fabrication_v27_connected_package/v27_mechanical_truth_audit.json`
- `reports/fabrication_v27_connected_package/v27_sampled_motion_audit.json`
- `reports/current_gate_summary.json`
