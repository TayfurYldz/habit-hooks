
from __future__ import annotations

import shlex
import sys
from pathlib import Path

from ..cli import ConfigError
from .model import Part
from .named_tools import spelled_for_a_shell, spelled_plainly

LIST_PLACEHOLDERS = ("${files}", "${args}", "${config}")
COMMA_FILES = "${files:comma}"


def spelled_files(part: Part, files: list[str]) -> list[str]:
    if part.argv is not None:
        return list(files)
    return [shlex.quote(path) for path in files]


def spells(part: Part, placeholder: str) -> bool:
    if part.argv is not None:
        return placeholder in part.argv
    return placeholder in (part.command or "")


def expanded(part: Part, files: list[str], config_path: Path | None) -> list[str]:
    _refuse_unusable_arguments(part)
    if part.argv is not None:
        return _argv_form(part, files, config_path)
    return ["bash", "-c", _shell_form(part, files, config_path)]


def _argv_form(part: Part, files: list[str], config_path: Path | None) -> list[str]:
    lists = {
        "${files}": files,
        "${args}": part.args,
        "${config}": _config_arguments(config_path),
    }
    elements = part.argv or []
    program = [_program(part, elements[0])] if elements else []
    return [
        argument
        for element in [*program, *elements[1:]]
        for argument in _element_arguments(part, element, lists)
    ]


def _program(part: Part, element: str) -> str:
    file = part.detectors.get(element)
    return element if file is None else file


def _element_arguments(
    part: Part, element: str, lists: dict[str, list[str]]
) -> list[str]:
    if element in lists:
        return lists[element]
    _refuse_embedded_list_placeholder(part, element)
    return [
        spelled_plainly(part, element)
        .replace("${python}", sys.executable)
        .replace("${dir}", str(part.directory))
        .replace(COMMA_FILES, ",".join(lists["${files}"]))
    ]


def _shell_form(part: Part, files: list[str], config_path: Path | None) -> str:
    return (
        spelled_for_a_shell(part, part.command or "")
        .replace("${python}", shlex.quote(sys.executable))
        .replace("${dir}", shlex.quote(str(part.directory)))
        .replace("${args}", shlex.join(part.args))
        .replace(COMMA_FILES, shlex.quote(",".join(files)))
        .replace("${files}", " ".join(files))
        .replace("${config}", shlex.join(_config_arguments(config_path)))
    )


def _refuse_embedded_list_placeholder(part: Part, element: str) -> None:
    embedded = next((name for name in LIST_PLACEHOLDERS if name in element), None)
    if embedded is None:
        return
    raise ConfigError(
        f"{part.name!r} cannot expand {embedded} inside {element!r} — it stands "
        f"for a whole list of arguments, so it has to be an argv element of its "
        f"own; split it into two elements, or use a 'command' string, where a "
        "shell does the splitting"
    )


def _refuse_unusable_arguments(part: Part) -> None:
    if not part.args or spells(part, "${args}"):
        return
    raise ConfigError(
        f"sensor {part.name!r} cannot take arguments — its command has no "
        f"'${{args}}' to expand {part.args} into; remove the 'args', clear a "
        f"plugin's own default with [sensors.{part.name}] args = [], or override "
        "the sensor with a command that spells '${args}'"
    )


def _config_arguments(config_path: Path | None) -> list[str]:
    if config_path is None:
        return []
    return ["--config", str(config_path)]
