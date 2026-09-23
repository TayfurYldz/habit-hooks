
from __future__ import annotations

import shlex
import sys
from collections.abc import Sequence
from importlib.util import find_spec
from pathlib import Path

from .plugin_packages import (
    CORE_DISTRIBUTION,
    depended_on_plugins,
    distribution,
    provided_extras,
)

UV_TOOL_RECEIPT = "uv-receipt.toml"

VENV_CONFIG = "pyvenv.cfg"
RELOCATABLE = "relocatable"
EXTENDED_ENVIRONMENT = "extends-environment"


def _installed_as_a_uv_tool() -> bool:
    return (Path(sys.prefix) / UV_TOOL_RECEIPT).is_file()


def _uv_tool_command(packaged: Sequence[str]) -> str:
    extras = provided_extras()
    shipped = ",".join(plugin for plugin in packaged if plugin in extras)
    target = f"{CORE_DISTRIBUTION}[{shipped}]" if shipped else CORE_DISTRIBUTION
    brought_by_habit_hooks = extras | depended_on_plugins()
    separate = "".join(
        f" --with {shlex.quote(distribution(plugin))}"
        for plugin in packaged
        if plugin not in brought_by_habit_hooks
    )
    return f"uv tool install {shlex.quote(target)}{separate}"


def _venv_settings() -> dict[str, str]:
    config = Path(sys.prefix) / VENV_CONFIG
    try:
        lines = config.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    settings = (line.partition("=") for line in lines)
    return {key.strip(): value.strip() for key, _, value in settings}


def _a_cache_entry_uv_owns() -> bool:
    return _venv_settings().get(RELOCATABLE) == "true"


def _pip_can_be_run() -> bool:
    return find_spec("pip") is not None


def _uv_pip_command(environment: str, plugin: str) -> str:
    return (
        f"uv pip install --python {shlex.quote(environment)} "
        f"{shlex.quote(distribution(plugin))}"
    )


def _added_to_this_environment(plugin: str) -> str:
    if _pip_can_be_run():
        return (
            f"{shlex.quote(sys.executable)} -m pip install "
            f"{shlex.quote(distribution(plugin))}"
        )
    return _uv_pip_command(sys.executable, plugin)


def install_commands(
    packaged: Sequence[str], uninstalled: Sequence[str]
) -> tuple[str, ...]:
    if not uninstalled:
        return ()
    extended = _venv_settings().get(EXTENDED_ENVIRONMENT)
    if extended is not None:
        return tuple(_uv_pip_command(extended, plugin) for plugin in uninstalled)
    if _installed_as_a_uv_tool() or _a_cache_entry_uv_owns():
        return (_uv_tool_command(packaged),)
    return tuple(_added_to_this_environment(plugin) for plugin in uninstalled)
