"""The report path a report-writing tool is handed, and reading it back.

``report = true`` on an inline entry buys a tool that answers in a report
rather than stdout: the framework reserves a fresh path, hands it to the tool
wherever the recipe spells ``${report}``, and reads back the one report the
tool left there. Where exactly the tool puts that report is the tool's own
family trait — some write a file at the path, some make it a directory and put
a named report inside it — so both spellings are read, and nothing at all is
the sensor's failed run rather than a clean one.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

from .model import InlineRecipe, Part, SensorError


@contextlib.contextmanager
def report_path(recipe: InlineRecipe) -> Iterator[Path | None]:
    """A fresh report path for the invocation when the entry asked for one.

    Handed over *empty* rather than pre-created: a path that already existed
    as a file would be in a directory-writer's way, and one that existed as a
    directory in a file-writer's.
    """
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
        shutil.rmtree(report, ignore_errors=True)


def report_text(sensor: Part, report: Path) -> str:
    """The one report the tool left at the path it was handed.

    A file is read as it stands; a directory is read as the single report file
    inside it. Nothing at all is a run that never delivered — a tool that
    answers in a report writes one even when it finds nothing, so a missing
    report is a failed run, never a clean one (the #139 class).
    """
    if report.is_file():
        return report.read_text(encoding="utf-8", errors="replace")
    if report.is_dir():
        written = sorted(entry for entry in report.iterdir() if entry.is_file())
        if len(written) == 1:
            return written[0].read_text(encoding="utf-8", errors="replace")
        raise SensorError(
            f"sensor {sensor.name!r} left {len(written)} files in its report "
            "directory rather than the one report — which of them holds the "
            "findings is not the run's to guess"
        )
    raise SensorError(
        f"sensor {sensor.name!r} wrote no report — a tool that answers in a "
        "report writes one even when it finds nothing, so no report is a run "
        "that never delivered, not a clean one"
    )
