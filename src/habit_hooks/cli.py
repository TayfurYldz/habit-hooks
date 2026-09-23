from __future__ import annotations

import argparse
import contextlib
import sys
from collections.abc import Callable
from importlib.metadata import version

EXIT_TOOL_ERROR = 2


class ToolError(SystemExit):
    pass


class ConfigError(ToolError):
    pass


def ensure_utf8_streams() -> None:
    with contextlib.suppress(AttributeError):
        sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def version_line() -> str:
    return f"habit-hooks v{version('habit-hooks')}"


def add_version_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version", action="version", version=version_line())


def _named(error: ToolError, program: str) -> str:
    return f"{program}: {error}" if isinstance(error, ConfigError) else str(error)


def run_console(
    program: str,
    body: Callable[[list[str]], int],
    argv: list[str] | None,
) -> int:
    ensure_utf8_streams()
    try:
        return body(argv if argv is not None else sys.argv[1:])
    except ToolError as error:
        sys.stderr.write(f"{_named(error, program)}\n")
        return EXIT_TOOL_ERROR
