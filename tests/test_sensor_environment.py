
from __future__ import annotations

import contextlib
import os
import stat
from collections.abc import Iterator
from pathlib import Path

import pytest
from platform_probe import A_SHELL_TO_RUN_IT_WITH, off_windows

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


@contextlib.contextmanager
def _parent_stdin(data: bytes) -> Iterator[None]:
    read_fd, write_fd = os.pipe()
    os.write(write_fd, data)
    os.close(write_fd)
    saved = os.dup(0)
    os.dup2(read_fd, 0)
    try:
        yield
    finally:
        os.dup2(saved, 0)
        for fd in (saved, read_fd):
            os.close(fd)


def test_a_sensor_reading_stdin_gets_immediate_eof(tmp_path: Path) -> None:
    (tmp_path / "readall.py").write_text(
        "import sys, json\n"
        "data = sys.stdin.read()\n"
        'print(json.dumps([{"smell": "s", "read": len(data), "issues": []}]))\n',
        encoding="utf-8",
    )
    part = Part(
        name="probe", directory=tmp_path, argv=["${python}", "${dir}/readall.py"]
    )
    execution = Execution(project_dir=tmp_path, scope=Scope(files=["src/a.py"]))

    with _parent_stdin(b"refs/heads/main 0000 refs/heads/main 1111\n"):
        findings = execution.run_sensor(part)

    assert findings == [{"smell": "s", "read": 0, "issues": []}]


def test_a_helper_reaches_its_neighbour_under_a_hardened_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "neighbour.py").write_text('SMELL = "s"\n', encoding="utf-8")
    (tmp_path / "helper.py").write_text(
        "import json\n"
        "from neighbour import SMELL\n"
        'print(json.dumps([{"smell": SMELL, "issues": []}]))\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONSAFEPATH", "1")
    part = Part(
        name="probe", directory=tmp_path, argv=["${python}", "${dir}/helper.py"]
    )
    execution = Execution(project_dir=tmp_path, scope=Scope(files=["src/a.py"]))

    assert execution.run_sensor(part) == [{"smell": "s", "issues": []}]


@A_SHELL_TO_RUN_IT_WITH
def test_a_sensor_reaches_the_project_s_own_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    tool = bin_dir / "habit-probe"
    tool.write_text('#!/bin/sh\nprintf \'[{"smell": "s", "issues": []}]\'\n', encoding="utf-8")
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    part = Part(name="probe", command="habit-probe", directory=tmp_path)
    execution = Execution(project_dir=tmp_path, scope=Scope(files=["src/a.py"]))

    assert execution.run_sensor(part) == [{"smell": "s", "issues": []}]
