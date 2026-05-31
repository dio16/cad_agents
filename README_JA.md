# CAD Agent Framework

Codex で機構設計を進めるための、local-first / WSL-first の CAD 自動化基盤です。
このリポジトリの正本は `GOAL.md`、運用規範は `AGENTS.md`、実行台帳は `TASKS.md` です。

## リポジトリのゴール

机上で静止していても自律的に巻き上がる給力機構を持ち、全体は大胆なキネティック・スカルプチャー、細部は時計のように精緻で、力の流れが立体空間を横断する卓上トゥールビオン機構オブジェを、3Dプリンタで製作可能な3Dモデルとして完成させます。

ただし優先順位は、重複を減らし実作業を飢えさせないため、次の通りです。

1. `P1` Operational Integrity / Truth
2. `P2` Reusable Design System
3. `P3` Goal Delivery / Evidence Production
4. `P4` Optional Optimization / Exploration

部分完了で停止せず、`GOAL.md` との差分が残る限り、外部 blocker でない未解決 gap は active task として残します。

## 基本コマンド

```bash
cd /home/diobrando/codex_wsl/cad_agent_framework
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json status
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json validate
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v28_mechanism_contract.json completion-status
```

上の 3 行は過去の mechanism package 例であり、現在の active goal path そのものを表すものではありません。実作業では、まず `TASKS.md` と router で指示された canonical workflow を読み、そこに記載された manifest を使います。

## 役割

- `GOAL.md`: ゴールと優先順位の正本
- `AGENTS.md`: 実行ルールの正本
- `TASKS.md`: ライブタスク台帳
- `cad_agent/onshape_client.py`: Onshape REST API クライアント
- `cad_agent/workflow.py`: import / assembly / pose / check の標準ワークフロー
- `cad_agent/transforms.py`: Assembly transform 用の 4x4 行列
- `manifests/*.json`: 設計契約
- `docs/mechanical_design_workflow_ja.md`: 再利用する機械設計ワークフローの正本
- `docs/front_loaded_design_framework_ja.md`: 3D 前に成立案を絞る設計前段フレームワークの正本
- `docs/fifty_point_feasibility_sweep_ja.md`: 設計案を外へ出す前の 50 観点成立性スイープの正本
- `docs/kinetic_object_value_framework_ja.md`: キネティック・オブジェ価値定義の正本
- `docs/skill_governance_ja.md`: workflow / skill 運用の正本
- `docs/design_rule_register_ja.md`: 設計ルール台帳の正本
- `docs/context_efficiency_playbook_ja.md`: 最小読込とコンテキスト効率の正本
- `docs/operating_packet_checklist_ja.md`: 長時間ループ再開 packet の正本
- `docs/skill_spec_audit_checklist_ja.md`: reusable skill 最小仕様監査の正本
- `docs/codex_operating_alignment_ja.md`: 公式 Codex 運用との整合正本
- `reports/current_goal_summary.json`: 現在の claim 要約
- `reports/goal_state.json` と `reports/goal_state_freshness.json`: 最終ゴール閉包で同時に pass が必要な artifact

## 現在の前提

- active work は必ず WSL 内の Bash から `bash ./run_cad_agent.sh ...` で実行します。
- PowerShell、`pwsh`、`cmd.exe`、direct `python`、direct `cad_agent_cli.py` は active-work entrypoint として使いません。
- Bash runner 外の証拠は完了 claim の根拠に使いません。
- 通常反復は local-first で進め、Onshape は最終レビューや local gate で答えられない場合にだけ使います。
- claim 文言は `reports/current_goal_summary.json` に従います。最終完了は `reports/goal_state.json` と同ターンで再検証した `reports/goal_state_freshness.json` がともに pass した時だけです。
- 「現在」を README 内の版番号から推測しません。機械向け入口は `deliverables/current_delivery.json`、人向け入口は `deliverables/README_JA.md`、現在の claim / limitation は `reports/current_goal_summary.json` を見ます。
- `deliverables/current_delivery.json` は最新の公開ハンドオフ先を示し、`reports/current_goal_summary.json` はそれが完成証拠なのか candidate package なのかを示します。別の文書と食い違う場合は、`TASKS.md` とこれらの artifact を正として drift を修正します。
- V28 は旧ゴールに対する baseline evidence として残し、active goal の完了主張には使いません。
- Native Onshape 証拠と物理試作証拠はまだ claim の外側です。
