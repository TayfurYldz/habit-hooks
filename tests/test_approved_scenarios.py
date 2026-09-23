
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

import approved_scenarios as scenarios
import exemplar_scenario as exemplar
from habit_hooks.cli import ConfigError
from habit_hooks.resolve import installed_plugin_dirs

FAILED = pytest.fail.Exception
SKIPPED = pytest.skip.Exception

def test_the_exemplar_scenario_approves(tmp_path: Path) -> None:
    scenarios.check("exemplar", exemplar.exemplar_scenario(tmp_path), tmp_path)


def test_a_drift_from_the_approval_prints_both_sides(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    approved = json.loads((scenario / "approved.json").read_text(encoding="utf-8"))
    approved[0]["issues"][0]["details"]["message"] = "stale wording"
    (scenario / "approved.json").write_text(json.dumps(approved), encoding="utf-8")

    with pytest.raises(FAILED) as drift:
        scenarios.check("exemplar", scenario, tmp_path)

    text = str(drift.value)
    assert "drifted from its approval" in text
    assert "stale wording" in text
    assert "a TODO left behind" in text


def test_a_scenario_without_approved_json_is_refused(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    (scenario / "approved.json").unlink()

    with pytest.raises(FAILED, match="approved.json"):
        scenarios.check("exemplar", scenario, tmp_path)


def test_a_scenario_without_a_sample_is_refused(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    shutil.rmtree(scenario / "sample")

    with pytest.raises(FAILED, match=r"sample/"):
        scenarios.check("exemplar", scenario, tmp_path)


def test_a_scenario_directory_naming_an_unknown_sensor_is_refused(
    tmp_path: Path,
) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    scenario.rename(scenario.parent / "no-such-sensor")

    with pytest.raises(FAILED) as refusal:
        scenarios.check("exemplar", scenario.parent / "no-such-sensor", tmp_path)

    text = str(refusal.value)
    assert "no-such-sensor" in text
    assert "stub-lint" in text


def test_a_scenario_whose_tool_is_absent_skips(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    shutil.rmtree(scenario / "sample" / "bin")

    with pytest.raises(SKIPPED, match="stub-lint"):
        scenarios.check("exemplar", scenario, tmp_path)


def test_a_scenario_naming_an_undeclared_tool_is_refused(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    (scenario / "scenario.toml").write_text("tool = 'ghost-lint'\n", encoding="utf-8")

    with pytest.raises(FAILED, match="ghost-lint"):
        scenarios.check("exemplar", scenario, tmp_path)


def test_a_scenario_toml_with_an_unknown_key_is_refused(tmp_path: Path) -> None:
    scenario = exemplar.exemplar_scenario(tmp_path)
    (scenario / "scenario.toml").write_text(
        "tool = 'stub-lint'\nreason = 'flaky tool'\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="reason"):
        scenarios.check("exemplar", scenario, tmp_path)


def _shipped() -> list[tuple[str, Path]]:
    return [
        (plugin, scenario)
        for plugin, plugin_dir in sorted(installed_plugin_dirs().items())
        for scenario in scenarios.scenarios_in(plugin_dir)
    ]


@pytest.fixture(autouse=True)
def _repo_tools_on_the_path(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_bin = Path(__file__).resolve().parents[1] / "node_modules" / ".bin"
    if repo_bin.is_dir():
        monkeypatch.setenv(
            "PATH", f"{repo_bin}{os.pathsep}{os.environ.get('PATH', '')}"
        )


@pytest.mark.parametrize(
    ("plugin", "scenario"),
    _shipped()
    or [
        pytest.param(
            None,
            None,
            marks=pytest.mark.skip("no installed plugin ships scenarios yet"),
        )
    ],
    ids=lambda value: value.name if isinstance(value, Path) else str(value),
)
def test_every_installed_scenario_still_approves(
    plugin: str, scenario: Path, tmp_path: Path
) -> None:
    scenarios.check(plugin, scenario, tmp_path / plugin)
