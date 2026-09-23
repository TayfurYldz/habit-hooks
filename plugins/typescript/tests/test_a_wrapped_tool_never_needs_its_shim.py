
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import NamedTuple

import pytest
from node_tool_stub import entry_script, install, spawns

SENSORS = Path(__file__).parents[1] / "src" / "habit_hooks_typescript" / "sensors"

BIN_SHIM = "node_modules/.bin"


class WrappedTool(NamedTuple):

    sensor: str
    tool: str
    report: str
    argv: tuple[str, ...]


KNIP = WrappedTool("knip.cjs", "knip", json.dumps({"files": [], "issues": []}), ())
ESLINT = WrappedTool("eslint.cjs", "eslint", json.dumps([]), ("--", "src/a.ts"))

wrapped_tool = pytest.mark.parametrize(
    "wrapped", [KNIP, ESLINT], ids=[KNIP.tool, ESLINT.tool]
)


def _spawned(tmp_path: Path, wrapped: WrappedTool) -> tuple[Path, list[list[str]]]:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    install(project, wrapped.tool, wrapped.report)
    subprocess.run(
        ["node", str(SENSORS / wrapped.sensor), *wrapped.argv],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    spawns_of = spawns(project, wrapped.tool)
    assert spawns_of, "the sensor spawned nothing"
    return project, spawns_of


@wrapped_tool
def test_the_tool_is_spawned_as_the_script_its_package_names(
    wrapped: WrappedTool, tmp_path: Path
) -> None:
    project, spawned = _spawned(tmp_path, wrapped)

    named = str(entry_script(project, wrapped.tool))
    assert [run[1] for run in spawned] == [named] * len(spawned)


@wrapped_tool
def test_nothing_from_the_bin_directory_is_spawned(
    wrapped: WrappedTool, tmp_path: Path
) -> None:
    _, spawned = _spawned(tmp_path, wrapped)

    assert [word for run in spawned for word in run if BIN_SHIM in word] == []


@wrapped_tool
def test_the_interpreter_is_named_by_its_own_file(
    wrapped: WrappedTool, tmp_path: Path
) -> None:
    _, spawned = _spawned(tmp_path, wrapped)

    assert [run[0] for run in spawned if not Path(run[0]).is_file()] == []
