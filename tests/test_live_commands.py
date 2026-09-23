
from __future__ import annotations

import subprocess
from collections.abc import Callable

import pytest
from platform_probe import off_windows, on_windows, recorded_signals, recorded_spawns

from habit_hooks.sensors import live_commands
from habit_hooks.sensors.live_commands import (
    CREATE_NEW_PROCESS_GROUP,
    its_own_process_group,
    kill_command,
)


def _raising(error: Exception) -> Callable[..., None]:

    def refuse(*_args: object, **_options: object) -> None:
        raise error

    return refuse


def test_off_windows_a_command_dies_by_one_signal_to_its_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    off_windows(monkeypatch)
    spawns, signals = recorded_spawns(monkeypatch), recorded_signals(monkeypatch)

    kill_command(4321)

    assert signals == [(4321, 9)]
    assert spawns == []


def test_off_windows_a_group_already_gone_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    off_windows(monkeypatch)
    monkeypatch.setattr(
        live_commands.os,
        "killpg",
        _raising(ProcessLookupError("no such process")),
        raising=False,
    )

    assert kill_command(4321) is None


def test_on_windows_a_command_dies_by_a_taskkill_of_its_whole_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)
    spawns, signals = recorded_spawns(monkeypatch), recorded_signals(monkeypatch)

    kill_command(4321)

    assert [argv for argv, _ in spawns] == [["taskkill", "/T", "/F", "/PID", "4321"]]
    assert signals == []


def test_on_windows_the_kill_never_speaks_where_the_findings_travel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)
    spawns = recorded_spawns(monkeypatch)

    kill_command(4321)

    assert [options["capture_output"] for _, options in spawns] == [True]


def test_on_windows_a_command_already_gone_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)

    def not_found(argv: list[str], **options: object) -> subprocess.CompletedProcess:
        if options.get("check"):
            raise subprocess.CalledProcessError(128, argv)
        return subprocess.CompletedProcess(argv, 128, "", "process not found")

    monkeypatch.setattr(live_commands.subprocess, "run", not_found)

    assert kill_command(4321) is None


def test_on_windows_a_machine_without_taskkill_is_not_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)
    monkeypatch.setattr(
        live_commands.subprocess, "run", _raising(FileNotFoundError("taskkill"))
    )

    assert kill_command(4321) is None


def test_off_windows_a_spawn_asks_for_a_session_of_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    off_windows(monkeypatch)

    assert its_own_process_group() == {"start_new_session": True}


def test_on_windows_a_spawn_asks_for_a_process_group_of_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)

    assert its_own_process_group() == {"creationflags": CREATE_NEW_PROCESS_GROUP}
