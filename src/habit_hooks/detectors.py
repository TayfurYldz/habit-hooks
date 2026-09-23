
from __future__ import annotations

import ntpath

from attrs import field, fields, frozen

from .cli import ConfigError
from .config_schema import named_keys, reject_unknown

COMMAND_KIND = "command"
NODE_MODULE_KIND = "node-module"
DETECTOR_KINDS = frozenset({COMMAND_KIND, NODE_MODULE_KIND})


@frozen
class Detector:
    name: str
    kind: str
    install: str
    search_paths: tuple[str, ...] = field(converter=tuple, default=())


DETECTOR_FIELDS = frozenset(field.name for field in fields(Detector))
REQUIRED_FIELDS = frozenset({"name", "kind", "install"})


def _reject_unknown_kind(value: object, where: str) -> None:
    if value in DETECTOR_KINDS:
        return
    known = ", ".join(repr(kind) for kind in sorted(DETECTOR_KINDS))
    raise ConfigError(
        f"unknown detector 'kind' {value!r} in {where}; known values: {known}"
    )


def _says_something(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _label(entry: dict) -> str:
    name = entry.get("name")
    return f"detector {name!r}" if _says_something(name) else f"detector {entry!r}"


def _reject_unusable_field(entry: dict, key: str, where: str) -> None:
    if _says_something(entry[key]):
        return
    raise ConfigError(
        f"{_label(entry)} needs a non-empty string {key!r} in {where}; "
        f"got {entry[key]!r}"
    )


def _reject_unusable_search_paths(entry: dict, where: str) -> None:
    paths = entry.get("search_paths", [])
    unusable = not isinstance(paths, list) or not all(
        _names_a_directory(path) for path in paths
    )
    if unusable:
        raise ConfigError(
            f"{_label(entry)} needs 'search_paths' as a list of non-empty "
            f"directories under the project in {where}; got {paths!r}"
        )


def _names_a_directory(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not _splices_extra_directories(value)
        and not _escapes_the_project(value)
    )


def _splices_extra_directories(path: str) -> bool:
    return ":" in path or ";" in path


def _escapes_the_project(path: str) -> bool:
    if ntpath.splitdrive(path)[0]:
        return True
    components = path.replace("\\", "/").split("/")
    return components[0] == "" or ".." in components


def _reject_invalid_detector(entry: object, where: str) -> None:
    if not isinstance(entry, dict):
        raise ConfigError(
            f"detector {entry!r} is not a table in {where}; "
            "expected { name = ..., kind = ..., install = ... }"
        )
    missing = sorted(key for key in REQUIRED_FIELDS if key not in entry)
    if missing:
        raise ConfigError(
            f"{_label(entry)} is missing {named_keys(missing)} in {where}"
        )
    reject_unknown(DETECTOR_FIELDS, entry, f"a detector in {where}")
    _reject_unknown_kind(entry["kind"], where)
    _reject_unusable_field(entry, "name", where)
    _reject_unusable_field(entry, "install", where)
    _reject_unusable_search_paths(entry, where)


def reject_invalid_detectors(value: object, where: str) -> None:
    if not isinstance(value, list):
        raise ConfigError(
            f"'detectors' must be a list of tables in {where}; got {value!r}"
        )
    for entry in value:
        _reject_invalid_detector(entry, where)
