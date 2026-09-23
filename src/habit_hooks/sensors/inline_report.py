from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from .model import InlineRecipe, Part, SensorError


@contextlib.contextmanager
def report_path(recipe: InlineRecipe) -> Iterator[Path | None]:
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
    try:
        return report.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise SensorError(
            f"sensor {sensor.name!r} wrote no report — a tool that answers in "
            "a report writes one even when it finds nothing, so no report is "
            "a run that never delivered, not a clean one"
        ) from None
