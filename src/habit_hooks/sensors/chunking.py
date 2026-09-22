"""How one sensor's scope splits across invocations under the argument budget."""

from __future__ import annotations

from collections.abc import Callable

from ..argv_budget import argument_budget, argument_cost, within_argument_limits
from .command_text import COMMA_FILES, spells
from .model import Part


def spells_files(part: Part) -> bool:
    """Whether the recipe splices the file list in any spelling — whole
    arguments (``${files}``) or the one joined argument (``${files:comma}``) —
    because either shape overflows one spawn on a work-tree-sized scope."""
    if spells(part, "${files}"):
        return True
    recipe = part.argv if part.argv is not None else [part.command or ""]
    return any(COMMA_FILES in element for element in recipe)


def chunked_commands(
    sensor: Part, files: list[str], expand: Callable[[list[str]], list[str]]
) -> list[list[str]]:
    """One invocation's argv per chunk of the already-spelled ``files``.

    A recipe that splices the files — either spelling — is split so a
    work-tree-sized scope never overflows one spawn; one that reads its own
    paths runs once. The budget is what is left after the rest of the argv.
    """
    split = spells_files(sensor) and files
    budget = argument_budget() - argument_cost(expand([]))
    chunks = within_argument_limits(files, budget) if split else [files]
    return [expand(chunk) for chunk in chunks]
