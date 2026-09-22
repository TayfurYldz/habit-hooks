"""How one sensor's scope splits across invocations under the argument budget."""

from __future__ import annotations

from collections.abc import Callable

from ..argv_budget import argument_budget, argument_cost, within_argument_limits
from .command_text import spells
from .model import Part


def chunked_commands(
    sensor: Part, files: list[str], expand: Callable[[list[str]], list[str]]
) -> list[list[str]]:
    """One invocation's argv per chunk of the already-spelled ``files``.

    A recipe that splices ``${files}`` is split so a huge list never fails
    the spawn (a raw ``OSError`` ``_safe_sensor`` never caught, escaping an
    ordinary CI-sized run as a traceback); one that reads its own paths
    (``knip``, ``deptry``, ``jscpd``) runs once, not once per chunk.

    Each form spends the budget on what it actually carries. A ``command``
    part's paths are quoted into one ``bash -c`` argument; an ``argv``
    part's are arguments of their own, quoted not at all. Either way the
    rest of the argv is paid for first, so the batch is measured against
    what is left rather than against the whole.
    """
    split = spells(sensor, "${files}") and files
    budget = argument_budget() - argument_cost(expand([]))
    chunks = within_argument_limits(files, budget) if split else [files]
    return [expand(chunk) for chunk in chunks]
