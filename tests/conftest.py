
from __future__ import annotations

import sys
from importlib.machinery import ModuleSpec
from pathlib import Path

import pytest
from habit_hooks import plugin_install, resolve
from habit_hooks.plugin_install import UV_TOOL_RECEIPT, VENV_CONFIG
from git_repo import stop_the_upward_walk_at
from plugin_fixture import write_plugin
from wheelhouse import build_wheels, install_wheels


@pytest.fixture
def git_ceiling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stop_the_upward_walk_at(tmp_path, monkeypatch)

SHIPPED_PACKAGES = (
    "habit-hooks",
    "habit-hooks-generic",
    "habit-hooks-java",
    "habit-hooks-php",
    "habit-hooks-python",
    "habit-hooks-ruby",
    "habit-hooks-typescript",
)


@pytest.fixture(scope="session")
def installed_habit_sensors(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("wheel-smoke")
    wheels_dir = root / "wheels"
    wheels_dir.mkdir()
    build_wheels(wheels_dir, SHIPPED_PACKAGES)
    return install_wheels(root / "venv", wheels_dir)


@pytest.fixture
def init_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    created = tmp_path / "project"
    created.mkdir()
    write_plugin(created, "generic", {"config.toml": ""})
    return created


@pytest.fixture
def pluginless_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resolve, "installed_plugin_dirs", dict)


def _resolving(module: str) -> ModuleSpec:
    return ModuleSpec(module, loader=None)


def _finding_nothing(module: str) -> None:
    return None


@pytest.fixture
def pip_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(plugin_install, "find_spec", _resolving)


@pytest.fixture
def pip_less_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(plugin_install, "find_spec", _finding_nothing)
    return tmp_path


@pytest.fixture
def uvx_run(pip_less_prefix: Path) -> None:
    (pip_less_prefix / VENV_CONFIG).write_text("uv = 0.8.11\nrelocatable = true\n", encoding="utf-8")


@pytest.fixture
def uvx_run_with_a_pip(uvx_run: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(plugin_install, "find_spec", _resolving)


@pytest.fixture
def uv_run_overlay(pip_less_prefix: Path) -> str:
    extended = "/opt/project-venv"
    (pip_less_prefix / VENV_CONFIG).write_text(
        f"uv = 0.8.11\nextends-environment = {extended}\n", encoding="utf-8"
    )
    return extended


@pytest.fixture
def uv_venv(pip_less_prefix: Path) -> None:
    (pip_less_prefix / VENV_CONFIG).write_text("uv = 0.8.11\nprompt = project\n", encoding="utf-8")


@pytest.fixture
def uv_tool_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / UV_TOOL_RECEIPT).write_text("[tool]\n", encoding="utf-8")
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(plugin_install, "find_spec", _resolving)


@pytest.fixture
def toolless_project(init_project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    empty = init_project.parent / "no-tools"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    return init_project
