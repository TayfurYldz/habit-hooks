
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import committed, repository, stop_the_upward_walk_at, tracked_symlink, written
from habit_hooks.config import Config
from platform_probe import A_MACHINE_THAT_CAN_MAKE_A_SYMLINK
from scope_probe import scope as _scope

_PY_SOURCE = ["**/*.py"]


@pytest.fixture(autouse=True)
def _only_the_repository_the_case_built(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stop_the_upward_walk_at(tmp_path, monkeypatch)


def test_an_ordinary_directory_is_never_called_a_submodule(tmp_path: Path) -> None:
    project = repository(tmp_path / "project")
    committed(project, project / "src" / "a.py")
    (project / "empty").mkdir()
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert scanned.files == ["src/a.py"]
    assert scanned.notices == []


@A_MACHINE_THAT_CAN_MAKE_A_SYMLINK
def test_a_tracked_symlink_to_a_directory_is_not_a_submodule(tmp_path: Path) -> None:
    outside = tmp_path / "elsewhere"
    written(outside / "dep.py")
    project = repository(tmp_path / "project")
    committed(project, project / "src" / "a.py")
    written(project / "inside" / "b.py")
    tracked_symlink(project, "node_modules", outside)
    tracked_symlink(project, "linked_in", project / "inside")
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert (project / "node_modules").is_dir()  # the situation under test
    assert (project / "linked_in").is_dir()
    assert scanned.notices == []


def test_a_plain_tracked_file_is_not_a_submodule(tmp_path: Path) -> None:
    project = repository(tmp_path / "project")
    committed(project, project / "src" / "a.py")
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert scanned.files == ["src/a.py"]
    assert scanned.notices == []


