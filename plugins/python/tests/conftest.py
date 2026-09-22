"""What the deptry sensor's tests need of the run they stand in for.

**The helper loads as a loose script.** The sensor spec spells
``${python} ${dir}/deptry_sensor.py``, so the interpreter puts the helper's own
directory first on ``sys.path``, and a unit test does the same rather than
reaching the code as ``habit_hooks_python.sensors.deptry_sensor`` — a load path
no run ever takes (see "A plugin helper imports its neighbours as top-level
modules" in CLAUDE.md).

**The helper is handed its tool as a file.** The spec names it with
``${detector:deptry}``, which the run resolves against the project's own bins
before the helper is spawned (``project_paths.tool_executable``). A test
spawning the helper directly stands in for the run, so it asks that same
question and hands over a real file rather than a name. Absent is a failure
rather than a skip: ``uv sync`` brings it, so a machine without it is a suite
that has quietly stopped gating.

ruff needs none of this since its migration to the inline form — its drift gate
is the approved scenario in ``scenarios/ruff/``.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

SENSORS = (
    Path(__file__).resolve().parents[1] / "src" / "habit_hooks_python" / "sensors"
)

sys.path.insert(0, str(SENSORS))


@pytest.fixture(scope="session")
def deptry() -> str:
    """The file this machine runs deptry by, as the sensor's first argument."""
    found = shutil.which("deptry")
    if found is None:
        pytest.fail("deptry is not on PATH — run 'uv sync'")
    return found
