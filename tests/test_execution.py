
from __future__ import annotations

import shlex
import sys
from pathlib import Path

import pytest
from platform_probe import A_SHELL_TO_RUN_IT_WITH, off_windows

from habit_hooks.cli import ConfigError
from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part


def _execution(tmp_path: Path) -> Execution:
    return Execution(project_dir=tmp_path, scope=Scope(files=[]))


def _shell_text(argv: list[str]) -> str:
    assert argv[:2] == ["bash", "-c"]
    return argv[2]


def test_expand_replaces_python_with_the_running_interpreter(tmp_path: Path) -> None:
    part = Part(
        name="line-count",
        command="${python} ${dir}/line-count.py",
        directory=tmp_path,
        args=[],
    )

    expanded = _shell_text(_execution(tmp_path)._expand(part))

    assert expanded == (
        f"{shlex.quote(sys.executable)} {shlex.quote(str(tmp_path))}/line-count.py"
    )


def test_expand_splices_the_sensor_args_in_quoted(tmp_path: Path) -> None:
    part = Part(
        name="line-count",
        command="count ${args}",
        directory=tmp_path,
        args=["--max", "2 00"],
    )

    expanded = _shell_text(_execution(tmp_path)._expand(part))

    assert expanded == "count --max '2 00'"


def test_args_a_command_has_nowhere_to_put_are_refused_by_name(tmp_path: Path) -> None:
    part = Part(
        name="comment", command="node ${dir}/comment.js", directory=tmp_path, args=["-v"]
    )

    with pytest.raises(ConfigError) as refusal:
        _execution(tmp_path)._expand(part)

    assert str(refusal.value) == (
        "sensor 'comment' cannot take arguments — its command has no '${args}' "
        "to expand ['-v'] into; remove the 'args', clear a plugin's own default "
        "with [sensors.comment] args = [], or override the sensor with a command "
        "that spells '${args}'"
    )


def test_an_emptied_args_override_is_no_argument_at_all(tmp_path: Path) -> None:
    part = Part(name="comment", command="node comment.js", directory=tmp_path, args=[])

    assert _shell_text(_execution(tmp_path)._expand(part)) == "node comment.js"


@A_SHELL_TO_RUN_IT_WITH
def test_a_filename_can_never_execute_a_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    marker = tmp_path / "PWNED"
    part = Part(
        name="probe",
        command="echo ${files} >/dev/null; printf '[]'",
        directory=tmp_path,
        args=[],
    )
    execution = Execution(
        project_dir=tmp_path,
        scope=Scope(files=[f"src/a$(touch {marker}).py"]),
    )

    execution.run_sensor(part)

    assert not marker.exists()


def test_a_filename_containing_a_space_stays_one_argument(tmp_path: Path) -> None:
    part = Part(name="probe", command="${files}", directory=tmp_path, args=[])
    execution = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/my file.py", "src/plain.py"])
    )

    expanded = _shell_text(execution._expand(part))

    assert expanded == "'src/my file.py' src/plain.py"


def test_expand_carries_the_named_config_to_a_transformer(tmp_path: Path) -> None:
    part = Part(name="snooze", command="run ${config}", directory=tmp_path, args=[])
    execution = Execution(
        project_dir=tmp_path,
        scope=Scope(files=[]),
        config_path=tmp_path / "other.toml",
    )

    expanded = _shell_text(execution._expand(part))

    assert shlex.split(expanded) == ["run", "--config", str(tmp_path / "other.toml")]


def test_expand_drops_config_when_the_run_named_none(tmp_path: Path) -> None:
    part = Part(name="snooze", command="run ${config}", directory=tmp_path, args=[])

    expanded = _shell_text(_execution(tmp_path)._expand(part))

    assert shlex.split(expanded) == ["run"]


@A_SHELL_TO_RUN_IT_WITH
def test_a_plugin_directory_containing_a_space_still_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    directory = tmp_path / "my plugin"
    directory.mkdir()
    (directory / "findings.json").write_text(
        '[{"smell": "oversized-file", "issues": [{"key": "src/a.py"}]}]',
        encoding="utf-8",
    )
    part = Part(
        name="probe", command="cat ${dir}/findings.json", directory=directory, args=[]
    )

    findings = Execution(project_dir=tmp_path, scope=Scope(files=[])).run_sensor(part)

    assert findings == [{"smell": "oversized-file", "issues": [{"key": "src/a.py"}]}]
