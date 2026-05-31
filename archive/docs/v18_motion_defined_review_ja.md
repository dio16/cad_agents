# V18 Motion-Defined Review

## 目的

V17はレイアウト成立性を改善しましたが、動作定義に曖昧さが残っていました。
特に、公転ピニオンの`spin_ratio`を絶対回転比として監査していた一方で、実際のTransform実装ではケージ公転角にローカル回転を足していました。

V18では、動作定義を`motion_contract`として明示し、その契約を`motion`コマンドで検証する方式に変えました。

## 抽出した問題

- `orbit_and_spin_z`の`spin_ratio`が絶対回転比なのかローカル回転比なのか曖昧だった。
- `pose --theta`のthetaが何の角度か曖昧だった。
- ギア関係が`design_checks`と各partの`motion`に分散しており、動作契約として読めなかった。

## 設計スキームでの解決

- `motion_contract.pose_parameter = cage_angle_deg`を定義。
- 公転ピニオンに`orbit_absolute_spin_z`を追加。
- `absolute_spin_ratio = -44 / 14 = -3.142857`を明示。
- 手回しクランクは、ケージ角を基準に`ratio = -44 / 11 = -4.0`として逆算。
- `motion`コマンドを追加し、ジョイント型とギア関係を検証。

## V18検証結果

- `validate`: pass
- `check`: pass
- `audit`: pass
- `motion`: pass
- Onshape API import: done
- Onshape Assembly: done
- `pose --theta 120`: done
- In-app browser visual inspection: done

## V18 Onshape Assembly

https://cad.onshape.com/documents/0222fa90c0584ca0727f31d2/w/0cb8dde2f58aafcc165e983c/e/0fa3f0f62d8b71c03f9723a3

## 実装したコマンド

```powershell
.\run_cad_agent.ps1 --manifest .\manifests\tourbillon_v18.json motion
```

## まだ残る課題

- Onshape合致フィーチャーはまだ0。
- `motion_contract`はAPI姿勢変更の正しさを保証するが、Onshape Mate Animateではない。
- 次はこの`motion_contract`からMate Connector、Revolute Mate、Gear Relationを生成する必要がある。
- 下段の手回し駆動ギアはまだ見えにくいため、鑑賞性改善としてベース側の観察窓が必要。

## 判定

V18で、動作定義の曖昧さは解消しました。
これにより、以後のCAD修正は「形状を見て勘で直す」のではなく、`motion_contract`に反するかどうかで判定できます。
