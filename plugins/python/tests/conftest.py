
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
    found = shutil.which("deptry")
    if found is None:
        pytest.fail("deptry is not on PATH — run 'uv sync'")
    return found
