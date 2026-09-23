from __future__ import annotations

import shutil
from pathlib import Path

PACKAGE = Path(__file__).parents[1] / "src" / "habit_hooks_typescript"

NOT_SHIPPED = shutil.ignore_patterns("__pycache__")


def vendored(project: Path) -> Path:
    return _copied_to(project / ".habit-hooks" / "typescript")


def in_a_local_venv(project: Path) -> Path:
    return _copied_to(
        project
        / ".venv"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "habit_hooks_typescript"
    )


def outside_the_project(root: Path) -> Path:
    return _copied_to(root / "site-packages" / "habit_hooks_typescript")


def sensor(package: Path, helper: str) -> Path:
    return package / "sensors" / helper


def _copied_to(destination: Path) -> Path:
    shutil.copytree(PACKAGE, destination, ignore=NOT_SHIPPED, dirs_exist_ok=True)
    return destination
