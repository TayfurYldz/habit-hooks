from __future__ import annotations

import tomllib
from pathlib import Path

import pathspec


PACKAGE = Path(__file__).resolve().parents[1] / "src" / "habit_hooks_java"
OTHER_LANGUAGES = (
    "scripts/build/deploy.py",
    "packages/app/build/config.ts",
)


def _declared_globs() -> list[str]:
    config = tomllib.loads((PACKAGE / "config.toml").read_text(encoding="utf-8"))
    return config["files"]


def test_another_language_s_build_directory_is_left_to_its_own_plugin() -> None:
    spec = pathspec.PathSpec.from_lines(
        "gitignore", ["**/*.py", "**/*.ts", *_declared_globs()]
    )

    assert [path for path in OTHER_LANGUAGES if spec.match_file(path)] == list(
        OTHER_LANGUAGES
    )
