# CAD Agents: AI Machine Design Platform

This repository now tracks the reference architecture for an AI-assisted mechanical design platform. The original proposal is [`docs/Origen/Design_document_for_a_machine_design_platform.md`](docs/Origen/Design_document_for_a_machine_design_platform.md); every maintained document and script is aligned to that proposal.

## Core principle

Do **not** ask an LLM to emit executable CAD code from free text. The platform uses a gated pipeline:

1. natural-language design intent
2. `Requirement JSON`
3. `Specification JSON`
4. validated `Parametric DSL`
5. deterministic CAD runtime using OCCT / FreeCAD-compatible workers
6. validation reports for geometry, DFM/AM, assembly, and optional FEA
7. versioned artifacts such as STEP AP242, STL, OBJ, glTF, PNG, and PDF

The LLM is a design planner, the CAD kernel is the executor, and validation is the quality gate.

## Canonical files

| File | Purpose |
|---|---|
| [`GOAL.md`](GOAL.md) | Repository mission, non-goals, and acceptance criteria |
| [`SPEC.md`](SPEC.md) | System architecture and data contracts |
| [`TASKS.md`](TASKS.md) | Implementation roadmap derived from the proposal |
| [`AGENTS.md`](AGENTS.md) | Agent responsibility and safety operating rules |
| [`docs/architecture_ja.md`](docs/architecture_ja.md) | Japanese architecture summary |
| [`docs/api_contracts_ja.md`](docs/api_contracts_ja.md) | API, schema, and traceability contracts |
| [`docs/validation_security_ja.md`](docs/validation_security_ja.md) | Validation, audit, and security gates |
| [`docs/operations_ja.md`](docs/operations_ja.md) | CI/CD, runtime, and operational model |

Legacy tourbillon-specific documents and scripts were removed because they were unrelated to the machine-design-platform proposal.

## Run the repository checks

```bash
bash ./run_cad_agent.sh validate-docs
bash ./run_cad_agent.sh status
```

The runner intentionally exposes only platform documentation/contract checks. It no longer exposes old single-artifact tourbillon generation commands.

## Repository layout

```text
docs/Origen/   Original proposal supplied by the user
docs/          Maintained platform documentation
scripts/       Deterministic validation scripts for the platform docs
run_cad_agent.sh  Bash entrypoint for local checks
```

## License

Apache-2.0. See [`LICENSE`](LICENSE).
