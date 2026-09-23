
from __future__ import annotations

from collections.abc import Callable

from ..argv_budget import argument_budget, argument_cost, within_argument_limits
from .command_text import COMMA_FILES, spells
from .model import Part


def spells_files(part: Part) -> bool:
    if spells(part, "${files}"):
        return True
    recipe = part.argv if part.argv is not None else [part.command or ""]
    return any(COMMA_FILES in element for element in recipe)


def chunked_commands(
    sensor: Part, files: list[str], expand: Callable[[list[str]], list[str]]
) -> list[list[str]]:
    split = spells_files(sensor) and files
    budget = argument_budget() - argument_cost(expand([]))
    chunks = within_argument_limits(files, budget) if split else [files]
    return [expand(chunk) for chunk in chunks]
