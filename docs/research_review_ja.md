# CAD Agent Workflow Research Review

## Sources Checked

- Onshape Assemblies API: https://onshape-public.github.io/docs/api-adv/assemblies/
- Onshape Feature API: https://onshape-public.github.io/docs/api-adv/featureaccess/
- Onshape Assemblies API mate connector section: https://onshape-public.github.io/docs/api-adv/assemblies/
- Onshape Part Studios API: https://onshape-public.github.io/docs/api-adv/partstudios/
- Onshape FeatureScript docs: https://cad.onshape.com/FsDoc/index.html
- CadQuery import/export docs: https://cadquery.readthedocs.io/en/latest/importexport.html
- CadQuery assemblies docs: https://cadquery.readthedocs.io/en/latest/assy.html

## Findings

The overall architecture is correct: use REST APIs for repeatable CAD actions and use the browser only for visual review.

Confirmed requirements:

- Onshape assembly transforms are absolute object-to-world 4x4 matrices in the top-level assembly coordinate system.
- Transforms should be recorded in meters, so local millimeter design coordinates need explicit conversion.
- FeatureScript is the correct future path for native parametric Onshape features and should be treated as a first-class generation backend alongside CadQuery.
- CadQuery assembly STEP export can preserve assembly structure and color, but individual STEP imports are often easier to map to Onshape part elements and motion roles.

## Framework Gaps Found

- Manifest validation was missing.
- Pose verification history was not written back to the manifest.
- FeatureScript/Part Studio API path was not documented as a future backend.
- Transform units and absolute transform semantics were only implicit in code.

## Changes Applied

- Added `validate` CLI command.
- Added pose verification history to manifests.
- Added Assembly Feature API client methods for future Mate Connector/Mate automation.
- Added this research review document.
- Updated README files with the review-surface/API-source-of-truth distinction.
