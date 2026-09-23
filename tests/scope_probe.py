
from __future__ import annotations

from pathlib import Path

from habit_hooks.config import Config
from habit_hooks.scope import Scope, resolve_scope
from habit_hooks.sensors import parse_args


def source_file(project_dir: Path) -> Path:
    (project_dir / "src").mkdir(exist_ok=True)
    source = project_dir / "src" / "a.py"
    source.write_text("x = 1\n", encoding="utf-8")
    return source


def scope(argv: list[str], project_dir: Path, config: Config | None = None) -> Scope:
    return resolve_scope(parse_args(argv), config or Config(), project_dir)


def scoped_files(
    argv: list[str], project_dir: Path, config: Config | None = None
) -> list[str]:
    return scope(argv, project_dir, config).files
