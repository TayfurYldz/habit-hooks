
from __future__ import annotations

from .. import host_platform
from .model import Part, SensorError
from .part_output import switch_off


def refuse_where_there_is_none(kind: str, part: Part) -> None:
    if part.command is None or not host_platform.is_windows():
        return
    raise SensorError(
        f"{kind} {part.name!r} cannot run on Windows: its recipe is a shell "
        f"command line, and there is no POSIX shell here to read it — "
        f"{switch_off(kind, part.name)}"
    )
