# CAD Agents

local-first / WSL-first のエージェンティック CAD 自動化基盤です。

このリポジトリの正本は `GOAL.md`、仕様は `SPEC.md`、運用規範は `AGENTS.md`、実行台帳は `TASKS.md` です。

## ゴール

机上で静止していても自律的に巻き上がる給力機構を持ち、全体は大胆なキネティック・スカルプチャー、細部は時計のように精緻で、力の流れが立体空間を横断する卓上トゥールビオン機構オブジェを、3Dプリンタで製作可能なモデルとして完成させます。

## 優先順位

1. `P1` Operational Integrity / Truth
2. `P2` Reusable Design System
3. `P3` Goal Delivery / Evidence Production
4. `P4` Optional Optimization / Exploration

部分完了で停止せず、`GOAL.md` との差分が残る限り、外部 blocker でない未解決 gap は active task として残します。

## セットアップ

```bash
git clone https://github.com/dio16/cad_agents.git
cd cad_agents
uv venv --python 3.12
uv pip install -e .
```

## 基本コマンド

```bash
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v31_geometry_contract.json status
bash ./run_cad_agent.sh --manifest manifests/tourbillon_v31_geometry_contract.json completion-status
```

利用可能なコマンド: `status`, `completion-status`, `local-backend-status`, `local-fabrication-audit`, `local-assembly-export`, `local-completion-status`, `local-pose-snapshots`, `check`, `motion`, `solid-audit`, `hardware-context-audit`, `motion-preview`

## 運用方針

- active work は必ず WSL 内の Bash から `bash ./run_cad_agent.sh ...` で実行します。
- PowerShell、`pwsh`、`cmd.exe`、direct `python`、direct `cad_agent_cli.py` は active-work entrypoint として使いません。
- Bash runner 外の証拠は完了主張の根拠に使いません。

## ディレクトリ構成

- `GOAL.md`: ゴールと優先順位の正本
- `SPEC.md`: プロジェクト仕様（スコープ、バックエンド戦略、I/O スキーマ）
- `AGENTS.md`: 実行ルールの薄いランチャー
- `TASKS.md`: ライブタスク台帳
- `cad_agent/workflow.py`: ローカルワークフロー（干渉検証、モーション、完成度など）
- `cad_agent/transforms.py`: 4x4 変換ヘルパー
- `manifests/*.json`: 設計契約
- `docs/`: 設計ワークフルール / 設計ルール台帳 / スキル運用など canonical 文書
- `scripts/`: 生成・検証スクリプト
- `reports/`: ゲート・検証レポート
- `deliverables/`: 現在の fabrication package

## ライセンス

Apache-2.0 — 詳細は [`LICENSE`](./LICENSE) を参照してください。
