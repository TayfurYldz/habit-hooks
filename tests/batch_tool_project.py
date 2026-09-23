
from __future__ import annotations

from pathlib import Path

import pytest
from bare_machine import project_with_no_tools
from detector_declarations import declaring
from executable_stub import write_batch_stub
from plugin_fixture import one_sensor

from habit_hooks.sensors.model import Part

BATCH_TOOL = '{ name = "probe.cmd", kind = "command", install = "npm i -D probe" }'
PLAIN_TOOL = '{ name = "probe", kind = "command", install = "npm i -D probe" }'


def recipe(*handed: str) -> str:
    tools = "".join(f', "{argument}"' for argument in handed)
    return f'argv = ["${{python}}", "-c", "print(\'[]\')"{tools}, "${{files}}"]'


def batch_sensor(project: Path) -> Part:
    return one_sensor(project, recipe("${detector:probe.cmd}"), declaring(BATCH_TOOL))


def installing_a_batch_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project = project_with_no_tools(tmp_path, monkeypatch)
    write_batch_stub(project / "node_modules" / ".bin", "probe")
    return project
