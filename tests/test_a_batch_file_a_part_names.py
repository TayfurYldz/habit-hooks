
from __future__ import annotations

from pathlib import Path

import pytest
from batch_tool_project import (
    BATCH_TOOL,
    PLAIN_TOOL,
    batch_sensor,
    installing_a_batch_tool,
    recipe,
)
from bare_machine import project_with_no_tools
from detector_declarations import declaring
from executable_stub import write_batch_stub, write_stub
from platform_probe import A_MACHINE_THAT_DOES_NOT, A_SHELL_TO_RUN_IT_WITH
from plugin_fixture import one_sensor, one_transformer

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from sensor_run import run_sensor


def test_a_batch_tool_a_part_names_reads_that_parts_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = installing_a_batch_tool(tmp_path, monkeypatch)
    tool = project / "node_modules" / ".bin" / "probe.cmd"

    run = run_sensor(batch_sensor(project), files=("src/a&echo.>PWNED&.py",))

    assert run.findings == []
    assert run.notices == [
        "habit-sensors: sensor 's' cannot pass 'src/a&echo.>PWNED&.py' to "
        f"{str(tool)!r}: a batch file is run by cmd.exe, which would read that "
        "as its own syntax rather than as text — rename the file, or keep it "
        "out of the scope with [files]"
    ]


def test_a_batch_tool_is_found_wherever_a_part_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = installing_a_batch_tool(tmp_path, monkeypatch)
    write_stub(project / "node_modules" / ".bin", "probe2")
    part = one_sensor(
        project,
        recipe("${detector:probe.cmd}", "${detector:probe2}"),
        declaring(BATCH_TOOL, PLAIN_TOOL.replace("probe", "probe2")),
    )

    assert run_sensor(part, files=("src/a&b.py",)).failed


def test_an_argument_of_only_text_still_reaches_a_batch_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = installing_a_batch_tool(tmp_path, monkeypatch)

    run = run_sensor(batch_sensor(project), files=("src/a.py", "build.bat",))

    assert run.notices == []


def test_a_scoped_batch_file_is_data_and_never_a_program(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    part = one_sensor(project, recipe())

    run = run_sensor(part, files=("build.bat", "src/a&b.py",))

    assert run.notices == []


@A_MACHINE_THAT_DOES_NOT
def test_a_tool_that_is_no_batch_file_reads_the_same_argument_as_a_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "node_modules" / ".bin", "probe")
    part = one_sensor(project, recipe("${detector:probe}"), declaring(PLAIN_TOOL))

    run = run_sensor(part, files=("src/a&b.py",))

    assert run.notices == []


@A_SHELL_TO_RUN_IT_WITH
def test_a_shell_recipe_is_text_to_split_and_not_arguments(tmp_path: Path) -> None:
    project = tmp_path / "project"
    write_batch_stub(project / "node_modules" / ".bin", "probe")
    shell_recipe = 'command = "${detector:probe.cmd} ${files} >/dev/null; printf \'[]\'"'
    part = one_sensor(project, shell_recipe, declaring(BATCH_TOOL))

    run = run_sensor(part, files=("src/a.py",))

    assert run.notices == []


def test_a_tool_nobody_installed_is_still_the_missing_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    run = run_sensor(batch_sensor(project), files=("src/a&b.py",))

    assert run.notices == [
        "habit-sensors: sensor 's' needs the 'probe.cmd' command, which is not "
        "installed — install it, or disable the sensor with [sensors.s] "
        "disabled = true"
    ]


def test_a_transformer_naming_one_is_refused_under_its_own_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = installing_a_batch_tool(tmp_path, monkeypatch)
    part = one_transformer(
        project, recipe("${detector:probe.cmd}"), declaring(BATCH_TOOL)
    )
    execution = Execution(project_dir=project, scope=Scope(files=["src/a&b.py"]))

    _, notices = execution.apply_transformers([part], [])

    assert notices == [
        "habit-sensors: transformer 't' cannot pass 'src/a&b.py' to "
        f"{str(project / 'node_modules' / '.bin' / 'probe.cmd')!r}: a batch file "
        "is run by cmd.exe, which would read that as its own syntax rather than "
        "as text — rename the file, or keep it out of the scope with [files]"
    ]
