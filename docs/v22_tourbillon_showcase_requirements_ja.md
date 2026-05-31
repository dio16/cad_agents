# V22 Tourbillon Showcase Requirements

## Reference-Derived Mechanism Requirements

Sources:

- THREEC Magazine, `トゥールビヨンの仕組み`, https://threec.jp/magazine/729
- User-provided YouTube reference, https://www.youtube.com/watch?v=FnQsow6iT5c

The V22 object must read as a tourbillon before it reads as a generic gear sculpture.

1. The fixed fourth-wheel analogue remains fixed: V21 uses the fixed internal ring for this role.
2. The rotating carriage remains the main moving stage.
3. A visible balance wheel, escape wheel, and pallet fork are carried by the rotating carriage.
4. Local pose exports at 0, 90, 180, and 270 degrees must show the escapement display parts moving with the carriage.
5. The model may use a visual escapement contract rather than a real timekeeping escapement, but it must not claim watch-grade regulation.

## Aesthetic Requirements

1. The default view must make the rotating carriage and balance wheel the first visual signal.
2. Fixed structures should be darker or translucent-looking so they do not overpower the moving mechanism.
3. Moving gears should use warm metal colors and be visibly separated from the fixed base/ring.
4. Jewel pivots should add small red highlights at important axes.
5. The viewer must include a hero pose and four motion poses so the user can inspect the motion path.
6. The showcase layer must include explicit role names for `balance_wheel`, `escape_wheel`, `pallet_fork`, `escapement_bridge`, and `jewel_pivots`.

## Completion Wording

V22 can be called `showcase complete` when:

- V21 mechanical gates remain pass.
- V22 local GLB poses and viewer are generated.
- V22 validation confirms the added escapement roles are present and carried by the rotating carriage transform.
- The native Onshape Gear Relation limitation remains explicit.

V22 must not be called `native Onshape complete` unless Onshape Gear Relation readback later returns `featureStatus: OK`.
