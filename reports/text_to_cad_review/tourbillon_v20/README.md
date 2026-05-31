# Tourbillon V20 text-to-CAD Review Staging

This directory stages the current V20 STEP outputs for optional text-to-CAD sidecar, cadref, and snapshot review.

Source of truth remains the CadQuery generator and `manifests/tourbillon_v20.json`; do not edit staged STEP files.

Useful commands:

- Sidecar summary: `cd '/mnt/c/Users/diobrando/Documents/New project/external/text-to-cad/skills/cad/scripts' && python -m gen_step_part '/home/diobrando/cad/tourbillon/cad_agent_framework/reports/text_to_cad_review/tourbillon_v20/step/01_base_608zz_bearing_pocket_v20.step' --summary`
- Snapshot example: `cd '/mnt/c/Users/diobrando/Documents/New project/external/text-to-cad/skills/cad/scripts' && python -m snapshot '/home/diobrando/cad/tourbillon/cad_agent_framework/reports/text_to_cad_review/tourbillon_v20/step/.01_base_608zz_bearing_pocket_v20.step/model.glb' --views isometric,top --out-dir '/home/diobrando/cad/tourbillon/cad_agent_framework/reports/text_to_cad_review/tourbillon_v20/snapshots'`

The primary mechanical gates remain design checks, geometry selector audit, motion preview, Onshape pose snapshots, and solid interference audit.
