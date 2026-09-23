
from __future__ import annotations

from pathlib import Path

import pytest
from habit_hooks.init_command import run
from init_install_fixture import FAILING, FIRST, PYTHON, SECOND, answering, needing, ran


def test_a_setup_with_nothing_missing_asks_nothing(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    assert run([]) == 0
    assert "[y/N]" not in capsys.readouterr().out


def test_nobody_is_prompted_where_nobody_is_there_to_answer(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)

    assert run([]) == 0
    assert "[y/N]" not in capsys.readouterr().out
    assert ran(init_project) == []


def test_the_commands_are_printed_even_where_they_cannot_be_offered(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)

    run([])

    assert f"{PYTHON} mark.py one" in capsys.readouterr().out


def test_one_prompt_covers_the_whole_list(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    needing(init_project, FIRST, SECOND)
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    run([])

    assert capsys.readouterr().out.count("[y/N]") == 1


def test_agreeing_runs_every_command_in_the_order_they_were_listed(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    needing(init_project, FIRST, SECOND)
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    assert run([]) == 0
    assert ran(init_project) == ["one", "two"]


def test_pressing_enter_installs_nothing(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)
    answering("\n", monkeypatch)

    assert run([]) == 0
    assert ran(init_project) == []


def test_declining_installs_nothing(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)
    answering("n\n", monkeypatch)

    run([])

    assert ran(init_project) == []


def test_a_closed_answer_is_no(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    needing(init_project, FIRST)
    monkeypatch.chdir(init_project)
    answering("", monkeypatch)

    assert run([]) == 0
    assert ran(init_project) == []


def test_a_command_that_fails_does_not_take_the_rest_with_it(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    needing(init_project, FAILING, SECOND)
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    run([])

    assert ran(init_project) == ["two"]


def test_a_command_that_fails_is_named_as_still_to_do(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    needing(init_project, FAILING, SECOND)
    monkeypatch.chdir(init_project)
    answering("y\n", monkeypatch)

    run([])

    reported = capsys.readouterr().out
    assert "These did not succeed, and are still to do:" in reported
    assert reported.rstrip().endswith(f"  {PYTHON} fail.py")
