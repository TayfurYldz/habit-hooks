
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import committed, repository, written
from habit_hooks.config import Config, ScopeDefaults
from scope_probe import scoped_files as _scoped_files

_PY_SOURCE = ["**/*.py"]
pytestmark = pytest.mark.usefixtures("git_ceiling")


def test_an_ignored_file_is_out_of_a_whole_project_scan(tmp_path: Path) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    committed(project, project / "src" / "a.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["src/a.py"]


def test_a_repository_above_the_project_still_ignores_for_it(tmp_path: Path) -> None:
    above = repository(tmp_path / "repo", ignoring="build/\n")
    project = above / "pkg"
    committed(above, project / "keep.py")
    written(project / "build" / "generated.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["keep.py"]


def test_a_brand_new_untracked_file_is_still_in_scope(tmp_path: Path) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    written(project / "fresh.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["fresh.py"]


def test_a_non_ascii_name_survives_gits_answer(tmp_path: Path) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    committed(project, project / "café.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["café.py"]


def test_the_configured_scope_filters_as_all_does(tmp_path: Path) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    committed(project, project / "src" / "a.py")
    written(project / "dist" / "built.py")
    config = Config(files=_PY_SOURCE, scope=ScopeDefaults(mainBranch="main"))
    assert _scoped_files([], project, config) == ["src/a.py"]


def test_files_still_narrows_what_git_keeps(tmp_path: Path) -> None:
    project = repository(tmp_path / "project")
    committed(project, project / "src" / "a.py")
    committed(project, project / "README.md")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["src/a.py"]


def test_a_file_deleted_from_the_work_tree_is_still_dropped(tmp_path: Path) -> None:
    project = repository(tmp_path / "project")
    committed(project, project / "src" / "a.py").unlink()
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == []


def test_a_project_whose_own_gitignore_starts_with_a_star(tmp_path: Path) -> None:
    project = repository(tmp_path / "project", ignoring="*\n!.gitignore\n!keep.py\n")
    committed(project, project / "keep.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["keep.py"]


def test_a_nested_project_whose_own_gitignore_starts_with_a_star(
    tmp_path: Path,
) -> None:
    above = repository(tmp_path / "repo")
    project = above / "pkg"
    written(project / ".gitignore").write_text("*\n!keep.py\n", encoding="utf-8")
    committed(above, project / "keep.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["keep.py"]
