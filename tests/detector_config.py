
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks.config import load_config
from plugin_fixture import write_plugin, write_project_config

INSTALL = 'install = "brew install jq"'


def declaring(tmp_path: Path, body: str) -> Path:
    write_project_config(tmp_path, 'plugins = ["alpha"]')
    write_plugin(tmp_path, "alpha", {"config.toml": body})
    return tmp_path


def refusal_for(project_dir: Path) -> str:
    with pytest.raises(SystemExit) as failure:
        load_config(project_dir)
    return str(failure.value)


def declaring_search_paths(tmp_path: Path, search_paths: str) -> None:
    entry = (
        f'{{ name = "jq", kind = "command", {INSTALL}, search_paths = {search_paths} }}'
    )
    declaring(tmp_path, f"detectors = [{entry}]")


def refusing_search_paths(tmp_path: Path, search_paths: str) -> str:
    declaring_search_paths(tmp_path, search_paths)
    message = refusal_for(tmp_path)
    assert "detector 'jq'" in message
    assert "'search_paths'" in message
    return message


def accepting_search_paths(tmp_path: Path, search_paths: str) -> None:
    declaring_search_paths(tmp_path, search_paths)
    load_config(tmp_path)
