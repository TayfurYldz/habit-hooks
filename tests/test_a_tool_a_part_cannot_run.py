
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from detector_declarations import JSCPD, PMD, declaring
from executable_stub import write_stub
from plugin_fixture import one_sensor, one_transformer

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part, Run


def _recipe(*arguments: str) -> str:
    handed = "".join(f', "{argument}"' for argument in arguments)
    return f"argv = [\"${{python}}\", \"-c\", \"print('[]')\"{handed}]"


def _run(project: Path, part: Part) -> Run:
    scope = Scope(files=["src/a.py"])
    return Execution(project_dir=project, scope=scope).run_sensors([part])


def test_a_part_naming_no_tool_answers_for_none_of_its_plugins_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    part = one_sensor(project, _recipe(), declaring(JSCPD, PMD))

    assert part.detectors == {}
    assert _run(project, part).notices == []


def test_a_sensor_naming_a_tool_the_project_cannot_run_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    recipe = _recipe("${detector:jscpd}")

    run = _run(project, one_sensor(project, recipe, declaring(JSCPD)))

    assert run.failed
    assert run.findings == []
    assert run.notices == [
        "habit-sensors: sensor 's' needs the 'jscpd' command, which is not "
        "installed — install it, or disable the sensor with [sensors.s] "
        "disabled = true"
    ]

    write_stub(project / "node_modules" / ".bin", "jscpd")

    assert _run(project, one_sensor(project, recipe, declaring(JSCPD))).notices == []


def test_the_tool_a_part_is_told_about_is_the_absent_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "node_modules" / ".bin", "jscpd")
    recipe = _recipe("${detector:jscpd}", "${detector:pmd}")

    run = _run(project, one_sensor(project, recipe, declaring(JSCPD, PMD)))

    assert run.notices == [
        "habit-sensors: sensor 's' needs the 'pmd' command, which is not "
        "installed — install it, or disable the sensor with [sensors.s] "
        "disabled = true"
    ]


def test_a_transformer_naming_one_is_told_how_to_drop_a_transformer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    part = one_transformer(project, _recipe("${detector:jscpd}"), declaring(JSCPD))
    execution = Execution(project_dir=project, scope=Scope(files=[]))

    _, notices = execution.apply_transformers([part], [])

    assert notices == [
        "habit-sensors: transformer 't' needs the 'jscpd' command, which is not "
        "installed — install it, or drop 't' from the root transformers list"
    ]
