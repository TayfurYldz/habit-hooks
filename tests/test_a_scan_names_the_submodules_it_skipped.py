
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import committed, repository, submodule
from habit_hooks import project_scan
from habit_hooks.config import Config
from scope_probe import scope as _scope
from scope_probe import scoped_files as _scoped_files

_PY_SOURCE = ["**/*.py"]
pytestmark = pytest.mark.usefixtures("git_ceiling")


def _vendoring_a_submodule(tmp_path: Path) -> Path:
    inner = repository(tmp_path / "lib")
    committed(inner, inner / "inner.py")
    project = repository(tmp_path / "project")
    committed(project, project / "own.py")
    submodule(project, inner, "vendor/lib")
    return project


def test_a_submodules_source_is_not_this_projects_to_scan(tmp_path: Path) -> None:
    project = _vendoring_a_submodule(tmp_path)
    assert (project / "vendor" / "lib" / "inner.py").is_file()
    assert _scoped_files(["--all"], project, Config(files=_PY_SOURCE)) == ["own.py"]


def test_a_submodule_left_out_of_a_partial_scan_is_named(tmp_path: Path) -> None:
    project = _vendoring_a_submodule(tmp_path)
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert scanned.files == ["own.py"]
    assert scanned.notices == [
        "habit-sensors: vendor/lib is a submodule; its files are scanned in "
        "their own repository"
    ]


def test_a_submodule_is_named_even_when_it_emptied_the_scan(tmp_path: Path) -> None:
    inner = repository(tmp_path / "lib")
    committed(inner, inner / "inner.py")
    project = repository(tmp_path / "project")
    committed(project, project / "README.md")
    submodule(project, inner, "vendor/lib")
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert scanned.files == []
    assert "vendor/lib is a submodule" in "\n".join(scanned.notices)


def test_a_submodule_no_files_setting_wanted_is_not_mentioned(tmp_path: Path) -> None:
    project = _vendoring_a_submodule(tmp_path)
    excluded = Config(files=["**/*.py", "!**/vendor/**"])

    assert _scope(["--all"], project, excluded).notices == []
    assert _scope(["--all"], project, Config(files=_PY_SOURCE)).notices != []


def test_a_submodules_own_entry_cannot_reach_a_sensor(tmp_path: Path) -> None:
    project = _vendoring_a_submodule(tmp_path)
    assert "vendor/lib" in project_scan.files_in(project)
    assert (project / "vendor" / "lib").is_dir()
    assert _scoped_files(["--all"], project, Config(files=["vendor/**"])) == []


def test_a_submodule_at_a_non_ascii_path_is_still_named(tmp_path: Path) -> None:
    inner = repository(tmp_path / "lib")
    committed(inner, inner / "inner.py")
    project = repository(tmp_path / "project")
    committed(project, project / "own.py")
    submodule(project, inner, "café/lib")
    scanned = _scope(["--all"], project, Config(files=_PY_SOURCE))

    assert scanned.files == ["own.py"]
    assert scanned.notices == [
        "habit-sensors: café/lib is a submodule; its files are scanned in "
        "their own repository"
    ]


def test_a_git_mode_is_silent_about_a_submodule_it_never_touched(
    tmp_path: Path,
) -> None:
    project = _vendoring_a_submodule(tmp_path)
    committed(project, project / "later.py")
    scanned = _scope(["--last", "1"], project, Config(files=_PY_SOURCE))

    assert scanned.files == ["later.py"]
    assert scanned.notices == []
