
from __future__ import annotations

import subprocess
from collections.abc import Callable

from . import batch_shell, posix_shell
from .model import Part, SensorError
from .part_output import command_not_found, part_spawn_failure, part_timeout


def run_part(
    kind: str, part: Part, run: Callable[[], subprocess.CompletedProcess[str]]
) -> subprocess.CompletedProcess[str]:
    posix_shell.refuse_where_there_is_none(kind, part)
    if part.missing_detector is not None:
        return command_not_found([part.missing_detector])
    try:
        return run()
    except batch_shell.UnreadableArgument as refusal:
        raise SensorError(f"{kind} {part.name!r} {refusal}") from None
    except subprocess.TimeoutExpired as expiry:
        raise part_timeout(kind, part, expiry) from None
    except OSError as refusal:
        raise part_spawn_failure(kind, part, refusal) from None
