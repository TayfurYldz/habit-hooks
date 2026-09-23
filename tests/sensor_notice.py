

from __future__ import annotations

from pathlib import Path

from habit_hooks.sensors.model import Part
from sensor_run import python_sensor, run_sensor_in


def sensor_notice(tmp_path: Path, command: str) -> str:
    return only_notice(Part(name="probe", command=command, directory=tmp_path))


def script_notice(tmp_path: Path, script: str) -> str:
    return only_notice(python_sensor(tmp_path, script))


def only_notice(part: Part, project_dir: Path | None = None) -> str:
    run = run_sensor_in(project_dir or part.directory, part)

    assert run.findings == []
    assert run.failed
    assert len(run.notices) == 1
    return run.notices[0]
