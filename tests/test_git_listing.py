
from __future__ import annotations

from pathlib import Path

from git_repo import repository_with_committed_file
from habit_hooks import git_listing


def test_an_untracked_file_is_named(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    (tmp_path / "fresh.py").write_text("VALUES = [1]\n", encoding="utf-8")
    assert git_listing.untracked_paths(tmp_path) == ["fresh.py"]


def test_an_ignored_file_is_not_named_untracked(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    (tmp_path / ".gitignore").write_text("build.py\n", encoding="utf-8")
    (tmp_path / "build.py").write_text("VALUES = [9]\n", encoding="utf-8")
    assert "build.py" not in git_listing.untracked_paths(tmp_path)
