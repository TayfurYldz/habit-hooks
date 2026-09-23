
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .cli import ensure_utf8_streams, run_console, version_line
from .init_command import run as run_init
from .sensors import build_parser

INIT = "init"

INIT_HELP = (
    "Set a project up with `habit-hooks init`: it writes .habit-hooks/config.toml "
    "and reports what is still missing."
)


def sibling(name: str) -> str:
    beside = Path(sys.argv[0]).resolve().parent / name
    return str(beside) if beside.is_file() else name


def mapper_args(args: list[str]) -> list[str]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config")
    known, _ = parser.parse_known_args(args)
    return ["--config", known.config] if known.config else []


def print_usage() -> None:
    parser = build_parser("habit-hooks")
    parser.epilog = INIT_HELP
    parser.print_help()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    ensure_utf8_streams()
    if args[:1] == [INIT]:
        return run_console("habit-hooks", run_init, args[1:])
    if "--version" in args:
        sys.stdout.write(version_line() + "\n")
        return 0
    if any(flag in args for flag in ("--help", "-h")):
        print_usage()
        return 0
    sensors = subprocess.Popen([sibling("habit-sensors"), *args], stdout=subprocess.PIPE)
    mapper = subprocess.Popen(
        [sibling("habit-mapper"), *mapper_args(args)], stdin=sensors.stdout
    )
    sensors.stdout.close()
    mapper.wait()
    sensors.wait()
    return mapper.returncode or sensors.returncode


if __name__ == "__main__":
    sys.exit(main())
