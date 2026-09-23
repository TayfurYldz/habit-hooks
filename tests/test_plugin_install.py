
from __future__ import annotations

import shlex
import sys
from pathlib import Path

import pytest
from habit_hooks.plugin_install import install_commands

PYTHON = shlex.quote(sys.executable)


def test_a_project_missing_no_plugin_is_asked_to_install_nothing(
    pip_installed: None,
) -> None:
    assert install_commands(("python", "generic"), ()) == ()


def test_a_pip_install_goes_through_the_interpreter_habit_hooks_runs_from(
    pip_installed: None,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        f"{PYTHON} -m pip install habit-hooks-python",
    )


def test_pip_is_asked_once_per_missing_plugin_in_the_planned_order(
    pip_installed: None,
) -> None:
    planned = ("python", "typescript", "generic")

    assert install_commands(planned, ("python", "typescript")) == (
        f"{PYTHON} -m pip install habit-hooks-python",
        f"{PYTHON} -m pip install habit-hooks-typescript",
    )


def test_an_interpreter_path_with_a_space_stays_one_word(
    pip_installed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "executable", "/opt/My Tools/bin/python")

    assert install_commands(("python",), ("python",)) == (
        "'/opt/My Tools/bin/python' -m pip install habit-hooks-python",
    )


def test_a_project_venv_is_added_to_rather_than_left_out_of_a_global_install(
    uv_venv: None,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        f"uv pip install --python {PYTHON} habit-hooks-python",
    )


def test_a_pip_less_environment_is_asked_once_per_missing_plugin(
    uv_venv: None,
) -> None:
    planned = ("python", "typescript", "generic")

    assert install_commands(planned, ("python", "typescript")) == (
        f"uv pip install --python {PYTHON} habit-hooks-python",
        f"uv pip install --python {PYTHON} habit-hooks-typescript",
    )


def test_an_overlay_installs_into_the_environment_it_extends(
    uv_run_overlay: str,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        f"uv pip install --python {uv_run_overlay} habit-hooks-python",
    )


def test_a_cache_entry_with_a_pip_in_it_is_still_not_one_to_install_into(
    uvx_run_with_a_pip: None,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        "uv tool install 'habit-hooks[python]'",
    )


def test_an_environment_that_says_nothing_about_itself_is_taken_for_a_durable_one(
    pip_less_prefix: Path,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        f"uv pip install --python {PYTHON} habit-hooks-python",
    )


def test_a_plugin_name_cannot_say_something_the_config_did_not_in_a_pip_command(
    pip_installed: None,
) -> None:
    hostile = "$(touch pwned)"

    assert install_commands((hostile,), (hostile,)) == (
        f"{PYTHON} -m pip install 'habit-hooks-$(touch pwned)'",
    )


def test_an_interpreter_with_no_pip_is_never_told_to_run_one(
    uvx_run: None,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        "uv tool install 'habit-hooks[python]'",
    )


def test_a_uv_tool_reinstalls_itself_rather_than_adding_to_itself(
    uv_tool_installed: None,
) -> None:
    assert install_commands(("python", "generic"), ("python",)) == (
        "uv tool install 'habit-hooks[python]'",
    )
