# Skill 最小仕様監査チェックリスト

この checklist は、`docs/skill_governance_ja.md` の最小仕様を実スキルへ落とすための監査面である。短い skill を長文化するためではなく、短いまま再実行可能にするために使う。

## 必須項目

- [ ] trigger: いつ呼ぶ skill か
- [ ] intended use: 何を解くか
- [ ] required inputs: 何が揃えば始められるか
- [ ] step sequence: 実行順が分かるか
- [ ] expected outputs: 何を残すか
- [ ] validation gates: 何で閉じるか
- [ ] common failure modes: 何を踏み抜きやすいか
- [ ] escalation / stop conditions: どこで止まり、どこへ返すか
- [ ] cheap-before-expensive checks: 重い検証前に安価に潰すものがあるか

## 判定

- 1 つでも欠ける場合は、skill を「短い」ではなく「未仕様」と扱う。
- ただし、汎用説明の重複で埋めない。正本が別にある場合は、要約 1 行と canonical doc への参照でよい。
- claim 境界、gate、stop 条件は省略しない。

## 優先監査対象

1. `mechanical-bearing-shaft-design`
2. `mechanical-motion-verification`
3. `mechanical-cad-validation`
4. `cad-standard-parts-bom`
5. `mechanical-gear-design`

## 出力

- `pass / gap / no-change-needed`
- 欠けている項目
- どの正本へリンクすれば重複なく閉じるか
- 追加が必要な stop / gate / failure-mode 文言
