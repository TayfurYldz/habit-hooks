
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import machine_bin, project_with_no_tools
from detector_declarations import JSCPD, PMD, declaring
from executable_stub import write_stub
from platform_probe import A_MACHINE_THAT_DOES_NOT
from plugin_fixture import one_sensor

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def _argv(project: Path, part: Part) -> list[str]:
    return Execution(project_dir=project, scope=Scope(files=[]))._expand(part)


def test_a_named_tool_expands_to_the_file_this_project_runs_for_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    bin_dir = project / "node_modules" / ".bin"
    write_stub(bin_dir, "jscpd")
    part = one_sensor(
        project, 'argv = ["${detector:jscpd}", "--reporters", "json"]', declaring(JSCPD)
    )

    argv = _argv(project, part)

    assert Path(argv[0]).parent == bin_dir
    assert Path(argv[0]).stem == "jscpd"
    assert argv[1:] == ["--reporters", "json"]


def test_a_named_tool_fills_in_inside_the_argument_that_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    bin_dir = project / "node_modules" / ".bin"
    write_stub(bin_dir, "jscpd")
    part = one_sensor(
        project, 'argv = ["node", "h.cjs", "--jscpd=${detector:jscpd}"]', declaring(JSCPD)
    )

    named = _argv(project, part)[2].removeprefix("--jscpd=")

    assert Path(named).parent == bin_dir
    assert Path(named).stem == "jscpd"


def test_each_named_tool_expands_to_its_own_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    bin_dir = project / "node_modules" / ".bin"
    write_stub(bin_dir, "jscpd")
    write_stub(bin_dir, "pmd")
    part = one_sensor(
        project,
        'argv = ["${detector:jscpd}", "--against", "${detector:pmd}"]',
        declaring(JSCPD, PMD),
    )

    argv = _argv(project, part)

    assert [Path(argv[0]).stem, Path(argv[2]).stem] == ["jscpd", "pmd"]
    assert {Path(argv[0]).parent, Path(argv[2]).parent} == {bin_dir}


def test_a_tool_named_twice_stands_for_the_same_file_at_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    bin_dir = project / "node_modules" / ".bin"
    write_stub(bin_dir, "jscpd")
    part = one_sensor(
        project,
        'argv = ["${detector:jscpd}", "--called", "${detector:jscpd}"]',
        declaring(JSCPD),
    )

    argv = _argv(project, part)

    assert list(part.detectors) == ["jscpd"]
    assert Path(argv[0]).parent == bin_dir
    assert argv[2] == argv[0]


def test_a_named_tool_is_looked_for_along_the_search_path_its_detector_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "bin", "rubocop")
    declaring_bundler = declaring(
        '{ name = "rubocop", kind = "command", install = "gem install rubocop", '
        'search_paths = ["bin"] }'
    )
    part = one_sensor(
        project, 'argv = ["${detector:rubocop}", "--json"]', declaring_bundler
    )

    argv = _argv(project, part)

    assert Path(argv[0]).parent == project / "bin"
    assert Path(argv[0]).stem == "rubocop"


@A_MACHINE_THAT_DOES_NOT
def test_a_shell_recipe_splices_the_file_quoted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    machine = machine_bin(tmp_path) / "with a space"
    project = project_with_no_tools(tmp_path, monkeypatch)
    monkeypatch.setenv("PATH", str(machine))
    write_stub(machine, "jscpd")
    part = one_sensor(project, 'command = "${detector:jscpd} --json"', declaring(JSCPD))

    assert _argv(project, part)[2] == f"'{machine / 'jscpd'}' --json"
