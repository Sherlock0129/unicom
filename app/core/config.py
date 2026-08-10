from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(value: str | Path) -> Path:
    """Resolve a path relative to the project root."""
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_yaml(path: str | Path) -> dict[str, Any]:
    with project_path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须包含一个对象: {path}")
    return data


def load_json(path: str | Path) -> dict[str, Any]:
    with project_path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"JSON 文件必须包含一个对象: {path}")
    return data


@dataclass(frozen=True)
class ClassNames:
    person: str
    helmet: str
    no_helmet: str


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]
    classes: ClassNames

    @classmethod
    def from_file(cls, path: str | Path = "configs/app.yaml") -> "AppConfig":
        raw = load_yaml(path)
        classes = raw["classes"]
        return cls(
            raw=raw,
            classes=ClassNames(
                person=str(classes["person"]),
                helmet=str(classes["helmet"]),
                no_helmet=str(classes["no_helmet"]),
            ),
        )

