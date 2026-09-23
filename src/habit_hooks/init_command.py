
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .config import project_config_path
from .init_report import report
from .initialise import plan


def _parse(argv: list[str]) -> None:
    argparse.ArgumentParser(
        prog="habit-hooks init",
        description="Set this project up: write .habit-hooks/config.toml and "
        "report what habit-hooks still needs installed.",
    ).parse_args(argv)


def _write_config(project_dir: Path, plugins: tuple[str, ...]) -> None:
    named = ", ".join(f'"{plugin}"' for plugin in plugins)
    path = project_config_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"plugins = [{named}]\n", encoding="utf-8")


def _say(line: str) -> None:
    sys.stdout.write(line + "\n")


def _question(count: int) -> str:
    subject = "this command" if count == 1 else f"these {count} commands"
    return f"\nRun {subject} now? [y/N] "


def _agreed(count: int) -> bool:
    sys.stdout.write(_question(count))
    sys.stdout.flush()
    return sys.stdin.readline().strip().lower() in ("y", "yes")


def _succeeded(command: str) -> bool:
    _say(f"\n$ {command}")
    sys.stdout.flush()
    try:
        argv = shlex.split(command)
        argv[0] = shutil.which(argv[0]) or argv[0]
        return subprocess.run(argv).returncode == 0
    except (ValueError, IndexError, OSError):
        return False


def _run_all(commands: tuple[str, ...]) -> None:
    failed = []
    for command in commands:
        if not _succeeded(command):
            failed.append(command)
    if not failed:
        return
    _say("\nThese did not succeed, and are still to do:")
    for command in failed:
        _say(f"  {command}")


def _offer(commands: tuple[str, ...]) -> None:
    if not commands or not sys.stdin.isatty():
        return
    if _agreed(len(commands)):
        _run_all(commands)


def run(argv: list[str]) -> int:
    _parse(argv)
    project_dir = Path.cwd()
    planned = plan(project_dir)
    if not planned.already_configured:
        _write_config(project_dir, planned.plugins)
    for line in report(planned):
        _say(line)
    _offer(planned.installs)
    return 0
