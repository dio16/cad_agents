# Codex Operating Gap Audit — 2026-05-18

## Verdict

この repo はすでに Codex 公式運用の中核とは整合している。

- durable goal: `GOAL.md`
- eval-driven improvement loop: fail-closed validators + gate artifacts
- verified operations: report / viewer / validation artifact を確認してから claim
- reusable work: canonical workflow と skill governance
- parallel specialized agents: bounded sidecar roles と reuse tracking

今回の問題は「原則がない」ことではなく、**強い原則の周辺に古い入口と重い hot path が残り、正しい原則へ到達するまでに misrouting と無駄読込が起きる**ことだった。

## Gap Findings

1. `README.md` / `README_JA.md` が mutable current state を手書きで複製し、`TASKS.md` と drift していた。
2. `TASKS.md` が hot ledger と historical archive を兼ね、現在の実行経路が cold history に埋もれていた。
3. 長時間再開用の compact operating packet がなく、毎回 raw docs から最小セットを再構成していた。
4. `skill_governance` の最小仕様と実スキル群の仕様密度に差があり、読者が欠けた gate / stop / failure mode を補完していた。
5. `tourbillon-cad-completion` が generic operating doctrine まで抱え込み、project-specific glue として太りすぎていた。

## Actions Taken

- README を stable artifact pointer 化し、current state を `current_delivery` / `current_goal_summary` へ一本化。
- `TASKS.md` を hot ledger へ縮退し、cold history を `reports/task_history_2026-05-18.md` へ退避。
- `docs/operating_packet_checklist_ja.md` と `scripts/write_current_operating_packet.py` を追加。
- `docs/skill_spec_audit_checklist_ja.md` と `docs/codex_operating_alignment_ja.md` を追加。
- `docs/pre_cad_design_readiness_checklist_ja.md` を pre-CAD admission の唯一 checklist 正本として明示。
- `tourbillon-cad-completion` skill を canonical-doc 参照型へスリム化。
- `AGENTS.md` に hot-ledger、conditional-backlog freshness、structured active-task detail、stable entrypoint の規範を追加。

## Deliberate Non-Changes

- design-rule register には新規 operating rule を追加しなかった。今回の発見は機械設計の normative rule ではなく、workflow / checklist / docs の責務である。
- strict gate、strict wording、goal-state freshness は削らなかった。削減対象は gate そのものではなく、そこへ至る重複説明である。

## Residual Work

- 既存の専門 skill 群は、今後 `docs/skill_spec_audit_checklist_ja.md` で順次最小仕様監査を行う。
- `AGENTS.md` はまだ 25 KB 台で、公式の「short, practical」精神に対して十分に軽いとは言い切れない。今回の loop では first-pass slim 化に留め、さらなる分割は次の再発証拠が出た時に行う。
