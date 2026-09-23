
from __future__ import annotations

import io
from pathlib import Path

import pytest

from habit_hooks import mapper
from habit_hooks.cli import EXIT_TOOL_ERROR
from plugin_fixture import write_project_config

_INCOMPLETE_RUN_FINDING = {
    "smell": "incomplete-run",
    "details": {},
    "issues": [
        {
            "key": "habit-sensors: sensor 'comment' failed: boom",
            "details": {"content": "habit-sensors: sensor 'comment' failed: boom"},
        }
    ],
}


def _main_over_stdin(
    stdin: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> int:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    return mapper.main([])


def test_an_incomplete_run_finding_is_coached_not_rendered_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    code = mapper.run([_INCOMPLETE_RUN_FINDING], tmp_path)

    out = capsys.readouterr().out
    assert "✅" not in out
    assert "── incomplete-run (1 issue) ──" in out
    assert "this run did not complete — a tool broke" in out
    assert "sensor 'comment' failed: boom" in out
    assert code == 1


def test_a_clean_run_still_renders_the_clean_guide(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    code = mapper.run([], tmp_path)

    assert "✅ Habit Hooks: automated checks passed." in capsys.readouterr().out
    assert code == 0


def test_nothing_on_stdin_is_coached_as_an_incomplete_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    code = _main_over_stdin("", tmp_path, monkeypatch)

    out = capsys.readouterr().out
    assert "✅" not in out
    assert "── incomplete-run (1 issue) ──" in out
    assert "this run did not complete — a tool broke" in out
    assert code == EXIT_TOOL_ERROR


def test_whitespace_only_stdin_is_an_incomplete_run_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    code = _main_over_stdin("\n", tmp_path, monkeypatch)

    assert "✅" not in capsys.readouterr().out
    assert code == EXIT_TOOL_ERROR


def test_an_empty_findings_array_on_stdin_is_still_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    code = _main_over_stdin("[]\n", tmp_path, monkeypatch)

    assert "✅ Habit Hooks: automated checks passed." in capsys.readouterr().out
    assert code == 0


def test_an_incomplete_run_cannot_be_disabled_into_a_clean_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_project_config(tmp_path, "[smells.incomplete-run]\ndisabled = true")

    code = _main_over_stdin("", tmp_path, monkeypatch)

    assert "✅" not in capsys.readouterr().out
    assert code == EXIT_TOOL_ERROR
