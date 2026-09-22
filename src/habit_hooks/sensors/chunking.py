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

    A recipe that splices ``${files}`` — or its one-argument ``${files:comma}``
    joining — is split so a huge list never fails
    the spawn (a raw ``OSError`` ``_safe_sensor`` never caught, escaping an
    ordinary CI-sized run as a traceback); one that reads its own paths
    (``knip``, ``deptry``, ``jscpd``) runs once, not once per chunk.

    Each form spends the budget on what it actually carries. A ``command``
    part's paths are quoted into one ``bash -c`` argument; an ``argv``
    part's are arguments of their own, quoted not at all. Either way the
    rest of the argv is paid for first, so the batch is measured against
    what is left rather than against the whole.
    """
    split = spells_files(sensor) and files
    budget = argument_budget() - argument_cost(expand([]))
    chunks = within_argument_limits(files, budget) if split else [files]
    return [expand(chunk) for chunk in chunks]
