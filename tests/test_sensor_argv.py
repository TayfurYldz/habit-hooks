
from __future__ import annotations

from pathlib import Path

import pytest
from platform_probe import off_windows

from habit_hooks.argv_budget import argument_budget, argument_cost
from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def test_a_scope_past_the_argv_budget_runs_in_chunks(tmp_path: Path) -> None:
    (tmp_path / "count.py").write_text(
        "import sys, json\n"
        'print(json.dumps([{"smell": "s", "count": len(sys.argv) - 1,'
        ' "issues": []}]))\n',
        encoding="utf-8",
    )
    part = Part(
        name="probe",
        directory=tmp_path,
        argv=["${python}", "${dir}/count.py", "${files}"],
    )
    files = [f"generated/module_{index:06d}.py" for index in range(8_000)]
    assert sum(len(name) + 1 for name in files) > 2 * argument_budget()
    execution = Execution(project_dir=tmp_path, scope=Scope(files=files))

    findings = execution.run_sensor(part)

    assert len(findings) > 1
    assert sum(finding["count"] for finding in findings) == len(files)


def test_the_budget_counts_a_path_as_the_command_line_spells_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    part = Part(
        name="probe", command="${python} ${dir}/count.py ${files}", directory=tmp_path
    )
    files = [f"src/it's/o'clock_{index:05d}.py" for index in range(3_800)]
    assert sum(len(name) + 1 for name in files) < argument_budget()
    execution = Execution(project_dir=tmp_path, scope=Scope(files=files))

    commands = execution._sensor_commands(part)

    assert len(commands) > 1
    assert max(argument_cost(command) for command in commands) <= argument_budget()


def test_a_spawn_the_system_refuses_is_a_notice_not_a_traceback(
    tmp_path: Path,
) -> None:
    part = Part(name="probe", command="printf '[]'", directory=tmp_path)
    execution = Execution(
        project_dir=tmp_path / "deleted", scope=Scope(files=["src/a.py"])
    )

    run = execution.run_sensors([part])

    assert run.findings == []
    assert run.failed
    assert any("probe" in notice for notice in run.notices)


def test_an_argv_part_budgets_the_paths_unquoted_because_it_carries_them_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    part = Part(name="probe", directory=tmp_path, argv=["count", "${files}"])
    files = [f"src/it's/o'clock_{index:05d}.py" for index in range(3_800)]
    execution = Execution(project_dir=tmp_path, scope=Scope(files=files))

    commands = execution._sensor_commands(part)

    assert commands == [["count", *files]]
    assert argument_cost(commands[0]) <= argument_budget()


def test_an_argv_part_past_the_budget_still_runs_in_chunks(tmp_path: Path) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["count", "${files}"])
    files = [f"generated/module_{index:06d}.py" for index in range(8_000)]
    assert argument_cost(files) > 2 * argument_budget()
    execution = Execution(project_dir=tmp_path, scope=Scope(files=files))

    commands = execution._sensor_commands(part)

    assert len(commands) > 1
    assert [path for command in commands for path in command[1:]] == files
    assert max(argument_cost(command) for command in commands) <= argument_budget()
