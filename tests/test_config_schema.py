
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks.config import load_config
from refusal import refusal_from
from plugin_fixture import write_plugin, write_project_config


def _project(tmp_path: Path, body: str) -> Path:
    write_project_config(tmp_path, body)
    return tmp_path


def _load(project_dir: Path) -> None:
    load_config(project_dir)


def _refusal(project_dir: Path) -> str:
    return refusal_from(lambda: _load(project_dir))


def _config_path(project_dir: Path) -> Path:
    return project_dir / ".habit-hooks" / "config.toml"


def test_an_unclosed_array_is_refused_by_file_and_reason(tmp_path: Path) -> None:
    project = _project(tmp_path, 'plugins = ["generic"]\nfiles   = ["src/**"')

    assert _refusal(project) == (
        f"{_config_path(project)}: invalid TOML: Unclosed array (at end of document)"
    )


def test_a_duplicated_table_is_refused_the_same_way(tmp_path: Path) -> None:
    body = '[scope]\nbranchBase = "main"\n\n[scope]\nmainBranch = "x"'
    project = _project(tmp_path, body)

    assert _refusal(project) == (
        f"{_config_path(project)}: invalid TOML: "
        "Cannot declare ('scope',) twice (at line 4, column 7)"
    )


def test_a_malformed_plugin_config_is_refused_too(tmp_path: Path) -> None:
    project = _project(tmp_path, 'plugins = ["alpha"]')
    write_plugin(project, "alpha", {"config.toml": 'sensors = ["s"'})

    assert _refusal(project) == (
        f"{project / '.habit-hooks' / 'alpha' / 'config.toml'}: invalid TOML: "
        "Unclosed array (at end of document)"
    )


def test_an_unknown_root_key_is_rejected_by_name(tmp_path: Path) -> None:
    project = _project(tmp_path, 'plugins = ["generic"]\n[sensor.knip]\ndisabled = true')
    with pytest.raises(SystemExit, match=r"'sensor'"):
        _load(project)


def test_an_unknown_scope_key_is_rejected_by_name(tmp_path: Path) -> None:
    project = _project(tmp_path, "[scope]\nchange_dOnly = true")
    with pytest.raises(SystemExit, match=r"'change_dOnly'"):
        _load(project)


def test_an_unknown_sensor_key_is_rejected_by_name(tmp_path: Path) -> None:
    project = _project(tmp_path, "[sensors.line-count]\ndisable = true")
    with pytest.raises(SystemExit, match=r"'disable'"):
        _load(project)


def test_an_unknown_smell_key_is_rejected_by_name(tmp_path: Path) -> None:
    project = _project(tmp_path, '[smells.duplicated-code]\nseverty = "suggested"')
    with pytest.raises(SystemExit, match=r"'severty'"):
        _load(project)


def test_an_unknown_uncoached_value_is_rejected_with_the_valid_ones(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path, 'uncoached = "supress"')
    with pytest.raises(SystemExit, match=r"'supress'") as failure:
        _load(project)
    message = str(failure.value)
    assert "'uncoached'" in message
    assert "'enforce', 'ignore', 'suggest'" in message


def test_an_unknown_plugin_config_key_is_rejected_by_name(tmp_path: Path) -> None:
    project = _project(tmp_path, 'plugins = ["alpha"]')
    write_plugin(project, "alpha", {"config.toml": 'sensors = ["s"]\nsensorz = ["oops"]'})
    with pytest.raises(SystemExit, match=r"'sensorz'"):
        _load(project)


def test_a_rejection_names_no_binary(tmp_path: Path) -> None:
    project = _project(tmp_path, '[smells.duplicated-code]\nseverty = "suggested"')
    with pytest.raises(SystemExit) as failure:
        load_config(project)
    assert str(failure.value).startswith("unknown config key")
