
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks.cli import ConfigError
from plugin_fixture import (
    loader_for,
    one_sensor,
    write_plugin,
    write_project_config,
)


def test_an_argv_spec_reaches_the_part_as_a_list(tmp_path: Path) -> None:
    part = one_sensor(tmp_path, 'argv = ["ruff", "check", "${files}"]')

    assert part.argv == ["ruff", "check", "${files}"]
    assert part.command is None


def test_a_spec_spelling_both_command_and_argv_is_refused_by_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(ConfigError) as refusal:
        one_sensor(tmp_path, 'command = "ruff"\nargv = ["ruff"]')

    assert str(refusal.value).startswith("sensor 's' spells both 'command' and 'argv'")


def test_a_spec_spelling_neither_is_refused_by_name(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as refusal:
        one_sensor(tmp_path, 'files = ["src/**"]')

    assert str(refusal.value).startswith("sensor 's' spells neither 'command' nor 'argv'")


def test_a_spec_spelling_an_empty_argv_is_refused_by_name(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as refusal:
        one_sensor(tmp_path, "argv = []")

    assert str(refusal.value).startswith("sensor 's' spells an empty 'argv'")


def test_a_spec_spelling_an_argv_element_that_is_not_text_is_refused_by_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(ConfigError) as refusal:
        one_sensor(tmp_path, 'argv = ["ruff", 1]')

    assert str(refusal.value).startswith("sensor 's' spells 1 in its 'argv'")


def test_a_spec_spelling_an_argv_that_is_not_a_list_is_refused_by_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(ConfigError) as refusal:
        one_sensor(tmp_path, 'argv = "ruff"')

    assert str(refusal.value).startswith("sensor 's' spells 'ruff' as its 'argv'")


def test_an_argv_of_one_element_is_a_part_that_runs(tmp_path: Path) -> None:
    part = one_sensor(tmp_path, 'argv = ["ruff"]')

    assert part.argv == ["ruff"]


def test_a_transformer_missing_its_recipe_is_named_a_transformer(
    tmp_path: Path,
) -> None:
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": 'sensors = []', "transformers/t.toml": 'files = ["src/**"]'},
    )

    with pytest.raises(ConfigError) as refusal:
        loader_for(tmp_path).resolve_part(["fixt"], "transformers", "t")

    assert str(refusal.value).startswith("transformer 't' spells neither")


def test_disabled_override_drops_the_sensor(tmp_path: Path) -> None:
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": 'sensors = ["s"]', "sensors/s.toml": 'command = "echo"'},
    )
    write_project_config(tmp_path, 'plugins = ["fixt"]\n[sensors.s]\ndisabled = true')
    assert loader_for(tmp_path).load_plugin("fixt").sensors == []


def test_args_override_reaches_the_part(tmp_path: Path) -> None:
    part = one_sensor(tmp_path, 'command = "echo ${args}"\nargs = ["--from-spec"]')
    assert part.args == ["--from-spec"]

    write_project_config(
        tmp_path, 'plugins = ["fixt"]\n[sensors.s]\nargs = ["--from-project"]'
    )
    assert loader_for(tmp_path).load_plugin("fixt").sensors[0].args == ["--from-project"]


def test_an_emptied_args_override_clears_the_specs_default(tmp_path: Path) -> None:
    one_sensor(tmp_path, 'command = "echo"\nargs = ["--from-spec"]')
    write_project_config(tmp_path, 'plugins = ["fixt"]\n[sensors.s]\nargs = []')

    assert loader_for(tmp_path).load_plugin("fixt").sensors[0].args == []


def test_sensor_spec_files_default_reaches_the_part(tmp_path: Path) -> None:
    part = one_sensor(tmp_path, 'command = "echo ${files}"\nfiles = ["src/**"]')
    assert part.files == ["src/**"]


def test_files_override_replaces_the_sensor_spec_default(tmp_path: Path) -> None:
    one_sensor(tmp_path, 'command = "echo ${files}"\nfiles = ["src/**"]')
    write_project_config(tmp_path, 'plugins = ["fixt"]\n[sensors.s]\nfiles = ["lib/**"]')
    assert loader_for(tmp_path).load_plugin("fixt").sensors[0].files == ["lib/**"]


def test_a_sensor_declaring_no_files_carries_none(tmp_path: Path) -> None:
    part = one_sensor(tmp_path, 'command = "echo ${files}"')
    assert part.files is None


def test_a_sensor_spec_that_is_not_toml_is_refused_by_name(tmp_path: Path) -> None:
    spec = tmp_path / ".habit-hooks" / "fixt" / "sensors" / "s.toml"

    with pytest.raises(SystemExit) as failure:
        one_sensor(tmp_path, 'command = "echo')

    assert str(failure.value) == (
        f"{spec}: invalid TOML: Unterminated string (at end of document)"
    )
