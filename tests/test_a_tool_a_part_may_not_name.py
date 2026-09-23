
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from detector_declarations import PMD, TS_MORPH, declaring
from plugin_fixture import loader_for, one_sensor, write_plugin, write_project_config

from habit_hooks.cli import ConfigError


def test_a_tool_no_plugin_declares_is_refused_when_the_config_loads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    with pytest.raises(ConfigError) as refusal:
        one_sensor(project, 'argv = ["${detector:jscpd}"]', declaring(PMD))

    assert str(refusal.value) == (
        "sensor 's' names ${detector:jscpd}, which no active plugin declares: a "
        "plugin names the tools its sensors reach for in its config.toml "
        "'detectors', and this run declares pmd (command) — disable the sensor "
        "with [sensors.s] disabled = true"
    )


def test_a_plugin_that_declares_nothing_is_told_it_declared_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    with pytest.raises(ConfigError) as refusal:
        one_sensor(project, 'argv = ["${detector:jscpd}"]')

    assert "this run declares none" in str(refusal.value)


def test_a_placeholder_naming_nothing_is_a_typo_and_not_an_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    with pytest.raises(ConfigError) as refusal:
        one_sensor(project, 'argv = ["${detector:}"]', declaring(PMD))

    assert "sensor 's' names ${detector:}, which no active plugin declares" in str(
        refusal.value
    )


def test_switching_the_sensor_off_really_does_clear_the_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_plugin(
        project,
        "fixt",
        {
            "config.toml": f'sensors = ["s"]\n{declaring(PMD)}',
            "sensors/s.toml": 'argv = ["${detector:jscpd}"]',
        },
    )
    write_project_config(project, 'plugins = ["fixt"]\n[sensors.s]\ndisabled = true')

    assert loader_for(project).load_plugin("fixt").sensors == []


def test_a_module_node_reads_is_no_command_and_is_refused_as_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)

    with pytest.raises(ConfigError) as refusal:
        one_sensor(project, 'argv = ["${detector:ts-morph}"]', declaring(TS_MORPH))

    assert str(refusal.value) == (
        "sensor 's' names ${detector:ts-morph}, but 'ts-morph' is declared "
        "'node-module', not 'command': only a command names a file this run can "
        "spawn, and a module is read by node from the project, never spawned by "
        "name — disable the sensor with [sensors.s] disabled = true"
    )
