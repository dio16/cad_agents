# コンテキスト効率プレイブック

この文書は、長時間走る CAD エージェント作業で、**品質を落とさず再読と再説明を減らす**ための正本である。  
目的は、短く話すことではなく、同じ真実を何度も読み直さずに済む構造を作ることである。

## 1. 基本方針

1. **真実は一度だけ正本へ置く。**  
   繰り返し使う原則は `AGENTS.md`、workflow、rule register、manifest schema のいずれかへ昇格し、版別文書や task note へ重複定義しない。
2. **読む順番を固定する。**  
   迷ったら `GOAL.md -> AGENTS.md の該当節 -> TASKS.md の current / active / next -> 当該 contract` の順で読む。
3. **全読より先に絞り込む。**  
   まず `rg` / `grep` / `sed -n` / `jq` で必要箇所を抜き、必要になった時だけ全文を読む。
4. **差分を読む。**  
   既知の sidecar や artifact を再利用する時は、前回から変わった点だけを問う。
5. **長文は仕組みに逃がす。**  
   何度も使う手順は script / checklist / reference に置き、毎回プロンプトへ再注入しない。
6. **要約は判定に寄せる。**  
   ledger や final は、背景を繰り返すより `何が変わったか / どの gate が通ったか / 次は何か` を優先する。
7. **再開時は operating packet から入る。**  
   長時間ループでは `docs/operating_packet_checklist_ja.md` に従い、最新 packet を入口にしてから raw ledger や履歴を掘る。

## 2. 実行時の最小読み込み順

| 状況 | まず読む | 追加で読む条件 |
| --- | --- | --- |
| 作業再開 | `GOAL.md`, `TASKS.md` current / active / next | priority や claim が曖昧なら `AGENTS.md` |
| 新しい CAD 実装 | 対象 manifest、該当 workflow、required gates | rule 解釈が必要なら design-rule register |
| 監査 | 対象 artifact、fresh report、該当 gate script | 原因追跡時のみ generator |
| 歴史調査 | canonical doc で不足した論点 | 版別 `v*` 文書を限定的に読む |
| sidecar 再利用 | 前回結論、今回の差分、対象 artifact | 全履歴再投入はしない |

長時間ループの再開では、上表の raw file 読みより先に `reports/current_operating_packet.md` を読む。packet が stale、または packet 自体を編集する時だけ `TASKS.md` へ戻る。

## 3. 文書設計ルール

1. 正本は短く、履歴は長くてよい。
2. 同じ説明を 2 箇所へ書く時は、片方を正本、もう片方をリンクへ変える。
3. skill 本体は手順の骨だけを持ち、詳細例・補足・長い説明は `references/` へ逃がす。
4. 可変情報は `TASKS.md`、manifest、report へ置き、stable prompt / stable rule と分ける。
5. 「何を読めば足りるか」を各 workflow / skill が示す。
6. append-only ledger は通常再開では最新 1〜3 件だけ読み、全件読込は archaeology / regression analysis の時だけにする。

## 4. sidecar 運用

1. 新規 sidecar は、役割・対象ファイル・ blocking question を絞って渡す。
2. 再利用 sidecar には「前回からの差分」だけを聞く。
3. 同じ問いを複数 agent に配るのは、独立仮説比較が必要な時だけにする。
4. full-history 再読が必要ないなら、repo path と対象 artifact だけを渡す。
5. agent limit で sidecar を増やせない時は、既存 sidecar の再利用を優先し、制限を `TASKS.md` に記録する。

## 5. 実務チェックリスト

- [ ] いま読むべき正本は 1 つに絞れているか
- [ ] `sed -n` / `rg` で足りるのに全文を読もうとしていないか
- [ ] 既知の結論を再説明せず、差分だけ扱えているか
- [ ] 長い手順を prompt ではなく skill / reference / script に逃がせているか
- [ ] ledger は背景より判定と次手を優先しているか
- [ ] 省トークン化で evidence や gate を削っていないか
- [ ] operating packet で足りるのに raw ledger 全文を読もうとしていないか

## 6. 根拠

- OpenAI の prompt caching ガイドは、静的な共通 prefix を前方へ、可変情報を後方へ置くことを推奨している。
- OpenAI の latency optimization ガイドは、巨大なコンテキストでは入力を絞ること、出力量を減らすこと、重複しない並列化を使うことを勧めている。
- この repo 自身でも、版別知識を canonical doc へ昇格した後の方が、再説明より task-local evidence に集中しやすい。

## 7. 禁止

次は「節約」ではなく品質低下なので禁止する。

- 必須 gate の省略
- blocker の隠蔽
- completion claim の短縮による過大主張
- 根拠 artifact を読まずに既知結論だけを再利用すること
- 歴史証拠が必要なのに正本だけで済ませたふりをすること
