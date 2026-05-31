# V25 Mechanical Design Workflow

V24 is rejected. The next design is not allowed to start from colors or a viewer. It must follow this workflow.

## 1. Requirements

- Target: watch-grade-inspired desktop tourbillon demonstrator.
- It must be mechanically coherent as a tabletop object, not a timekeeping watch movement.
- Native Onshape Gear Relation is not required for local completion, but the local motion contract must be continuous and ratio-correct.
- The escapement must be supported on the rotating carrier. Decorative jewels or red markers must not float.
- Any limitation, such as simplified load or tooth contact model, must be written into validation.

## 2. Mechanism Topology

- Fixed element: internal fixed fourth-wheel analogue, represented as an internal gear/ring, not an external gear drawn inside another external gear.
- Moving element: rotating carrier around the central axis.
- Planet element: escape-pinion/orbit-pinion shaft mounted on the carrier and driven by the fixed internal gear.
- Input: hand crank pinion drives a carrier drive gear.
- Escapement: escape wheel, pallet fork, balance wheel, banking pins, and jewel supports are mounted to the carrier frame.

## 3. Component Design

- Gears use a single normal module inside each mesh pair.
- External gears use involute 20 degree pressure angle unless a later contract selects another profile.
- Internal fixed ring must be modeled and validated as an internal ring gear.
- Shaft and bridge features must exist for every moving part.
- Visual jewel parts must sit on physical supports or be omitted.

## 4. Dimensioning

Minimum contract fields:

- tooth counts
- module
- pressure angle
- pitch diameter/radius
- base diameter/radius
- root diameter/radius
- outside diameter/radius
- center distance
- backlash
- material and load assumptions
- shaft diameter and support span

## 5. Verification

CAD generation is blocked until these gates exist:

- gear pitch/module/ratio check
- involute tooth parameter check
- undercut check
- backlash check
- Lewis bending stress estimate
- internal ring/orbit relation check
- hand/carrier external gear relation check
- carrier-mounted escapement support check
- no-floating-part check
- visibility/contact-sheet check

## 6. CAD Completion Rule

Completion is allowed only when generated CAD/viewer outputs trace back to the V25 contract and all validation reports pass. A pretty viewer is not completion.
