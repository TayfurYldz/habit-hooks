
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from executable_stub import write_recording_tool, write_stub
from plugin_fixture import loader_for, write_plugin, write_project_config

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution


def test_glob_metacharacters_in_a_filename_are_escaped_for_the_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_recording_tool(project / "bin", "lint", "phase1-args.log")
    write_plugin(
        project,
        "fixt",
        {
            "config.toml": (
                "sensors = [{ tool = \"lint\", args = [\"${files}\"] }]\n"
                "detectors = [{ name = \"lint\", kind = \"command\", "
                'install = "echo lint", search_paths = ["bin"] }]'
            ),
        },
    )
    write_project_config(project, 'plugins = ["fixt"]')
    sensor = loader_for(project).load_plugin("fixt").sensors[0]

    Execution(
        project_dir=project,
        scope=Scope(files=["src/plain.py", "src/a*b[1].py"]),
    ).run_sensors([sensor])

    recorded = (project / "bin" / "phase1-args.log").read_text(encoding="utf-8")
    assert "src/plain.py" in recorded
    assert "src/a\\*b\\[1\\].py" in recorded


def test_a_bare_tool_name_runs_the_file_its_detector_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_stub(project / "bin", "lint")
    write_plugin(
        project,
        "fixt",
        {
            "config.toml": (
                'sensors = [{ tool = "lint", args = ["--json"] }]\n'
                "detectors = [{ name = \"lint\", kind = \"command\", "
                'install = "echo lint", search_paths = ["bin"] }]'
            ),
        },
    )
    write_project_config(project, 'plugins = ["fixt"]')

    sensor = loader_for(project).load_plugin("fixt").sensors[0]

    argv = Execution(project_dir=project, scope=Scope(files=[]))._expand(sensor)
    assert Path(argv[0]).parent == project / "bin"
    assert argv[1:] == ["--json"]
