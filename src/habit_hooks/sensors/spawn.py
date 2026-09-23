
from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..project_paths import tool_executable, tool_search_path
from . import batch_shell
from .deadline import DEFAULT_SENSOR_TIMEOUT_SECONDS, bounded_output
from .live_commands import LIVE_COMMANDS, its_own_process_group
from .part_output import command_not_found, no_project_to_run_in


@dataclass(frozen=True)
class Spawner:

    project_dir: Path
    timeout: float = DEFAULT_SENSOR_TIMEOUT_SECONDS

    def run(
        self, argv: list[str], stdin: str = "", tools: Sequence[str] = ()
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._spawned(self._runnable(argv, tools), stdin)
        except FileNotFoundError:
            if not self.project_dir.is_dir():
                raise no_project_to_run_in(self.project_dir) from None
            return command_not_found(argv)

    def _runnable(self, argv: list[str], tools: Sequence[str]) -> list[str]:
        found = (
            None
            if os.path.dirname(argv[0])
            else tool_executable(argv[0], self.project_dir)
        )
        runnable = argv if found is None else [found, *argv[1:]]
        batch_shell.refuse_unreadable_arguments([runnable[0], *tools], runnable[1:])
        return runnable

    def _spawned(self, argv: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
        with subprocess.Popen(
            argv,
            cwd=self.project_dir,
            env=self._path_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            **its_own_process_group(),
        ) as process, LIVE_COMMANDS.tracking(process.pid):
            return bounded_output(process, stdin, self.timeout)

    def _path_env(self) -> dict:
        return {
            **os.environ,
            "PATH": tool_search_path(self.project_dir),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONSAFEPATH": "",
        }
