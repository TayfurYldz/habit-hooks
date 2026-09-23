
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from executable_stub import write_batch_stub

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part, SensorError
from habit_hooks.sensors.spawn import Spawner


def _project_with_a_batch_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    project = project_with_no_tools(tmp_path, monkeypatch)
    return project, write_batch_stub(project / "node_modules" / ".bin", "probe")


def test_a_filename_can_never_become_cmd_syntax(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _ = _project_with_a_batch_tool(tmp_path, monkeypatch)
    marker = project / "PWNED"
    part = Part(name="probe", directory=project, argv=["probe.cmd", "${files}"])
    execution = Execution(
        project_dir=project, scope=Scope(files=["src/a&echo.>PWNED&.py"])
    )

    with pytest.raises(SensorError) as refusal:
        execution.run_sensor(part)

    assert not marker.exists()
    assert str(refusal.value).startswith(
        "sensor 'probe' cannot pass 'src/a&echo.>PWNED&.py' to "
    )


def test_a_batch_file_still_runs_when_every_argument_is_only_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, tool = _project_with_a_batch_tool(tmp_path, monkeypatch)

    result = Spawner(project).run(["probe.cmd", "--max", "200", "src/a.py"])

    assert result.returncode == 0
    assert result.args == [str(tool), "--max", "200", "src/a.py"]


def test_a_batch_file_named_by_its_own_path_is_refused_the_same(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, tool = _project_with_a_batch_tool(tmp_path, monkeypatch)

    with pytest.raises(SensorError):
        Spawner(project).run([str(tool), "src/a&b.py"])


def test_the_first_unreadable_argument_is_the_one_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _ = _project_with_a_batch_tool(tmp_path, monkeypatch)

    with pytest.raises(SensorError) as refusal:
        Spawner(project).run(["probe.cmd", "fine.py", "a&b.py", "c|d.py"])

    assert "'a&b.py'" in str(refusal.value)


@pytest.mark.parametrize("syntax", ["&", "|", "<", ">", "^", '"', "%", "\n", "\r"])
def test_every_character_cmd_exe_reads_as_syntax_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, syntax: str
) -> None:
    project, _ = _project_with_a_batch_tool(tmp_path, monkeypatch)

    with pytest.raises(SensorError):
        Spawner(project).run(["probe.cmd", f"src/a{syntax}b.py"])


@pytest.mark.parametrize("punctuation", ["(", ")", "!", "'", "$", " ", "#"])
def test_punctuation_cmd_exe_reads_as_text_is_left_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, punctuation: str
) -> None:
    project, tool = _project_with_a_batch_tool(tmp_path, monkeypatch)

    result = Spawner(project).run(["probe.cmd", f"src/a{punctuation}b.py"])

    assert result.args == [str(tool), f"src/a{punctuation}b.py"]


def test_the_same_argument_is_ordinary_text_for_a_program_that_is_no_batch_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    result = Spawner(project).run(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", "src/a&b.py"]
    )

    assert result.stdout.strip() == "src/a&b.py"


def test_a_refused_argument_fails_that_sensor_and_leaves_the_run_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, tool = _project_with_a_batch_tool(tmp_path, monkeypatch)
    part = Part(name="probe", directory=project, argv=["probe.cmd", "${files}"])
    execution = Execution(project_dir=project, scope=Scope(files=["src/a&b.py"]))

    run = execution.run_sensors([part])

    assert run.failed
    assert run.findings == []
    assert run.notices == [
        f"habit-sensors: sensor 'probe' cannot pass 'src/a&b.py' to {str(tool)!r}: "
        "a batch file is run by cmd.exe, which would read that as its own "
        "syntax rather than as text — rename the file, or keep it out of the "
        "scope with [files]"
    ]
