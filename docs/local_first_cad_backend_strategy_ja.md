# Local-First CAD Backend Strategy

## 結論

Onshape API の年間使用量を節約するため、このリポジトリの主系 CAD ワークフローはローカル完結にする。Onshape は共有・閲覧・最終レビュー・ユーザー指定時だけ使う補助系とし、通常の設計生成、干渉確認、動作ポーズ、可視化、STL/STEP/GLB 出力、fabrication package 生成はローカルで完結させる。

推奨主系:

1. **CadQuery/OCP**: 既存 generator、STEP/STL、干渉体積、bbox、fabrication package の主系。
2. **build123d/OCP**: 新規形状・より読みやすい CAD-as-code・text-to-CAD harness の推奨プロトタイプ系。
3. **text-to-CAD harness**: build123d ベースのローカル viewer、snapshot、STEP/STL/GLB/DXF/URDF 補助系。
4. **CadQuery Assembly / explicit transform contract**: Onshape Gear Relation の代替として、ローカルの mate/pose/kinematic contract を検証する。
5. **FreeCAD / SolveSpace / py-slvs**: 必要時のみ、拘束ソルバ比較または図面化・外部検証の補助系。

## 調査メモ

- build123d は Open Cascade ベースの Python BREP CAD で、3D printing/CNC/laser cutting 向けに STEP/STL/glTF などを扱える。CadQuery から派生し、より Pythonic な API を持つ。
- CadQuery は既存リポジトリで稼働済みで、Assembly export、STEP/STL、OCP ベースの干渉検証と相性がよい。CadQuery Assembly には constraint/solve 機構があり、ローカル assembly gate として使える。
- PartCAD は CadQuery/build123d/STEP/STL/3MF などを扱う package/digital thread 寄りのツールで、将来の部品管理や interface/port 管理の候補。
- SolveSpace/py-slvs は拘束ソルバの候補だが、現状の tourbillon では Onshape relation 代替の主系にする前に追加検証が必要。
- FreeCAD Assembly 系はローカルで使えるが、安定性・自動化・速度のリスクがあるため、主系ではなく補助/比較に留める。

## API Budget Policy

Onshape API は次の条件を満たす場合だけ使う。

1. ローカル gate では答えられない確認である。
2. ユーザーが Onshape 上の共有・レビュー・操作を明示した。
3. ローカルで pass した成果物を最終閲覧用に同期する必要がある。
4. Native Gear Relation の既知 schema/正常 readback が手元にあり、少数回の検証で完了見込みがある。

禁止:

- 通常の STEP 再インポートを反復改善ループのたびに行う。
- disposable probe を無制限に作る。
- Onshape API をローカルで検証可能な bbox、干渉、STL 出力、ポーズ生成、visibility snapshot の代替に使う。
- `featureStatus: ERROR` が続く native relation schema を、証跡なしに追加 variant で大量試行する。

## Local Gate Order

通常の設計改善は以下の順に行う。

1. Manifest contract review.
2. CadQuery/build123d geometry generation.
3. STEP/STL/GLB export.
4. Local bbox / volume / single-solid / topology reference checks.
5. Local gear pitch, tooth clearance, shaft/bearing clearance, hardware context checks.
6. Local kinematic transform contract and sampled pose checks.
7. Local rendered contact sheet / viewer snapshot.
8. Fabrication package validation.
9. User-consumable deliverable validation.
10. Optional Onshape sync only when API budget policyを満たす。

## Repository Rule

今後の完成判定は、Onshape native relation を必須にしない。Native relation は `native Onshape complete` の条件であり、物理的・製造的な object completion はローカル gate と fabrication package の pass で判定する。

Status wording:

- `local fabrication complete`: local generation, validation, motion transform, visibility, fabrication package, and user-consumable deliverable pass.
- `Onshape reviewed`: Onshape import/basic mates/pose snapshots pass.
- `native Onshape complete`: Gear Relation probe/readback returns `featureStatus: OK`.

## Next Implementation Candidates

1. Add a `local-backend-status` CLI command that reports CadQuery/OCP/build123d/text-to-CAD availability and the selected backend.
2. Add a local assembly export gate using CadQuery Assembly STEP/GLB instead of Onshape assembly when possible.
3. Add a build123d prototype mirror for the gear module only, to compare tooth geometry and viewer output without disturbing production CadQuery scripts.
4. Add a strict API budget counter log for every Onshape API call made by the repo tooling.

## References

- build123d GitHub: https://github.com/gumyr/build123d
- build123d import/export docs: https://build123d.readthedocs.io/en/latest/import_export.html
- CadQuery project: https://cadquery.github.io/
- CadQuery importing/exporting docs: https://cadquery.readthedocs.io/en/latest/importexport.html
- CadQuery assemblies docs: https://cadquery.readthedocs.io/en/latest/assy.html
- PartCAD GitHub: https://github.com/partcad/partcad
- PartCAD design docs: https://partcad.readthedocs.io/en/latest/design.html
- SolveSpace GitHub: https://github.com/solvespace/solvespace
- py-slvs PyPI: https://pypi.org/project/py-slvs/1.0.1/
- FreeCAD Assembly3 documentation snapshot: https://reqrefusion.github.io/FreeCAD-Documentation-html/wiki/Assembly3_Workbench.html
