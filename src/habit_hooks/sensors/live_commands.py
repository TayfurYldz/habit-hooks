
from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
from collections.abc import Iterator

from .. import host_platform

CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

UNREFUSABLE_KILL = getattr(signal, "SIGKILL", 9)


def its_own_process_group() -> dict:
    if host_platform.is_windows():
        return {"creationflags": CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def kill_command(pid: int) -> None:
    if host_platform.is_windows():
        _taskkill_tree(pid)
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pid, UNREFUSABLE_KILL)


def _taskkill_tree(pid: int) -> None:
    with contextlib.suppress(OSError):
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            capture_output=True,
            check=False,
        )


class _LiveCommands:

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pids: set[int] = set()
        self._interrupted = False

    @contextlib.contextmanager
    def tracking(self, pid: int) -> Iterator[None]:
        with self._lock:
            self._pids.add(pid)
            interrupted = self._interrupted
        if interrupted:
            kill_command(pid)
        try:
            yield
        finally:
            with self._lock:
                self._pids.discard(pid)

    def interrupt(self) -> None:
        with self._lock:
            self._interrupted = True
            pids = list(self._pids)
        for pid in pids:
            kill_command(pid)


LIVE_COMMANDS = _LiveCommands()
