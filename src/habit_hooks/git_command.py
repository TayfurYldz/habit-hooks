
from __future__ import annotations

import subprocess
from pathlib import Path


def git(project_dir: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_dir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",  # sensors.spawn's policy
            input="",
        )
    except OSError:
        return None


def git_output(project_dir: Path, *args: str) -> str:
    result = git(project_dir, *args)
    if result is None or result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_succeeded(project_dir: Path, *args: str) -> bool:
    result = git(project_dir, *args)
    return result is not None and result.returncode == 0
