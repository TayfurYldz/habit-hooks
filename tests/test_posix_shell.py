
from __future__ import annotations

from pathlib import Path

import pytest
from platform_probe import A_SHELL_TO_RUN_IT_WITH, off_windows, on_windows

from habit_hooks.scope import Scope
from habit_hooks.sensors import posix_shell
from habit_hooks.sensors.execution import Execution
from habit_hooks.sensors.model import Part, SensorError


def _shell_sensor(tmp_path: Path, command: str) -> Part:
    return Part(name="probe", directory=tmp_path, command=command)


def _argv_sensor(tmp_path: Path) -> Part:
    (tmp_path / "probe.py").write_text(
        'print(\'[{"smell": "long-file", "issues": [{"key": "src/a.py"}]}]\')\n',
        encoding="utf-8",
    )
    return Part(
        name="argv-probe", directory=tmp_path, argv=["${python}", "${dir}/probe.py"]
    )


def _execution(tmp_path: Path) -> Execution:
    return Execution(project_dir=tmp_path, scope=Scope(files=["src/a.py"]))


def test_a_sensor_that_wanted_a_shell_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)

    with pytest.raises(SensorError) as refusal:
        posix_shell.refuse_where_there_is_none(
            "sensor", _shell_sensor(tmp_path, "ruff check | jq .")
        )

    assert str(refusal.value) == (
        "sensor 'probe' cannot run on Windows: its recipe is a shell command "
        "line, and there is no POSIX shell here to read it — disable the sensor "
        "with [sensors.probe] disabled = true"
    )


def test_a_transformer_is_refused_with_advice_that_is_true_for_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)
    transformer = Part(name="snooze", directory=tmp_path, command="jq .")

    with pytest.raises(SensorError) as refusal:
        posix_shell.refuse_where_there_is_none("transformer", transformer)

    assert "drop 'snooze' from the root transformers list" in str(refusal.value)
    assert "[sensors." not in str(refusal.value)


def test_a_part_spelled_as_an_argv_is_never_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)
    part = _argv_sensor(tmp_path)

    assert posix_shell.refuse_where_there_is_none("sensor", part) is None


def test_a_shell_recipe_is_not_refused_where_a_shell_reads_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    off_windows(monkeypatch)

    part = _shell_sensor(tmp_path, "ruff check | jq .")

    assert posix_shell.refuse_where_there_is_none("sensor", part) is None


def test_a_shell_sensor_on_windows_fails_the_run_instead_of_spawning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)
    marker = tmp_path / "it-ran"
    part = _shell_sensor(tmp_path, f"touch {marker}; printf '[]'")

    run = _execution(tmp_path).run_sensors([part])

    assert not marker.exists()
    assert run.findings == []
    assert run.failed
    assert "no POSIX shell" in "\n".join(run.notices)


def test_a_refused_sensor_costs_the_run_only_its_own_findings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)
    parts = [_shell_sensor(tmp_path, "printf '[]'"), _argv_sensor(tmp_path)]

    run = _execution(tmp_path).run_sensors(parts)

    assert run.findings == [{"smell": "long-file", "issues": [{"key": "src/a.py"}]}]
    assert run.failed
    assert len(run.notices) == 1


def test_a_refused_transformer_leaves_the_findings_it_was_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    on_windows(monkeypatch)
    transformer = Part(name="snooze", directory=tmp_path, command="jq .")
    findings = [{"smell": "long-file", "issues": [{"key": "src/a.py"}]}]

    kept, notices = _execution(tmp_path).apply_transformers([transformer], findings)

    assert kept == findings
    assert len(notices) == 1
    assert "no POSIX shell" in notices[0]


@A_SHELL_TO_RUN_IT_WITH
def test_the_same_sensor_runs_where_there_is_a_shell(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    off_windows(monkeypatch)
    marker = tmp_path / "it-ran"
    part = _shell_sensor(tmp_path, f"touch {marker}; printf '[]'")

    run = _execution(tmp_path).run_sensors([part])

    assert marker.exists()
    assert run.findings == []
    assert not run.failed
