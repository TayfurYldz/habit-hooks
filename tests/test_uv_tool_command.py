
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from habit_hooks import resolve
from habit_hooks.initialise import plan
from habit_hooks.plugin_install import install_commands
from plugin_fixture import write_plugin, write_project_config


@pytest.fixture
def installed_machine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[..., None]:

    def holding(**distributions: str) -> None:
        dirs = {}
        for plugin in distributions:
            directory = tmp_path / plugin
            directory.mkdir()
            (directory / "config.toml").write_text("", encoding="utf-8")
            dirs[plugin] = directory
        monkeypatch.setattr(resolve, "installed_plugin_dirs", lambda: dirs)
        monkeypatch.setattr(
            resolve, "installed_plugin_distributions", lambda: distributions
        )

    return holding


def test_every_installed_plugin_has_a_distribution_name() -> None:
    assert set(resolve.installed_plugin_distributions()) == set(
        resolve.installed_plugin_dirs()
    )


def test_an_installed_plugin_is_reinstalled_under_the_name_it_arrived_under(
    installed_machine: Callable[..., None], uv_tool_installed: None
) -> None:
    installed_machine(cobol="acme-hooks-cobol", generic="habit-hooks-generic")

    assert install_commands(("cobol", "python", "generic"), ("python",)) == (
        "uv tool install 'habit-hooks[python]' --with acme-hooks-cobol",
    )


def test_every_missing_plugin_is_installed_in_one_command(
    uv_tool_installed: None,
) -> None:
    planned = ("python", "typescript", "generic")

    assert install_commands(planned, ("python", "typescript")) == (
        "uv tool install 'habit-hooks[python,typescript]'",
    )


def test_the_plugins_this_project_already_has_are_named_again(
    uv_tool_installed: None,
) -> None:
    planned = ("python", "typescript", "generic")

    assert install_commands(planned, ("python",)) == (
        "uv tool install 'habit-hooks[python,typescript]'",
    )


def test_a_plugin_habit_hooks_does_not_ship_is_named_beside_the_extras(
    uv_tool_installed: None,
) -> None:
    assert install_commands(("cobol", "python", "generic"), ("cobol",)) == (
        "uv tool install 'habit-hooks[python]' --with habit-hooks-cobol",
    )


def test_a_plugin_habit_hooks_does_not_ship_is_kept_once_it_is_installed(
    uv_tool_installed: None,
) -> None:
    assert install_commands(("cobol", "python", "generic"), ("python",)) == (
        "uv tool install 'habit-hooks[python]' --with habit-hooks-cobol",
    )


def test_a_uv_tool_needing_no_shipped_plugin_names_habit_hooks_plainly(
    uv_tool_installed: None,
) -> None:
    assert install_commands(("cobol", "generic"), ("cobol",)) == (
        "uv tool install habit-hooks --with habit-hooks-cobol",
    )


def test_a_plugin_name_cannot_say_something_the_config_did_not_to_uv(
    uv_tool_installed: None,
) -> None:
    hostile = "$(touch pwned)"

    assert install_commands((hostile, "generic"), (hostile,)) == (
        "uv tool install habit-hooks --with 'habit-hooks-$(touch pwned)'",
    )


def test_a_plugin_this_project_already_has_is_named_again(
    init_project: Path, installed_machine: Callable[..., None], uv_tool_installed: None
) -> None:
    installed_machine(cobol="habit-hooks-cobol", generic="habit-hooks-generic")
    write_project_config(init_project, 'plugins = ["cobol", "python", "generic"]')

    assert plan(init_project).plugin_installs == (
        "uv tool install 'habit-hooks[python]' --with habit-hooks-cobol",
    )


def test_a_plugin_only_the_project_next_door_runs_is_kept(
    init_project: Path, installed_machine: Callable[..., None], uv_tool_installed: None
) -> None:
    installed_machine(python="habit-hooks-python", generic="habit-hooks-generic")
    write_project_config(init_project, 'plugins = ["php", "generic"]')

    assert plan(init_project).plugin_installs == (
        "uv tool install 'habit-hooks[python,php]'",
    )


def test_a_plugin_kept_in_the_project_is_left_out_of_the_command(
    init_project: Path, pluginless_machine: None, uv_tool_installed: None
) -> None:
    write_plugin(init_project, "cobol", {"config.toml": ""})
    write_project_config(init_project, 'plugins = ["cobol", "python", "generic"]')

    assert plan(init_project).plugin_installs == (
        "uv tool install 'habit-hooks[python]'",
    )
