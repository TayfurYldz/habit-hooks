
from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

from platform_probe import A_SHELL_TO_RUN_IT_WITH

WEDGED_RUN = """
import os, sys
from pathlib import Path

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part

marker = os.environ["HABIT_HOOKS_PROBE_MARKER"]
sleeper = f"{sys.executable} -c 'import time; time.sleep(60)' {marker}"
part = Part(name="probe", command=f"{sleeper} | {sleeper}", directory=Path("."))
Execution(
    project_dir=Path("."), scope=Scope(files=["src/a.py"]), timeout=60.0
).run_sensors([part])
"""


def _pids(marker: str) -> list[str]:
    found = subprocess.run(
        ["pgrep", "-f", marker],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return found.stdout.split()


def _within(seconds: float, condition: Callable[[], bool]) -> bool:
    deadline = time.monotonic() + seconds
    while not condition():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)
    return True


@contextlib.contextmanager
def _wedged_run(marker: str, tmp_path: Path) -> Iterator[subprocess.Popen[bytes]]:
    tool = subprocess.Popen(
        [sys.executable, "-c", WEDGED_RUN],
        cwd=tmp_path,
        env={**os.environ, "HABIT_HOOKS_PROBE_MARKER": marker},
        start_new_session=True,
    )
    try:
        assert _within(30, lambda: bool(_pids(marker))), "the sensor never started"
        yield tool
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(tool.pid, signal.SIGKILL)
        subprocess.run(["pkill", "-f", marker])
        tool.wait()


@A_SHELL_TO_RUN_IT_WITH
def test_an_interrupted_run_does_not_wait_out_its_sensor_deadlines(
    tmp_path: Path,
) -> None:
    marker = f"habit_hooks_probe_{uuid.uuid4().hex}"

    with _wedged_run(marker, tmp_path) as tool:
        os.killpg(tool.pid, signal.SIGINT)

        assert _within(20, lambda: tool.poll() is not None), "still running"
        assert _within(5, lambda: not _pids(marker)), "left its pipeline behind"
