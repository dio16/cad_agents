# 50 観点成立性スイープ（正本）

大規模な設計案を要求定義や geometry contract として外へ出す前に、main agent は次の 50 観点を内部で確認し、  
機械可読な `reports/<design_id>_internal_feasibility_sweep.json` に要約だけを残す。

## A. Claim / value

1. claim が一文で明確
2. non-claim が明確
3. ゴール価値と案が一致
4. 遠景価値がある
5. 中景で力の流れが追える
6. 近景で精緻さがある
7. 立体駆動の価値が必然

## B. Mechanism topology

8. 入力から出力まで drive chain が閉じる
9. 全可動ロールに predecessor がある
10. 全可動ロールに successor がある
11. 物理関係が表示アニメーションではなく実体
12. DOF が説明できる
13. 拘束過多がない
14. 拘束不足がない
15. 回転軸が実在する
16. 支持体が実在する
17. 軸方向の保持がある

## C. Gear / transmission

18. 歯数が定義済み
19. ratio が定義済み
20. center distance が閉じている
21. backlash 仮定がある
22. undercut risk がない
23. tip/root clearance が説明できる
24. mesh role が geometry で表せる
25. spatial transition が実在伝達
26. viewer motion が joint-relative で表せる

## D. Power / energy

27. 入力源が定義済み
28. torque budget が一次閉包
29. speed budget が一次閉包
30. energy / holdover が一次閉包
31. winding control がある
32. reverse-flow protection がある
33. overload / overwind protection がある

## E. Support / DFAM / assembly

34. 標準部品が仮決定
35. 軸径とクリアランスが整合
36. 2 点支持が必要箇所で確保
37. 壁厚が成立
38. print orientation が成立
39. support risk が把握済み
40. tool access がある
41. assembly order が成立
42. maintenance / replacement access がある

## F. Spatial / visual integration

43. hero view で主経路が見える
44. 可動部が大物に隠れない
45. slow / medium / fast の hierarchy が読める
46. silhouette が object goal に合う
47. occlusion budget が許容内

## G. Validation / reuse

48. expensive 3D で初めて知ることが限定済み
49. geometry-derived mechanical-truth gate が定義済み
50. 今回の学びが reusable rule / workflow へ戻せる

## Artifact contract

各 sweep artifact は最低限次を持つ。

- `design_id`
- `proposal_artifact`
- `created_at`
- `status`
- `checks`（ちょうど 50 件）
- `pass_count`
- `blocking_failures`
- 各 check の `id / name / status / evidence_ref / blocking_reason`

`blocking_failures` が 1 件でもあれば、設計案は外へ出してはならない。
