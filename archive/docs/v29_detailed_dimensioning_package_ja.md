# V29 Detailed Dimensioning Package

## 目的

V29 の採用案を、full CAD 前に寸法 budget と risky-subsystem 順へ落とし込む。

## 1. サブシステム寸法 budget

| サブシステム | 初期 budget | 意図 |
| --- | --- | --- |
| 可視 winding drum | 直径 70-90 mm | 遠景の主役。全体 silhouette の 35-45% |
| 低電圧 motor chamber | 25 x 40 x 20 mm 以内の基部領域 | motor を主役にせず、給力の存在だけを構造化 |
| spring barrel / storage | 直径 28-40 mm | motor と表示機構を切り離し、時計らしい蓄力感を出す |
| horizontal transfer shaft | base plane に沿う 1 本 | drum / barrel から riser へ因果を読ませる |
| bevel riser | 1 段、axis transition 1 回 | 立体駆動の核心。視覚 gimmick にしない |
| canted carrier | 直径 70-90 mm、初期傾斜 30° | 大胆さと支持成立の折衷 |
| fast-fine zone | carrier 前面の開放領域 | pallet / escape / balance を覆わない |

## 2. 速度階層 budget

| motion class | 見せる役割 | 初期方針 |
| --- | --- | --- |
| slow macro | winding drum | 目で追える遅さ |
| medium transfer | barrel / transfer / riser | 因果が読める中速 |
| fast fine | escape / pallet / balance | 近づくと見える速い精緻さ |

## 3. 先に切り出す risky subsystem

full geometry の前に、次の最小モジュールだけを先に試す。

1. **autonomous power module**
   - motor
   - visible winding drum
   - storage barrel
   - output shaft
2. **spatial riser module**
   - horizontal shaft
   - bevel / crown equivalent
   - elevated output shaft
3. **open canted cage sightline module**
   - cage tilt
   - hero-view occlusion
   - fast-fine zone visibility

## 4. 主要 failure mode と前倒し対策

| Failure | 前倒し対策 |
| --- | --- |
| motor が作品性を壊す | motor は隠し、見せるのは drum / barrel / riser |
| winding drum が支配的すぎる | 面積比 budget と hero-view review |
| storage が不要な direct-drive に退化する | goal で蓄力を価値と明示 |
| riser が高すぎて支持が弱くなる | shaft span / bearing concept を先に閉じる |
| cage 傾斜で細部が隠れる | 30° 初期値、occlusion budget 付き |

## 5. Full CAD へ進む前の gate

1. power-module topology pass
2. storage-output contract pass
3. spatial-riser ratio / support pass
4. hero-view openness pass
5. canted-cage support concept pass
6. assembly-order concept pass

## 6. 次工程

1. autonomous power module の最小 CAD
2. spatial riser module の最小 CAD
3. risky subsystem review
4. system interface control package
5. full assembly contract
6. kinematic dimension contract
7. その後にのみ architecture demonstrator / full geometry
