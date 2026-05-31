# 長時間ループ用 Operating Packet チェックリスト

この文書は、長時間ループを再開する時に読む最小パックの正本である。目的は、真実を削ることではなく、再起動のたびに同じ選別をやり直さないことにある。

## 1. 先に読む順序

1. `GOAL.md`
2. `AGENTS.md` の authority / priority / turn-end / router 節
3. `reports/current_operating_packet.md` または `reports/current_operating_packet.json`
4. router が指す canonical doc を 1 つだけ
5. 必要なら `reports/progress_ledger.jsonl` の最新 1〜3 件

`TASKS.md` の全文、履歴 report、版別 docs は、packet が stale、artifact archaeology が必要、または個別修正に入る時だけ読む。

## 2. Packet に必ず入れるもの

- current claim と completion wording
- unresolved goal gap
- open active tasks
- active / blocked sidecars
- open emergent inbox
- current external blockers
- open next queue
- current delivery / current goal summary / goal-state freshness の参照先
- router 上の次に読むべき canonical doc

## 3. sidecar へ渡す最小情報

- `Role`
- `Scope`
- `Do not modify`
- `Blocking question`
- `Evidence required`
- `Stop condition`
- 再利用 agent には前回結論からの delta のみ

## 4. restart 時の禁止

- packet があるのに、いきなり `TASKS.md` 全文や古い iteration ledger を読む
- cold history を live state と同じ重さで扱う
- current claim を README の版番号や過去の package 名から推測する
- 最新 1〜3 件で足りるのに ledger 全体を毎回読み直す

## 5. 完了条件

- 5 分以内に「今の claim / 残 gap / 次の 1 手 / 使う canonical doc」が言える
- stale packet や entrypoint drift があれば `P1` として即時修正される
- packet を短くするために blocker、gate、limitation を削っていない
