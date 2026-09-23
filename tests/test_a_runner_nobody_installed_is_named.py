
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks import mapper
from habit_hooks.cli import ToolError
from plugin_fixture import write_plugin, write_project_config

_FINDING = {
    "smell": "oversized-file",
    "details": {},
    "issues": [{"key": "src/a.py", "details": {"file": "src/a.py"}}],
}


def _project_routing_to(tmp_path: Path, runner: str) -> Path:
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": "", "guides/oversized-file.sh": "echo fixed\n"},
    )
    write_project_config(
        tmp_path, f'plugins = ["fixt"]\n[runners]\nsh = "{runner}"'
    )
    return tmp_path


def test_a_runner_that_is_not_installed_is_named_with_what_to_do(
    tmp_path: Path,
) -> None:
    project = _project_routing_to(tmp_path, "a-runner-nobody-installed")

    with pytest.raises(ToolError) as refusal:
        mapper.run([_FINDING], project)

    said = str(refusal.value)
    assert "a-runner-nobody-installed" in said
    assert "oversized-file.sh" in said
    assert "Traceback" not in said


def test_a_runner_that_is_installed_still_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _project_routing_to(tmp_path, "sh")

    mapper.run([_FINDING], project)

    assert "fixed" in capsys.readouterr().out
