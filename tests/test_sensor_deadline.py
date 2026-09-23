
from __future__ import annotations

import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from platform_probe import A_SHELL_TO_RUN_IT_WITH, off_windows

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def _timed_out_notice(tmp_path: Path, script: str) -> str:
    (tmp_path / "wedge.py").write_text(script, encoding="utf-8")
    part = Part(name="probe", directory=tmp_path, argv=["${python}", "${dir}/wedge.py"])
    execution = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/a.py"]), timeout=0.3
    )

    run = execution.run_sensors([part])

    assert run.failed
    return "\n".join(run.notices)


def test_a_wedged_sensor_times_out_into_a_failed_run(tmp_path: Path) -> None:
    (tmp_path / "wedge.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    part = Part(name="probe", directory=tmp_path, argv=["${python}", "${dir}/wedge.py"])
    execution = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/a.py"]), timeout=0.2
    )

    run = execution.run_sensors([part])

    assert run.findings == []
    assert run.failed
    assert any("timed out" in notice for notice in run.notices)


def test_a_wedged_sensor_quotes_back_the_little_it_managed_to_say(
    tmp_path: Path,
) -> None:
    notice = _timed_out_notice(
        tmp_path,
        "import sys, time\n"
        "print('cannot reach registry', file=sys.stderr)\n"
        "sys.stderr.flush()\n"
        "time.sleep(5)\n",
    )

    assert "cannot reach registry" in notice
    assert "b'" not in notice


def test_a_wedged_sensor_that_said_a_lot_is_still_a_notice(tmp_path: Path) -> None:
    notice = _timed_out_notice(
        tmp_path,
        "import sys, time\n"
        "for i in range(1, 26):\n"
        "    print(f'warning {i}', file=sys.stderr)\n"
        "sys.stderr.flush()\n"
        "time.sleep(5)\n",
    )
    lines = notice.splitlines()

    assert "warning 1" in lines
    assert "warning 10" in lines
    assert "warning 11" not in lines
    assert "warning 15" not in lines
    assert "warning 16" in lines
    assert "warning 25" in lines
    assert "... 5 lines omitted ..." in notice


def test_a_wedged_sensor_printing_undecodable_bytes_is_still_a_notice(
    tmp_path: Path,
) -> None:
    notice = _timed_out_notice(
        tmp_path,
        "import sys, time\n"
        "sys.stderr.buffer.write(b'sad \\xff\\xfe end')\n"
        "sys.stderr.buffer.flush()\n"
        "time.sleep(5)\n",
    )

    assert "timed out" in notice
    assert "sad" in notice
    assert "end" in notice
    assert "b'" not in notice


def _surviving_pids(marker: str) -> list[str]:
    deadline = time.monotonic() + 5
    while True:
        found = subprocess.run(
            ["pgrep", "-f", marker],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        pids = found.stdout.split()
        if not pids or time.monotonic() > deadline:
            return pids
        time.sleep(0.05)


@A_SHELL_TO_RUN_IT_WITH
def test_a_timed_out_sensor_takes_its_whole_pipeline_with_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    marker = f"habit_hooks_probe_{uuid.uuid4().hex}"
    sleeper = f"{shlex.quote(sys.executable)} -c 'import time; time.sleep(30)' {marker}"
    part = Part(name="probe", command=f"{sleeper} | {sleeper}", directory=tmp_path)
    execution = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/a.py"]), timeout=1.0
    )

    run = execution.run_sensors([part])

    assert run.failed
    assert _surviving_pids(marker) == []
