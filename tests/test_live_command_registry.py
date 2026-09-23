
from __future__ import annotations

import pytest
from platform_probe import on_windows, recorded_spawns

from habit_hooks.sensors import live_commands


def _kills(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    kills: list[int] = []
    monkeypatch.setattr(live_commands, "kill_command", kills.append)
    return kills


def test_nothing_live_is_nothing_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    kills = _kills(monkeypatch)

    live_commands._LiveCommands().interrupt()

    assert kills == []


def test_an_interrupt_ends_every_live_command(monkeypatch: pytest.MonkeyPatch) -> None:
    kills = _kills(monkeypatch)
    live = live_commands._LiveCommands()

    with live.tracking(11), live.tracking(22):
        live.interrupt()

    assert set(kills) == {11, 22}


def test_a_finished_command_is_no_longer_live(monkeypatch: pytest.MonkeyPatch) -> None:
    kills = _kills(monkeypatch)
    live = live_commands._LiveCommands()

    with live.tracking(11):
        pass
    live.interrupt()

    assert kills == []


def test_a_command_started_after_the_interrupt_is_ended_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kills = _kills(monkeypatch)
    live = live_commands._LiveCommands()
    live.interrupt()

    with live.tracking(33):
        assert kills == [33]


def test_on_windows_an_interrupt_reaches_the_kill_that_platform_has(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_windows(monkeypatch)
    spawns = recorded_spawns(monkeypatch)
    live = live_commands._LiveCommands()

    with live.tracking(11), live.tracking(22):
        live.interrupt()

    assert {argv[-1] for argv, _ in spawns} == {"11", "22"}
