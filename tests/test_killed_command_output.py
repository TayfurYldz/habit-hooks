
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from habit_hooks.sensors import deadline
from habit_hooks.sensors.deadline import bounded_output
from habit_hooks.sensors.model import Part
from habit_hooks.sensors.part_output import part_timeout

ARGV = ["probe"]
PID = 4321
A_WINDOWS_EXPIRY = subprocess.TimeoutExpired(ARGV, 0.3)
A_POSIX_EXPIRY = subprocess.TimeoutExpired(ARGV, 0.3, stderr=b"cannot reach registry\n")


class _Command:

    args = ARGV
    pid = PID
    returncode = -9

    def __init__(self, *turns: object) -> None:
        self._turns = list(turns)

    def communicate(self, stdin: str = "", timeout: float = 0.0) -> object:
        turn = self._turns.pop(0)
        if isinstance(turn, BaseException):
            raise turn
        return turn


@pytest.fixture
def killed(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    ended: list[int] = []
    monkeypatch.setattr(deadline, "kill_command", ended.append)
    return ended


def test_a_command_that_answered_in_time_is_not_killed_or_asked_again(
    killed: list[int],
) -> None:
    result = bounded_output(_Command(("[]", "")), "", 0.3)

    assert result.stdout == "[]"
    assert killed == []


def test_a_timeout_that_carried_nothing_still_quotes_the_tool_back(
    killed: list[int],
) -> None:
    command = _Command(A_WINDOWS_EXPIRY, ("", "cannot reach registry\n"))

    with pytest.raises(subprocess.TimeoutExpired) as timeout:
        bounded_output(command, "", 0.3)

    assert killed == [PID]
    assert timeout.value.stderr == "cannot reach registry\n"
    assert timeout.value.timeout == 0.3


def test_the_deadline_reported_is_the_one_that_passed(killed: list[int]) -> None:
    command = _Command(A_WINDOWS_EXPIRY, ("", ""))

    with pytest.raises(subprocess.TimeoutExpired) as timeout:
        bounded_output(command, "", 0.3)

    assert timeout.value.timeout == 0.3


def test_a_pipe_that_will_not_close_leaves_the_first_answer_standing(
    killed: list[int], tmp_path: Path
) -> None:
    command = _Command(A_POSIX_EXPIRY, subprocess.TimeoutExpired(ARGV, 5.0))
    part = Part(name="probe", directory=tmp_path, argv=ARGV)

    with pytest.raises(subprocess.TimeoutExpired) as timeout:
        bounded_output(command, "", 0.3)

    assert timeout.value is A_POSIX_EXPIRY
    assert "cannot reach registry" in str(part_timeout("sensor", part, timeout.value))
