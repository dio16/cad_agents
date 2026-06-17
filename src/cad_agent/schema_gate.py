from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_DIR = files("cad_agent.contracts.phase1")
ALLOWED_SCHEMA_NAMES = frozenset({"requirement", "specification", "parametric_dsl", "validation_report"})


@dataclass(frozen=True)
class ContractResult:
    name: str
    status: str
    detail: str = ""


@lru_cache(maxsize=None)
def _load_schema(schema_name: str) -> dict[str, Any]:
    if schema_name not in ALLOWED_SCHEMA_NAMES:
        raise ValueError(f"unknown Phase 1 schema name: {schema_name}")
    return json.loads(SCHEMA_DIR.joinpath(f"{schema_name}.schema.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _schema_validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(_load_schema(schema_name))


def validate_against_schema(document: dict[str, Any], schema_name: str) -> list[ContractResult]:
    if schema_name not in ALLOWED_SCHEMA_NAMES:
        return [ContractResult(f"{schema_name} JSON Schema", "fail", f"unknown Phase 1 schema name: {schema_name}")]

    validator = _schema_validator(schema_name)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if not errors:
        return [ContractResult(f"{schema_name} JSON Schema", "pass")]

    details = "; ".join(f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}" for error in errors)
    return [ContractResult(f"{schema_name} JSON Schema", "fail", details)]
