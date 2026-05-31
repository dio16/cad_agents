# V12-V15 PDCA Review

## 結論

V11は機械として不成立だったため、V12からV15まで4回のPDCAを回しました。
V15では、V11で失敗していた駆動接続、内歯車内を転がるピニオンの自転比、軸穴クリアランス、ギア中心距離の数値条件を通過しました。

ただし、Onshape上の合致フィーチャーはまだ0です。
したがって、現時点の検証済み範囲は「STEP投入、Assembly構成、API姿勢変更、機構寸法監査」です。
「Onshape Mateを作成してAnimateした」検証は未完了です。

## PDCA 1: V12

Plan:
V11の不成立点を直接潰す。

Do:
- 手回しクランクを前面の独立軸とし、同軸の小ピニオンを追加。
- 回転ケージに外周駆動ギアを統合。
- 固定内歯リングと公転ピニオンのピッチ関係を再設定。
- ピニオン穴とケージ軸のクリアランスを正値化。

Check:
- orbit pinion to fixed ring pitch: pass
- cage drive gear to hand crank pinion pitch: pass
- hand crank drives the model: pass
- hand crank mechanically coupled to cage: pass
- internal rolling ratio: pass
- pinion bore clearance: pass

Act:
クリアランスをさらに増やし、3Dプリント時の回転不良リスクを下げる。

## PDCA 2: V13

Plan:
FDM造形向けに軸穴余裕を増やす。

Do:
- orbit pinion boreをR2.9 mmへ拡大。
- cage axleはR2.25 mmを維持。

Check:
- pinion bore radial clearance: 0.65 mm
- その他の設計チェック: pass

Act:
噛み合いが詰まって見えないリスクを下げるため、次サイクルでピニオン半径と中心距離を再調整する。

## PDCA 3: V14

Plan:
内歯リングとピニオンの見た目の余裕を増やす。

Do:
- pinion centerを43.0 mmへ変更。
- pinion pitch radiusを13.0 mmへ変更。
- fixed ring pitch radiusは56.0 mmを維持。

Check:
- internal gear pitch error: 0.0 mm
- internal rolling expected ratio: -3.3077
- actual spin ratio: -3.3077
- pinion bore radial clearance: 0.75 mm

Act:
最終版では軸をわずかに細くし、見やすさと回転余裕を優先する。

## PDCA 4: V15

Plan:
最終版として、鑑賞性とFDM余裕を両立させる。

Do:
- cage shaftをR2.2 mmへ変更。
- hand crank motionを原点回転ではなく、前面軸まわりのspinへ修正。
- hand crank ratioを`-43 / 10 = -4.3`へ修正。
- OnshapeへAPI importし、Assemblyを作成。
- `pose --theta 120`で姿勢変更を適用。

Check:
- validate: pass
- check: pass
- audit: pass
- Onshape import: done
- Onshape Assembly: created
- Onshape visual inspection: done

Act:
次の残課題は、API姿勢変更ではなくOnshape Mate/Relationを実作成すること。

## V15主要寸法

- fixed internal ring pitch radius: 56.0 mm
- orbit pinion center distance: 43.0 mm
- orbit pinion pitch radius: 13.0 mm
- orbit pinion spin ratio: -3.3077
- cage drive gear pitch radius: 43.0 mm
- hand crank pinion pitch radius: 10.0 mm
- hand crank ratio against cage: -4.3
- orbit pinion bore radius: 3.0 mm
- cage pinion shaft radius: 2.2 mm
- pinion radial clearance: 0.8 mm

## V15 Onshape Assembly

https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/02ec794d33363341f7b5c182

## 残課題

- Onshape合致フィーチャーは0。
- Revolute Mate、固定、Gear RelationのAPI生成はまだ未完了。
- Balance wheelとescape wheelは鑑賞要素であり、脱進機としての機械拘束は未実装。
- 歯形は厳密なインボリュートではなく、FDM鑑賞用の丸め歯/ピン歯。

## 判定

V15はV11より機械構成として大きく改善しました。
ただし「Onshape上でMateを使って本当にアニメーションしたTourbillon」としては未完成です。
次のPDCAはMate Connector生成とGear Relation作成を最優先にする必要があります。
