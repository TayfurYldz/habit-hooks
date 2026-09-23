
from __future__ import annotations

from pathlib import Path

from habit_hooks.initialise import plan
from plugin_fixture import write_plugin, write_project_config

_NEEDING_A_TOOL = (
    'detectors = [{ name = "wobble", kind = "command",'
    ' install = "brew install wobble" }]'
)


def test_a_planned_plugin_nobody_has_is_what_stands_in_the_way(
    init_project: Path, pluginless_machine: None
) -> None:
    (init_project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    planned = plan(init_project)

    assert planned.plugins == ("python", "generic")
    assert planned.uninstalled_plugins == ("python",)
    assert planned.plugin_installs != ()


def test_a_vendored_plugin_is_one_this_project_has(
    init_project: Path, pluginless_machine: None
) -> None:
    assert plan(init_project).uninstalled_plugins == ()


def test_a_configured_plugin_nobody_has_is_reported_by_a_re_run(
    init_project: Path,
) -> None:
    write_project_config(init_project, 'plugins = ["cobol", "generic"]')

    assert plan(init_project).uninstalled_plugins == ("cobol",)


def test_the_plugins_are_installed_before_the_tools_they_bring(
    init_project: Path, pluginless_machine: None
) -> None:
    write_plugin(init_project, "generic", {"config.toml": _NEEDING_A_TOOL})
    write_project_config(init_project, 'plugins = ["cobol", "generic"]')

    planned = plan(init_project)

    assert planned.installs == (*planned.plugin_installs, "brew install wobble")
