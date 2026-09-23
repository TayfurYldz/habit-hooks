
from __future__ import annotations

from .model import SensorError

BATCH_SUFFIXES = (".bat", ".cmd")

CMD_SYNTAX = frozenset('&|<>^"%\n\r')


class UnreadableArgument(SensorError):
    pass


def refuse_unreadable_arguments(programs: list[str], arguments: list[str]) -> None:
    for program in programs:
        unreadable = cmd_syntax(program, arguments)
        if unreadable is not None:
            raise UnreadableArgument(
                f"cannot pass {unreadable!r} to {program!r}: a batch file is run "
                "by cmd.exe, which would read that as its own syntax rather than "
                "as text — rename the file, or keep it out of the scope with "
                "[files]"
            )


def cmd_syntax(program: str, arguments: list[str]) -> str | None:
    if not program.lower().endswith(BATCH_SUFFIXES):
        return None
    return next(
        (argument for argument in arguments if CMD_SYNTAX & set(argument)), None
    )
