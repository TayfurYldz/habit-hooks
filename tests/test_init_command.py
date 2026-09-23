
from __future__ import annotations

from pathlib import Path

import pytest
from habit_hooks import hooks
from habit_hooks.init_command import run
from plugin_fixture import write_project_config


def _config(project_dir: Path) -> Path:
    return project_dir / ".habit-hooks" / "config.toml"


def test_a_fresh_project_gets_a_config_naming_the_plugins_it_needs(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (init_project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    monkeypatch.chdir(init_project)

    assert run([]) == 0
    assert _config(init_project).read_text(encoding="utf-8") == 'plugins = ["python", "generic"]\n'


def test_a_configured_project_is_left_exactly_as_it_was(
    init_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_project_config(init_project, '# mine\nplugins = ["generic"]\n')
    monkeypatch.chdir(init_project)

    assert run([]) == 0
    assert _config(init_project).read_text(encoding="utf-8") == '# mine\nplugins = ["generic"]\n'


def test_the_pipeline_runs_init_rather_than_piping_it_into_the_mapper(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.chdir(init_project)

    assert hooks.main(["init"]) == 0
    assert "Wrote .habit-hooks/config.toml" in capsys.readouterr().out


def test_the_pipeline_s_help_names_the_command_that_sets_a_project_up(
    capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLUMNS", "100")

    assert hooks.main(["--help"]) == 0
    assert "habit-hooks init" in capsys.readouterr().out


def test_a_rejected_config_fails_the_tool_under_the_pipeline_s_name(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    write_project_config(init_project, "plugns = []\n")
    monkeypatch.chdir(init_project)

    assert hooks.main(["init"]) == 2
    assert capsys.readouterr().err.startswith("habit-hooks: unknown config key")


def test_init_takes_no_arguments_and_says_so(
    init_project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.chdir(init_project)

    with pytest.raises(SystemExit) as failure:
        hooks.main(["init", "--all"])

    assert failure.value.code == 2
    assert "usage: habit-hooks init" in capsys.readouterr().err
