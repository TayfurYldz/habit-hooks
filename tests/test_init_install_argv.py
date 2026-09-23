
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest
from habit_hooks import init_command
from habit_hooks.init_command import run
from init_install_fixture import FIRST, PYTHON, answering, needing, ran
from toml_text import toml_string


def test_a_quoted_argument_reaches_the_command_as_one_piece(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    quoted = shlex.quote("habit-hooks[python]")
    needing(
        init_project,
        f'{{ name = "wobble-quoted", kind = "command", '
        f'install = {toml_string(f"{PYTHON} mark.py {quoted}")} }}',
    )
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    assert run([]) == 0
    assert ran(init_project) == ["habit-hooks[python]"]


def _recorded_commands(monkeypatch: pytest.MonkeyPatch) -> list[tuple[tuple, dict]]:
    real_run = subprocess.run
    calls: list[tuple[tuple, dict]] = []

    def _recording(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        calls.append((args, kwargs))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(init_command.subprocess, "run", _recording)
    return calls


def test_the_command_is_spawned_as_an_argv_never_read_by_a_shell(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _recorded_commands(monkeypatch)
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    run([])

    (spawned, options) = next(call for call in calls if "mark.py" in call[0][0])
    assert isinstance(spawned[0], list)
    assert options.get("shell") is not True
