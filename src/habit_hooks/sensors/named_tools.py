
from __future__ import annotations

import os
import re
import shlex
from collections.abc import Callable
from pathlib import Path

from attrs import frozen

from ..cli import ConfigError
from ..detectors import COMMAND_KIND, NODE_MODULE_KIND, Detector, search_paths_for
from ..project_paths import tool_executable
from .model import Part
from .part_output import switch_off



DETECTOR = re.compile(r"\$\{detector:([^{}]*)\}")


@frozen
class DeclaredTools:

    declared: list[Detector]
    project_dir: Path

    def file_for(self, name: str) -> str | None:
        return tool_executable(name, self.project_dir, _search_paths(name, self.declared))

    def kinds_of(self, name: str) -> list[str]:
        return sorted(
            {detector.kind for detector in self.declared if detector.name == name}
        )

    def spelled_out(self) -> str:
        named = ", ".join(
            f"{detector.name} ({detector.kind})" for detector in self.declared
        )
        return named or "none"


def _search_paths(name: str, declared: list[Detector]) -> tuple[str, ...]:
    return search_paths_for(name, declared)


def files_for(part: Part, kind: str, tools: DeclaredTools) -> dict[str, str | None]:
    named = _names_in(part)
    for name in named:
        unusable = _why_no_file_for(name, tools)
        if unusable is not None:
            raise ConfigError(
                f"{kind} {part.name!r} names ${{detector:{name}}}, {unusable} — "
                f"{switch_off(kind, part.name)}"
            )
    files = {name: tools.file_for(name) for name in named}
    program = _bare_program(part)
    if program and program not in files and COMMAND_KIND in tools.kinds_of(program):
        files[program] = tools.file_for(program)
    return files


def spelled_plainly(part: Part, text: str) -> str:
    return _filled_in(part, text, str)


def spelled_for_a_shell(part: Part, text: str) -> str:
    return _filled_in(part, text, shlex.quote)


def _filled_in(part: Part, text: str, spell: Callable[[str], str]) -> str:
    for name, file in part.detectors.items():
        if file is not None:
            text = text.replace(f"${{detector:{name}}}", spell(file))
    return text


def _names_in(part: Part) -> list[str]:
    recipe = (part.command or "") if part.argv is None else " ".join(part.argv)
    return list(dict.fromkeys(DETECTOR.findall(recipe)))


def _bare_program(part: Part) -> str | None:
    if part.argv is None or os.path.dirname(part.argv[0]):
        return None
    return part.argv[0]


def _why_no_file_for(name: str, tools: DeclaredTools) -> str | None:
    kinds = tools.kinds_of(name)
    if COMMAND_KIND in kinds:
        return None
    if not kinds:
        return _nobody_declared(tools)
    return _the_wrong_kind(name, kinds)


def _nobody_declared(tools: DeclaredTools) -> str:
    return (
        "which no active plugin declares: a plugin names the tools its sensors "
        "reach for in its config.toml 'detectors', and this run declares "
        f"{tools.spelled_out()}"
    )


def _the_wrong_kind(name: str, kinds: list[str]) -> str:
    spelled = ", ".join(repr(kind) for kind in kinds)
    return (
        f"but {name!r} is declared {spelled}, not {COMMAND_KIND!r}: only a "
        f"command names a file this run can spawn{_and_what_a_module_is(kinds)}"
    )


def _and_what_a_module_is(kinds: list[str]) -> str:
    if NODE_MODULE_KIND not in kinds:
        return ""
    return ", and a module is read by node from the project, never spawned by name"
