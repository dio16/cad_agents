# Codex 運用整合プレイブック

この文書は、OpenAI 公式の Codex 運用原則を、この repo の長時間 CAD ループへ翻訳した正本である。目的は、ルールを増やすことではなく、すでにある良い仕組みを **止まりにくく、迷いにくく、再利用しやすく** することにある。

## 1. 公式原則との対応

| 公式 Codex 原則 | repo での採用形 |
| --- | --- |
| durable goal を持つ | `GOAL.md` と turn-end goal-state gate |
| hard task は eval-driven loop で改善する | 各反復は focused change -> gate -> artifact の順で閉じる |
| 反復する仕事は skill 化する | `docs/skill_governance_ja.md` と skill audit checklist |
| verified operations は proof artifact まで確認する | pass/fail を report / validator / viewer artifact で残す |
| subagents は独立した並行仕事に使う | bounded sidecar prompts と role reuse |
| `AGENTS.md` は短く実務的に保つ | 詳細は canonical docs へ逃がし、`AGENTS.md` は authority / constraints / router を優先 |

## 2. 長時間ループの標準サイクル

1. operating packet を読む
2. 最高優先の unblocked task を 1 つ選ぶ
3. 独立 sidecar が有効なら並列に走らせる
4. 1 回に 1 つの focused change を行う
5. gate を再実行し、proof artifact を確認する
6. durable lesson を workflow / skill / checklist へ昇格する
7. 次の smallest trustworthy task を queue へ戻す

## 3. repo 固有の差分補正

### 3.1 Fail に陥りやすい差分

- mutable current state を README に手書きで複製する
- live ledger に cold history を積み続ける
- skill の最小仕様を要求しているのに、実スキル側が欠けたままになる
- closeout artifact の pass を current goal path へ自動継承してしまう

### 3.2 効率を落とす差分

- 同じ pre-CAD admission を複数文書で再説明する
- generic operating doctrine を project-specific skill が抱え込みすぎる
- ledger 全文や長い履歴を毎回読み直す

## 4. 実装上の方針

- current truth は artifact / ledger / canonical docs のいずれか 1 箇所だけを正とする
- `AGENTS.md` は短い practical contract、詳細は canonical docs へ
- skill は「必要時だけ深くなる」構造にする
- 並列化は独立した問いにだけ使い、同じ問いを複数 agent へ重複配布しない
- output は status narration ではなく、gate / artifact / next task で閉じる

## 5. ループ終端の確認

- 今回の反復は goal gap を縮めたか
- 同じ失敗を次回起こしにくくしたか
- 次の再開時に読む量を減らしたか
- current truth を複製して drift を増やしていないか
