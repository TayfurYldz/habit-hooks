
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from habit_hooks import host_platform
from habit_hooks.sensors import live_commands

A_SHELL_TO_RUN_IT_WITH = pytest.mark.skipif(
    os.name == "nt",
    reason="showing a shell recipe run takes a machine with a shell on it",
)

A_MACHINE_THAT_SPELLS_A_COMMAND_ITSELF = pytest.mark.skipif(
    os.name != "nt",
    reason="only Windows adds an extension of its own to a bare command name",
)

A_MACHINE_THAT_DOES_NOT = pytest.mark.skipif(
    os.name == "nt",
    reason="everywhere else a command is the filename it is, and a shebang runs",
)


def _symlinks_are_permitted_here() -> bool:
    with tempfile.TemporaryDirectory() as scratch:
        try:
            Path(scratch, "probe").symlink_to(scratch)
        except (OSError, NotImplementedError):
            return False
        return True


A_MACHINE_WITH_SIGNALS = pytest.mark.skipif(
    os.name == "nt",
    reason="a killed process only carries a signal where the platform has them",
)

A_MACHINE_WITHOUT_SIGNALS = pytest.mark.skipif(
    os.name != "nt",
    reason="only Windows ends a process with TerminateProcess, leaving an exit code",
)

A_MACHINE_THAT_CAN_MAKE_A_SYMLINK = pytest.mark.skipif(
    not _symlinks_are_permitted_here(),
    reason=(
        "creating a symlink needs SeCreateSymbolicLinkPrivilege on Windows, so "
        "a symlinked node_modules — pnpm's ordinary layout — is unmeasured on a "
        "machine without it; platform gaps skip out loud rather than pass over"
    ),
)


A_FILESYSTEM_THAT_ALLOWS_A_STAR_IN_A_FILENAME = pytest.mark.skipif(
    os.name == "nt",
    reason=(
        "Windows forbids `*` in a filename outright, so a scope file carrying "
        "one literally is a POSIX filesystem's own case to tell — skipped out "
        "loud rather than passed over"
    ),
)


def on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(host_platform, "is_windows", lambda: True)


def off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(host_platform, "is_windows", lambda: False)


def recorded_spawns(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], dict]]:
    spawns: list[tuple[list[str], dict]] = []

    def record(argv: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        spawns.append((argv, options))
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(live_commands.subprocess, "run", record)
    return spawns


def recorded_signals(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    signals: list[tuple[int, int]] = []
    monkeypatch.setattr(
        live_commands.os,
        "killpg",
        lambda pgid, number: signals.append((pgid, number)),
        raising=False,
    )
    return signals
