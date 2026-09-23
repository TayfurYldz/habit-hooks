
from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO = Path(__file__).resolve().parents[1]


def _pyproject(path: Path) -> dict:
    return tomllib.loads((path / "pyproject.toml").read_text(encoding="utf-8"))


def _core() -> dict:
    return _pyproject(REPO)["project"]


def _plugin_requirements(project: dict) -> list[str]:
    declared = list(project["dependencies"])
    for extra in project["optional-dependencies"].values():
        declared.extend(extra)
    return [
        requirement
        for requirement in declared
        if requirement.startswith("habit-hooks-")
    ]


def _floor_for(version: str) -> SpecifierSet:
    major, minor, *_ = version.split(".")
    return SpecifierSet(f">={major}.{minor}.dev0,<{int(major) + 1}")


def test_every_plugin_is_floored_at_this_release_s_minor() -> None:
    core = _core()

    floors = {
        Requirement(requirement).specifier
        for requirement in _plugin_requirements(core)
    }

    assert floors == {_floor_for(core["version"])}


def test_this_release_satisfies_the_floors_it_declares() -> None:
    released = Version(_core()["version"])

    refused = [
        requirement
        for requirement in _plugin_requirements(_core())
        if released not in Requirement(requirement).specifier
    ]

    assert refused == [], f"{released} does not satisfy {refused}"


def test_every_plugin_ships_at_the_core_s_version() -> None:
    expected = _core()["version"]

    versions = {
        path.parent.name: _pyproject(path.parent)["project"]["version"]
        for path in sorted(REPO.glob("plugins/*/pyproject.toml"))
    }

    assert versions == dict.fromkeys(versions, expected)
