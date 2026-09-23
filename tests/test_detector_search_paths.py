
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import machine_bin, project_with_no_tools
from detector_config import accepting_search_paths, refusing_search_paths
from executable_stub import write_stub
from habit_hooks.detectors import COMMAND_KIND, NODE_MODULE_KIND, Detector
from habit_hooks.missing_tools import missing_tools
from habit_hooks.project_paths import tool_executable
from habit_hooks.sensors.named_tools import DeclaredTools

RUBOCOP = Detector(name="rubocop", kind=COMMAND_KIND, install="gem install rubocop")
BUNDLED_RUBOCOP = Detector(
    name="rubocop",
    kind=COMMAND_KIND,
    install="gem install rubocop",
    search_paths=("bin",),
)
BUNDLED_NODE = Detector(
    name="node", kind=COMMAND_KIND, install="brew install node", search_paths=("bin",)
)
TS_MORPH = Detector(name="ts-morph", kind=NODE_MODULE_KIND, install="npm i -D ts-morph")


def test_a_command_only_in_the_project_s_bin_is_found_by_no_default_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "bin", "rubocop")

    assert tool_executable("rubocop", project) is None
    assert missing_tools([RUBOCOP], project) == (RUBOCOP,)


def test_a_detector_s_own_search_path_finds_the_bundler_binstub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(machine_bin(tmp_path), "rubocop")
    write_stub(project / "bin", "rubocop")

    found = tool_executable("rubocop", project, ("bin",))

    assert Path(found or "").parent == project / "bin"


def test_a_bundler_binstub_answers_the_setup_and_the_run_in_one_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    tools = DeclaredTools([BUNDLED_RUBOCOP], project)

    assert missing_tools([BUNDLED_RUBOCOP], project) == (BUNDLED_RUBOCOP,)
    assert tools.file_for("rubocop") is None

    write_stub(project / "bin", "rubocop")

    assert missing_tools([BUNDLED_RUBOCOP], project) == ()
    assert Path(tools.file_for("rubocop") or "").parent == project / "bin"


def test_a_node_found_along_its_detector_s_search_path_answers_for_its_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    assert missing_tools([BUNDLED_NODE, TS_MORPH], project) == (BUNDLED_NODE,)

    write_stub(project / "bin", "node")

    assert missing_tools([BUNDLED_NODE, TS_MORPH], project) == ()


def test_a_directory_under_the_project_is_valid(tmp_path: Path) -> None:
    accepting_search_paths(tmp_path, '["bin"]')


def test_search_paths_written_as_a_string_is_refused(tmp_path: Path) -> None:
    assert "list" in refusing_search_paths(tmp_path, '"bin"')


def test_an_empty_search_path_is_refused(tmp_path: Path) -> None:
    assert "non-empty" in refusing_search_paths(tmp_path, '[""]')


def test_a_posix_absolute_search_path_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["/usr/local/bin"]')


def test_a_windows_drive_search_path_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["C:\\\\tools"]')


def test_a_drive_relative_search_path_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["C:tools"]')


def test_a_rooted_search_path_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["\\\\tools"]')


def test_a_search_path_climbing_out_of_the_project_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["../bin"]')


def test_a_search_path_that_climbs_and_returns_is_refused(tmp_path: Path) -> None:
    assert "under the project" in refusing_search_paths(tmp_path, '["bin/.."]')


@pytest.mark.parametrize("separator", [":", ";"])
def test_a_search_path_carrying_a_path_separator_is_refused(
    tmp_path: Path, separator: str
) -> None:
    assert "under the project" in refusing_search_paths(
        tmp_path, f'["bin{separator}../tools"]'
    )
