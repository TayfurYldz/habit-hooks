
from __future__ import annotations

from pathlib import Path
from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def run_sensor(
    part: Part, files: list[str] | tuple[str, ...] = ("src/a.py",)
):
    return Execution(
        project_dir=part.directory, scope=Scope(files=list(files))
    ).run_sensors([part])


def run_sensor_in(project_dir: Path, part: Part):
    return Execution(
        project_dir=project_dir, scope=Scope(files=["src/a.py"])
    ).run_sensors([part])


def run_sensor_until(part: Part, timeout: float):
    return Execution(
        project_dir=part.directory,
        scope=Scope(files=["src/a.py"]),
        timeout=timeout,
    ).run_sensors([part])


def python_sensor(directory: Path, script: str) -> Part:
    (directory / "probe.py").write_text(script, encoding="utf-8")
    return Part(name="probe", directory=directory, argv=["${python}", "${dir}/probe.py"])
