# text-to-CAD 補助レビュー手順

このリポジトリの主系統は CadQuery 生成、manifest 検証、Onshape インポート、Onshape pose snapshot です。`earthtojake/text-to-cad` は主系統を置き換えず、STEP の sidecar 生成、`cadref` 参照、snapshot PNG による視覚レビューを追加する補助系統として使います。

## 実行

WSL の CAD 仮想環境を使います。

```bash
cd /home/diobrando/cad/tourbillon/cad_agent_framework
source /home/diobrando/cad/tourbillon/.venv-cadquery/bin/activate
python scripts/stage_text_to_cad_review.py --run-text-to-cad --summary
```

出力先は `reports/text_to_cad_review/tourbillon_v20/` です。`review_manifest.json` に staged STEP、text-to-CAD script の場所、再実行コマンド、sidecar 生成ログが残ります。

## 使い分け

- 機械成立性: `cad_agent_cli.py check`, `geometry-audit`, `solid-audit`, `motion-preview`, `pose-snapshots` を優先する。
- 形状の見え方: text-to-CAD の `gen_step_part` で STEP sidecar を作り、必要な部品だけ `snapshot` で確認する。
- Onshape 連携: Onshape API のインポートと assembly 作成を正とし、text-to-CAD はローカルで早く観察するための補助に限定する。

## 注意

staged STEP は生成物です。形状変更は `scripts/generate_tourbillon_v20_mechanically_closed.py` と manifest 契約側へ戻して行います。
