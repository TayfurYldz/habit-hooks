
from __future__ import annotations

from pathlib import Path

from text_io_encoding import REPO_ROOT, _violations_in_file

MINIMUM_TARGET_FILES = 50


def _target_files() -> list[Path]:
    roots = [
        REPO_ROOT / "src",
        REPO_ROOT / "tests",
        *(REPO_ROOT / "plugins").glob("*/src"),
        *(REPO_ROOT / "plugins").glob("*/tests"),
    ]
    files = [path for root in roots for path in root.rglob("*.py")]
    files = [path for path in files if "scenarios" not in path.parts]
    files.append(REPO_ROOT / "conftest.py")
    return files


def test_target_files_resolve_to_a_nontrivial_set() -> None:
    assert len(_target_files()) > MINIMUM_TARGET_FILES


def test_every_text_io_call_in_the_repo_names_its_encoding() -> None:
    violations = [line for path in _target_files() for line in _violations_in_file(path)]
    assert violations == [], (
        "these calls read or write text with no encoding=:\n"
        + "\n".join(violations)
    )
