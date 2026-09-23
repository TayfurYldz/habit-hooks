
from __future__ import annotations

import difflib
import json
import shutil
from pathlib import Path

import pytest

from habit_hooks.config import Config, load_config
from habit_hooks.config_schema import read_toml, reject_unknown
from habit_hooks.missing_tools import missing_tools
from habit_hooks.resolve import Resolver
from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.loader import PluginLoader
from habit_hooks.sensors.model import Part

SCENARIO_KEYS = frozenset({"tool"})


def _staged(plugin: str, scenario: Path, project: Path) -> Config:
    if not (scenario / "sample").is_dir():
        _refuses(
            scenario,
            "ships no sample/ directory — the sample codebase is the "
            "run's scope",
        )
    if not (scenario / "approved.json").is_file():
        _refuses(
            scenario,
            "ships no approved.json — the findings the sensor must "
            "produce over sample/, and nothing else",
        )
    shutil.copytree(scenario / "sample", project, dirs_exist_ok=True)
    (project / ".habit-hooks").mkdir(parents=True, exist_ok=True)
    (project / ".habit-hooks" / "config.toml").write_text(
        f"plugins = [{plugin!r}]\n", encoding="utf-8"
    )
    return load_config(project)


def scenarios_in(plugin_dir: Path) -> list[Path]:
    scenarios = plugin_dir / "scenarios"
    if not scenarios.is_dir():
        return []
    return sorted(entry for entry in scenarios.iterdir() if entry.is_dir())


def check(plugin: str, scenario: Path, project: Path) -> None:
    config = _staged(plugin, scenario, project)
    loader = PluginLoader(Resolver.discover(project), config)
    sensor = _sensor_named(plugin, scenario, loader)
    _skip_when_tool_absent(scenario, config, project)
    run = Execution(
        project_dir=project, scope=Scope(files=_scoped_paths(project))
    ).run_sensors([sensor])
    if run.notices:
        pytest.fail(
            f"scenario {scenario.name!r}: the sensor run failed\n"
            + "\n".join(run.notices)
        )
    _matches_approved(scenario, run.findings)


def _sensor_named(plugin: str, scenario: Path, loader: PluginLoader) -> Part:
    sensors = loader.load_plugin(plugin).sensors
    for sensor in sensors:
        if sensor.name == scenario.name:
            return sensor
    enabled = ", ".join(sorted(sensor.name for sensor in sensors)) or "none"
    pytest.fail(
        f"the scenario directory is named {scenario.name!r}, but the "
        f"{plugin!r} plugin enables no sensor by that name (it "
        f"enables: {enabled}) — a scenario directory is named after the "
        "sensor it runs"
    )


def _skip_when_tool_absent(scenario: Path, config: Config, project: Path) -> None:
    meta = scenario / "scenario.toml"
    if not meta.is_file():
        return
    spec = read_toml(meta)
    reject_unknown(SCENARIO_KEYS, spec, f"scenario {scenario.name!r}")
    tool = _tool_named_in(scenario, spec)
    declared = [d for d in config.plugin_detectors if d.name == tool]
    if not declared:
        _refuses(
            scenario,
            f"names the tool {tool!r} in scenario.toml, which no plugin "
            "declares as a detector",
        )
    if missing_tools(declared, project):
        pytest.skip(
            f"scenario {scenario.name!r}: its tool {tool!r} is not "
            "installed on this machine"
        )


def _tool_named_in(scenario: Path, spec: dict) -> str:
    tool = spec.get("tool")
    if isinstance(tool, str) and tool:
        return tool
    _refuses(
        scenario,
        f"spells {tool!r} as its scenario.toml 'tool' — the name of the "
        "sensor's tool is expected there",
    )


def _scoped_paths(project: Path) -> list[str]:
    return sorted(
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file() and ".habit-hooks" not in path.parts
    )


def _matches_approved(scenario: Path, findings: list[dict]) -> None:
    approved = json.loads((scenario / "approved.json").read_text(encoding="utf-8"))
    if not isinstance(approved, list):
        _refuses(
            scenario,
            "spells an approved.json that is not a findings array — it holds "
            "the findings JSON only, never guide strings",
        )
    if findings == approved:
        return
    drift = "\n".join(
        difflib.unified_diff(
            _printed(approved),
            _printed(findings),
            "approved.json",
            "this run",
            lineterm="",
        )
    )
    pytest.fail(
        f"scenario {scenario.name!r}: the sensor drifted from its approval\n{drift}"
    )


def _printed(payload: object) -> list[str]:
    return json.dumps(payload, indent=2, sort_keys=True).splitlines()


def _refuses(scenario: Path, problem: str) -> None:
    pytest.fail(f"scenario {scenario.name!r} {problem}")
