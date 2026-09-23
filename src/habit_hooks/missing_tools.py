
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from attrs import frozen

from .detectors import COMMAND_KIND, NODE_MODULE_KIND, Detector, search_paths_for
from .project_paths import tool_executable

NODE = "node"





NODE_RESOLVE_TIMEOUT_SECONDS = 30.0


@frozen
class _Tools:

    project_dir: Path
    node: str | None
    node_declared: bool

    @classmethod
    def under(cls, project_dir: Path, declared: list[Detector]) -> _Tools:
        return cls(
            project_dir,
            tool_executable(NODE, project_dir, _node_search_paths(declared)),
            any(_is_node(detector) for detector in declared),
        )


def _node_search_paths(declared: list[Detector]) -> tuple[str, ...]:
    return search_paths_for(NODE, [detector for detector in declared if _is_node(detector)])


def _is_node(detector: Detector) -> bool:
    return detector.kind == COMMAND_KIND and detector.name == NODE


def missing_tools(
    declared: list[Detector], project_dir: Path
) -> tuple[Detector, ...]:
    tools = _Tools.under(project_dir, declared)
    return tuple(detector for detector in declared if _is_missing(detector, tools))


def _is_missing(detector: Detector, tools: _Tools) -> bool:
    if detector.kind == NODE_MODULE_KIND:
        return _module_is_missing(detector.name, tools)
    return (
        tool_executable(detector.name, tools.project_dir, detector.search_paths) is None
    )


def _module_is_missing(module: str, tools: _Tools) -> bool:
    if tools.node is None:
        return not tools.node_declared
    return not _node_resolves(tools.node, module, tools.project_dir)


def _node_resolves(node: str, module: str, project_dir: Path) -> bool:
    script = f"require.resolve({json.dumps(module)})"
    try:
        asked = subprocess.run(
            [node, "-e", script],
            cwd=project_dir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            input="",
            timeout=NODE_RESOLVE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return asked.returncode == 0
