
from __future__ import annotations

import os
from pathlib import Path

import pytest
from platform_probe import off_windows, on_windows

from habit_hooks.project_paths import (
    project_relative,
    tool_search_path,
    venv_bin_dir,
    venv_executable,
)


def test_an_absolute_path_inside_the_project_is_re_expressed(tmp_path: Path) -> None:
    assert project_relative(str(tmp_path / "src" / "a.py"), tmp_path) == "src/a.py"


def test_a_relative_path_keeps_its_meaning_and_loses_its_detours(
    tmp_path: Path,
) -> None:
    assert project_relative("./src/../src/a.py", tmp_path) == "src/a.py"


def test_the_project_itself_is_not_a_path_under_it(tmp_path: Path) -> None:
    assert project_relative("", tmp_path) is None
    assert project_relative(".", tmp_path) is None
    assert project_relative(str(tmp_path), tmp_path) is None


def test_a_path_escaping_the_project_cannot_be_anchored(tmp_path: Path) -> None:
    assert project_relative("../elsewhere/a.py", tmp_path) is None
    assert project_relative("/etc/hosts", tmp_path) is None


def test_a_project_reached_through_a_symlink_still_anchors(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    through_link = tmp_path / "link"
    through_link.symlink_to(real)

    assert project_relative(str(real / "src" / "a.py"), through_link) == "src/a.py"


def test_a_symlinked_source_directory_keeps_the_project_s_own_name_for_it(
    tmp_path: Path,
) -> None:
    shared = tmp_path / "shared-lib"
    shared.mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "shared").symlink_to(shared)

    assert project_relative("src/shared/a.py", tmp_path) == "src/shared/a.py"


def test_the_project_s_own_tool_bins_come_first_on_its_search_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")
    off_windows(monkeypatch)

    assert tool_search_path(tmp_path).split(os.pathsep) == [
        str(tmp_path / "node_modules" / ".bin"),
        str(tmp_path / ".venv" / "bin"),
        "/usr/bin",
    ]


def test_the_project_s_bin_is_searched_only_where_a_detector_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")

    assert str(tmp_path / "bin") not in tool_search_path(tmp_path).split(os.pathsep)


def test_a_venv_keeps_its_executables_under_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)

    assert venv_bin_dir(tmp_path / ".venv") == tmp_path / ".venv" / "bin"


def test_a_windows_venv_keeps_its_executables_under_scripts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    on_windows(monkeypatch)

    assert venv_bin_dir(tmp_path / ".venv") == tmp_path / ".venv" / "Scripts"


def test_the_search_path_reaches_a_windows_venv_s_scripts_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")
    on_windows(monkeypatch)

    entries = tool_search_path(tmp_path).split(os.pathsep)

    assert str(tmp_path / ".venv" / "Scripts") in entries
    assert str(tmp_path / ".venv" / "bin") not in entries


def test_a_venv_s_interpreter_keeps_its_bare_name_off_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)

    assert venv_executable(tmp_path / ".venv", "python") == tmp_path / ".venv" / "bin" / "python"


def test_a_windows_venv_s_interpreter_gains_an_exe_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    on_windows(monkeypatch)

    assert (
        venv_executable(tmp_path / ".venv", "python")
        == tmp_path / ".venv" / "Scripts" / "python.exe"
    )


def test_a_windows_venv_s_console_script_gains_the_same_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    on_windows(monkeypatch)

    assert (
        venv_executable(tmp_path / ".venv", "habit-sensors")
        == tmp_path / ".venv" / "Scripts" / "habit-sensors.exe"
    )
