"""The report file a report-writing tool is handed through ``${report}``,
and what it means when nothing was written there."""


from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from .model import InlineRecipe, Part, SensorError


@contextlib.contextmanager
def report_path(recipe: InlineRecipe) -> Iterator[Path | None]:
    """A fresh report file for the invocation when the entry asked for one."""
    if not recipe.report:
        yield None
        return
    handle, name = tempfile.mkstemp(prefix="habit-hooks-report-")
    os.close(handle)
    report = Path(name)
    report.unlink()
    try:
        yield report
    finally:
        report.unlink(missing_ok=True)


def report_text(sensor: Part, report: Path) -> str:
    """What the tool wrote at the path it was handed.

    A tool that answers in a report writes one even when it finds nothing, so
    no report is a failed run, never a clean one.
    """
    try:
        return report.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise SensorError(
            f"sensor {sensor.name!r} wrote no report — a tool that answers in "
            "a report writes one even when it finds nothing, so no report is "
            "a run that never delivered, not a clean one"
        ) from None
