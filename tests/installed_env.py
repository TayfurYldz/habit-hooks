
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def require_tool(name: str) -> str:
    tool = shutil.which(name)
    if tool is None:
        pytest.skip(f"{name} is not on PATH")
    return tool


def run_and_collect_findings(
    habit_sensors: Path, project: Path, env: dict[str, str] | None = None
) -> list[dict]:
    result = subprocess.run(
        [str(habit_sensors), "--all"],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",  # sensors.spawn's policy
        env=env,
    )
    assert "is not installed" not in result.stderr, result.stderr
    assert "could not locate" not in result.stderr.lower(), result.stderr
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


_RUNNABLE_EXTENSIONS = {
    extension.lower() for extension in os.environ.get("PATHEXT", "").split(os.pathsep)
}


def _the_machine_runs(tool: Path) -> bool:
    if os.name == "nt":
        return tool.suffix.lower() in _RUNNABLE_EXTENSIONS
    return os.access(tool, os.X_OK)


def _the_command_it_answers(tool: Path) -> str:
    return tool.stem.lower() if os.name == "nt" else tool.name


def _link_executables_except(bin_dir: Path, blocked: set[str]) -> None:
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        source = Path(entry)
        if not source.is_dir():
            continue
        for tool in source.iterdir():
            link = bin_dir / tool.name
            if _the_command_it_answers(tool) in blocked or link.exists():
                continue
            if _the_machine_runs(tool):
                link.symlink_to(tool)


def without_python_on_path(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "no-python-bin"
    bin_dir.mkdir()
    _link_executables_except(bin_dir, {"python", "python3"})

    assert shutil.which("python", path=str(bin_dir)) is None
    assert shutil.which("python3", path=str(bin_dir)) is None
    assert shutil.which("git", path=str(bin_dir)) is not None
    return {**os.environ, "PATH": str(bin_dir)}
