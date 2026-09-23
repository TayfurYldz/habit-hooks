
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import committed, git, repository, stop_the_upward_walk_at, written
from habit_hooks import git_listing, project_scan
from habit_hooks.config import Config
from scope_probe import scoped_files as _scoped_files

_PY_SOURCE = ["**/*.py"]


@pytest.fixture(autouse=True)
def _only_the_repository_the_case_built(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stop_the_upward_walk_at(tmp_path, monkeypatch)


def test_a_project_in_somebody_elses_ignored_tree_scans_everything(
    tmp_path: Path,
) -> None:
    above = repository(tmp_path / "repo", ignoring="runs/\n")
    project = above / "runs" / "case"
    written(project / "a.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["a.py"]


def test_one_force_tracked_file_never_becomes_an_ignored_projects_whole_scope(
    tmp_path: Path,
) -> None:
    above = repository(tmp_path / "repo", ignoring="runs/\n")
    project = above / "runs" / "case"
    committed(above, project / "tracked.py")
    written(project / "unseen.py")

    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == [
        "tracked.py",
        "unseen.py",
    ]


def test_the_tree_walk_spells_a_nested_path_the_way_git_does(tmp_path: Path) -> None:
    project = tmp_path / "project"
    written(project / "src" / "a.py")
    assert project_scan.files_in(project) == ["src/a.py"]


def test_a_project_outside_a_repository_scans_everything(tmp_path: Path) -> None:
    project = tmp_path / "project"
    written(project / "a.py")
    written(project / "dist" / "built.py")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == [
        "a.py",
        "dist/built.py",
    ]


def test_a_machine_with_no_git_scans_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    written(project / "a.py")
    written(project / "dist" / "built.py")
    monkeypatch.setenv("PATH", str(written(tmp_path / "bin" / "keep.py").parent))
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == [
        "a.py",
        "dist/built.py",
    ]


def test_a_project_with_no_files_setting_asks_git_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    def _never_asked(*_args: object) -> object:
        raise AssertionError("git was asked about a project with no [files]")

    monkeypatch.setattr(git_listing, "ignores_directory", _never_asked)
    monkeypatch.setattr(git_listing, "project_files", _never_asked)
    monkeypatch.setattr(git_listing, "submodule_paths", _never_asked)
    project = repository(tmp_path / "project")
    written(project / "a.py")
    assert _scoped_files(["--all"], project, Config()) == []


def test_a_repository_git_cannot_be_asked_about_still_places_its_files(
    tmp_path: Path,
) -> None:
    project = repository(tmp_path / "project", ignoring="dist/\n")
    written(project / "a.py")
    written(project / "dist" / "built.py")
    git(project, "add", "a.py")
    (project / ".git" / "index").write_bytes(b"not an index")
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == [
        "a.py",
        "dist/built.py",
    ]
