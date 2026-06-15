from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "phase1"


@dataclass(frozen=True)
class ContractResult:
    name: str
    status: str
    detail: str = ""


@lru_cache(maxsize=None)
def _load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / f"{schema_name}.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _schema_validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(_load_schema(schema_name))


def validate_against_schema(document: dict[str, Any], schema_name: str) -> list[ContractResult]:
    validator = _schema_validator(schema_name)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if not errors:
        return [ContractResult(f"{schema_name} JSON Schema", "pass")]

    details = "; ".join(f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}" for error in errors)
    return [ContractResult(f"{schema_name} JSON Schema", "fail", details)]
