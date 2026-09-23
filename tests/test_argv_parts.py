
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from habit_hooks.cli import ConfigError
from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def _argv(part: Part, files: list[str]) -> list[str]:
    execution = Execution(project_dir=part.directory, scope=Scope(files=list(files)))
    return execution._expand(part)


def test_an_argv_part_is_spawned_with_no_shell_around_it(tmp_path: Path) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["ruff", "check", "--quiet"])

    assert _argv(part, []) == ["ruff", "check", "--quiet"]


def test_no_files_expand_to_no_arguments_at_all(tmp_path: Path) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["ruff", "${files}"])

    assert _argv(part, []) == ["ruff"]

def test_many_files_expand_where_the_placeholder_stands(tmp_path: Path) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["ruff", "${files}", "--json"])

    assert _argv(part, ["src/a.php"]) == ["ruff", "src/a.php", "--json"]
    assert _argv(part, ["src/a.py", "src/b.py"]) == [
        "ruff",
        "src/a.py",
        "src/b.py",
        "--json",
    ]


def test_the_sensor_args_expand_in_place_too(tmp_path: Path) -> None:
    part = Part(
        name="line-count",
        directory=tmp_path,
        argv=["count", "${args}", "${files}"],
        args=["--max", "2 00"],
    )

    assert _argv(part, ["src/a.py"]) == ["count", "--max", "2 00", "src/a.py"]


def test_an_emptied_args_override_expands_to_nothing(tmp_path: Path) -> None:
    part = Part(name="line-count", directory=tmp_path, argv=["count", "${args}"])

    assert _argv(part, []) == ["count"]


def test_the_named_config_expands_to_both_of_its_arguments(tmp_path: Path) -> None:
    part = Part(name="snooze", directory=tmp_path, argv=["run", "${config}"])
    execution = Execution(
        project_dir=tmp_path, scope=Scope(files=[]), config_path=tmp_path / "other.toml"
    )

    assert execution._expand(part) == ["run", "--config", str(tmp_path / "other.toml")]


def test_no_named_config_expands_to_nothing(tmp_path: Path) -> None:
    part = Part(name="snooze", directory=tmp_path, argv=["run", "${config}"])

    assert _argv(part, []) == ["run"]


def test_a_string_placeholder_fills_in_inside_its_own_element(tmp_path: Path) -> None:
    directory = tmp_path / "my plugin"
    part = Part(
        name="line-count", directory=directory, argv=["${python}", "${dir}/count.py"]
    )

    assert _argv(part, []) == [sys.executable, f"{directory}/count.py"]


def test_a_filename_that_is_shell_syntax_reaches_the_tool_intact(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "PWNED"
    name = f"src/it's \"a $(touch {marker}) file\".py"
    (tmp_path / "echo_argv.py").write_text(
        "import sys, json\n"
        'print(json.dumps([{"smell": "s",'
        ' "issues": [{"key": name} for name in sys.argv[1:]]}]))\n',
        encoding="utf-8",
    )
    part = Part(
        name="probe",
        directory=tmp_path,
        argv=["${python}", "${dir}/echo_argv.py", "${files}"],
    )
    execution = Execution(project_dir=tmp_path, scope=Scope(files=[name]))

    findings = execution.run_sensor(part)

    assert findings[0]["issues"] == [{"key": name}]
    assert not marker.exists()


def test_a_list_placeholder_buried_in_a_larger_element_is_refused(
    tmp_path: Path,
) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["ruff", "--paths=${files}"])

    with pytest.raises(ConfigError) as refusal:
        _argv(part, ["src/a.py"])

    assert str(refusal.value) == (
        "'probe' cannot expand ${files} inside '--paths=${files}' — it stands "
        "for a whole list of arguments, so it has to be an argv element of its "
        "own; split it into two elements, or use a 'command' string, where a "
        "shell does the splitting"
    )


def test_args_an_argv_has_nowhere_to_put_are_refused_by_name(tmp_path: Path) -> None:
    part = Part(
        name="comment", directory=tmp_path, argv=["node", "comment.js"], args=["-v"]
    )

    with pytest.raises(ConfigError) as refusal:
        _argv(part, [])

    assert "cannot take arguments" in str(refusal.value)
