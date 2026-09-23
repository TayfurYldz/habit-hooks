
from __future__ import annotations

import stat
from pathlib import Path

import pytest
from bare_machine import machine_bin, project_with_no_tools
from executable_stub import write_stub
from platform_probe import (
    A_MACHINE_THAT_DOES_NOT,
    A_MACHINE_THAT_SPELLS_A_COMMAND_ITSELF,
    off_windows,
)

from habit_hooks import project_paths
from habit_hooks.detectors import COMMAND_KIND, Detector
from habit_hooks.missing_tools import missing_tools
from habit_hooks.project_paths import tool_executable

JSCPD = Detector(name="jscpd", kind=COMMAND_KIND, install="npm i -D jscpd")


def test_a_command_nowhere_on_the_search_path_names_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    assert tool_executable("jscpd", project) is None


def test_a_command_in_the_project_s_own_bin_names_the_file_installed_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    off_windows(monkeypatch)
    bin_dir = project / ".venv" / "bin"
    write_stub(bin_dir, "jscpd")

    found = tool_executable("jscpd", project)

    assert found is not None
    assert Path(found).parent == bin_dir


def test_the_project_s_own_bin_wins_over_the_same_command_on_the_machine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(machine_bin(tmp_path), "jscpd")
    pinned = project / "node_modules" / ".bin"
    write_stub(pinned, "jscpd")

    assert Path(tool_executable("jscpd", project) or "").parent == pinned


def test_installing_a_tool_answers_the_setup_and_the_run_in_one_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    assert missing_tools([JSCPD], project) == (JSCPD,)
    assert tool_executable("jscpd", project) is None

    bin_dir = project / "node_modules" / ".bin"
    write_stub(bin_dir, "jscpd")

    assert missing_tools([JSCPD], project) == ()
    assert Path(tool_executable("jscpd", project) or "").parent == bin_dir


def test_a_command_found_in_this_process_s_own_directory_is_named_absolutely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    monkeypatch.setattr(project_paths.shutil, "which", lambda *_, **__: "./jscpd.cmd")

    assert tool_executable("jscpd", project) == str(Path.cwd() / "jscpd.cmd")


@A_MACHINE_THAT_SPELLS_A_COMMAND_ITSELF
def test_a_shim_answers_to_the_bare_name_it_was_installed_under(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "node_modules" / ".bin", "jscpd")

    found = tool_executable("jscpd", project)

    assert found is not None
    assert found.lower().endswith("jscpd.cmd")


@A_MACHINE_THAT_DOES_NOT
def test_a_shim_named_for_windows_is_no_command_at_all_here(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    shim = project / "node_modules" / ".bin" / "jscpd.cmd"
    shim.parent.mkdir(parents=True)
    shim.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)

    assert tool_executable("jscpd", project) is None
    assert tool_executable("jscpd.cmd", project) == str(shim)
