from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from cad_agent.security_policy import ALLOWED_DATA_CLASSIFICATIONS

DEFAULT_DATA_CLASSIFICATION = "internal"
_ALLOWED_UPDATE_FIELDS = {"name", "description", "data_classification"}
_PROJECTS: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy_project(project: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(project)


def validate_data_classification(data_classification: str) -> bool:
    return isinstance(data_classification, str) and data_classification in ALLOWED_DATA_CLASSIFICATIONS


def _require_valid_data_classification(data_classification: str) -> None:
    if not validate_data_classification(data_classification):
        raise ValueError(f"unknown data_classification: {data_classification}")


def create_project(name: str, description: str, data_classification: str = DEFAULT_DATA_CLASSIFICATION) -> dict[str, Any]:
    _require_valid_data_classification(data_classification)
    now = _utc_now()
    project_id = f"proj_{uuid4().hex}"
    project = {
        "project_id": project_id,
        "name": name,
        "description": description,
        "data_classification": data_classification,
        "created_at": now,
        "updated_at": now,
    }
    _PROJECTS[project_id] = project
    return _copy_project(project)


def get_project(project_id: str) -> dict[str, Any] | None:
    project = _PROJECTS.get(project_id)
    return _copy_project(project) if project is not None else None


def list_projects() -> list[dict[str, Any]]:
    return [_copy_project(project) for project in _PROJECTS.values()]


def update_project(project_id: str, **fields: Any) -> dict[str, Any] | None:
    project = _PROJECTS.get(project_id)
    if project is None:
        return None

    updates = {key: value for key, value in fields.items() if key in _ALLOWED_UPDATE_FIELDS}
    if "data_classification" in updates:
        _require_valid_data_classification(str(updates["data_classification"]))
    if updates:
        project.update(updates)
        project["updated_at"] = _utc_now()
    return _copy_project(project)


def delete_project(project_id: str) -> bool:
    return _PROJECTS.pop(project_id, None) is not None


def reset_projects() -> None:
    _PROJECTS.clear()
