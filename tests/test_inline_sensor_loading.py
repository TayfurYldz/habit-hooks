"""Loading the declarative inline sensor: an entry in a plugin's config.toml.

An inline entry is a table in the ``sensors`` list — ``sensors = [{ tool = ... }]``
— naming the tool, its arguments, and the pipeline that turns its output into
findings. Loading is where every misspelling is answered: an unknown key, a
missing transform program, a table that shadows a shipped ``sensors/<name>.toml``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from plugin_fixture import loader_for, write_plugin, write_project_config

PYTHON_TOOL = '{ tool = "${python}", name = "lint", args = ["${dir}/tool.py"] }'


def inline_part(project: Path, entry: str):
    writing(project, entry)
    return loader_for(project).load_plugin("fixt").sensors[0]


def writing(project: Path, entry: str, files=None) -> Path:
    write_project_config(project, 'plugins = ["fixt"]')
    write_plugin(
        project,
        "fixt",
        {"config.toml": f"sensors = [{entry}]", **(files or {})},
    )
    return project


def refusal_for(project: Path) -> str:
    with pytest.raises(SystemExit) as failure:
        loader_for(project).load_plugin("fixt")
    return str(failure.value)


def test_an_inline_sensor_loads_with_its_tool_and_args(tmp_path: Path) -> None:
    part = inline_part(tmp_path, PYTHON_TOOL)

    assert part.argv == ["${python}", "${dir}/tool.py"]
    assert part.directory == tmp_path / ".habit-hooks" / "fixt"
    assert part.inline is not None
    assert part.inline.success_exit_codes == (0,)
    assert part.inline.transform is None
    assert part.inline.report is False


def test_the_sensor_name_defaults_to_the_tool(tmp_path: Path) -> None:
    part = inline_part(tmp_path, '{ tool = "golangci-lint", args = ["run"] }')

    assert part.name == "golangci-lint"


def test_a_placeholder_tool_has_to_name_its_sensor(tmp_path: Path) -> None:
    """The name cannot default to a tool spelled as a placeholder — the notice
    that would quote ``sensor '${{python}}'`` names nothing the reader wrote."""
    writing(tmp_path, '{ tool = "${python}", args = ["x"] }')

    assert "name" in refusal_for(tmp_path)


def test_an_inline_sensor_whose_spec_file_also_exists_is_refused(
    tmp_path: Path,
) -> None:
    writing(
        tmp_path,
        '{ name = "both", tool = "${python}" }',
        files={"sensors/both.toml": 'command = "echo []"'},
    )

    assert "also ships sensors/both.toml" in refusal_for(tmp_path)


def test_a_sensor_enabled_twice_is_refused(tmp_path: Path) -> None:
    writing(
        tmp_path, '{ tool = "other", name = "lint" }, { tool = "other2", name = "lint" }'
    )

    assert "enables sensor 'lint' twice" in refusal_for(tmp_path)


def test_a_spec_file_string_listed_twice_still_loads(tmp_path: Path) -> None:
    """Two plain spec-file strings of one name loaded before inline sensors
    existed, duplicating findings — and keep loading exactly as they did."""
    write_project_config(tmp_path, 'plugins = ["fixt"]')
    write_plugin(
        tmp_path,
        "fixt",
        {
            "config.toml": 'sensors = ["lint", "lint"]',
            "sensors/lint.toml": 'argv = ["true"]',
        },
    )

    sensors = loader_for(tmp_path).load_plugin("fixt").sensors

    assert [sensor.name for sensor in sensors] == ["lint", "lint"]


def test_an_unknown_key_in_an_inline_sensor_is_refused(tmp_path: Path) -> None:
    writing(tmp_path, f'{PYTHON_TOOL[:-1]}, colout = "red" }}')

    assert "colout" in refusal_for(tmp_path)


def test_a_missing_transform_program_is_refused(tmp_path: Path) -> None:
    writing(tmp_path, f'{PYTHON_TOOL[:-1]}, transform = "map.jq" }}')

    message = refusal_for(tmp_path)
    assert "map.jq" in message
    assert "transform" in message


def test_success_exit_codes_must_be_numbers(tmp_path: Path) -> None:
    writing(tmp_path, f'{PYTHON_TOOL[:-1]}, success_exit_codes = ["1"] }}')

    assert "success_exit_codes" in refusal_for(tmp_path)


def test_a_report_no_argument_asks_for_is_refused(tmp_path: Path) -> None:
    writing(tmp_path, f'{PYTHON_TOOL[:-1]}, report = true }}')

    message = refusal_for(tmp_path)
    assert "${report}" in message
    assert "report" in message


def test_a_report_argument_without_a_report_is_refused(tmp_path: Path) -> None:
    """Spelling ``${{report}}`` in the args without ``report = true`` would hand
    the tool the placeholder as a literal argument — refused at load instead."""
    writing(
        tmp_path,
        '{ tool = "${python}", name = "lint", '
        'args = ["${dir}/tool.py", "${report}"] }',
    )

    message = refusal_for(tmp_path)
    assert "${report}" in message
    assert "report" in message


def test_project_args_land_where_the_recipe_spells_args(tmp_path: Path) -> None:
    """An inline entry's ``args`` are its recipe — spelled once, for every run
    — so a project's ``[sensors.<name>]`` args override lands in the recipe's
    ``${args}`` slot, exactly as a spec file's ``args`` default receives one,
    rather than replacing the recipe wholesale."""
    write_project_config(
        tmp_path,
        'plugins = ["fixt"]\n[sensors.lint]\nargs = ["--max", "300"]',
    )
    write_plugin(
        tmp_path,
        "fixt",
        {
            "config.toml": (
                'sensors = [{ tool = "${python}", name = "lint", '
                'args = ["${dir}/tool.py", "${args}", "${files}"] }]'
            ),
            "tool.py": 'print("[]")\n',
        },
    )

    part = loader_for(tmp_path).load_plugin("fixt").sensors[0]

    assert part.argv == ["${python}", "${dir}/tool.py", "${args}", "${files}"]
    assert part.args == ["--max", "300"]


def test_an_entry_without_args_keeps_an_empty_override_slot(tmp_path: Path) -> None:
    part = inline_part(tmp_path, PYTHON_TOOL)

    assert part.args == []
