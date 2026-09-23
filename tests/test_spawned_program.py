
from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from executable_stub import write_stub
from platform_probe import (
    A_MACHINE_THAT_DOES_NOT,
    A_MACHINE_THAT_SPELLS_A_COMMAND_ITSELF,
    off_windows,
)

from habit_hooks.sensors.spawn import Spawner


@A_MACHINE_THAT_DOES_NOT
def test_a_bare_command_is_spawned_as_the_file_the_search_path_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    off_windows(monkeypatch)
    bin_dir = project / ".venv" / "bin"
    write_stub(bin_dir, "jscpd")

    result = Spawner(project).run(["jscpd", "--reporters", "json"])

    assert result.args == [str(bin_dir / "jscpd"), "--reporters", "json"]


@A_MACHINE_THAT_SPELLS_A_COMMAND_ITSELF
def test_a_shim_the_spawn_could_not_have_found_by_name_still_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    bin_dir = project / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "jscpd.cmd").write_text("@echo off\r\necho []\r\n", encoding="utf-8")

    result = Spawner(project).run(["jscpd"])

    assert result.returncode == 0
    assert result.stdout.strip() == "[]"


@A_MACHINE_THAT_DOES_NOT
def test_a_program_named_by_a_path_is_left_for_the_spawn_to_find(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    tool = project / "tools" / "probe"
    tool.parent.mkdir(parents=True)
    tool.write_text("#!/bin/sh\nprintf '[]'\n", encoding="utf-8")
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)

    result = Spawner(project).run(["tools/probe"])

    assert result.args == ["tools/probe"]
    assert result.stdout == "[]"


def test_every_argument_after_the_program_is_spawned_exactly_as_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    script = project / "probe.py"
    script.write_text("print('[]')\n", encoding="utf-8")

    result = Spawner(project).run([sys.executable, str(script)])

    assert result.args == [sys.executable, str(script)]
    assert result.stdout.strip() == "[]"


def test_a_command_nobody_installed_in_a_project_that_is_gone_names_the_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    with pytest.raises(FileNotFoundError) as refusal:
        Spawner(project / "deleted").run(["jscpd"])

    assert "deleted" in str(refusal.value)
    assert "jscpd" not in str(refusal.value)
