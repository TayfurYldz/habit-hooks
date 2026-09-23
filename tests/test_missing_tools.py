
from __future__ import annotations

from pathlib import Path

import pytest
from executable_stub import write_recording_tool, write_stub, write_wedged_tool
from platform_probe import off_windows

from habit_hooks import missing_tools
from habit_hooks.initialise import plan
from plugin_fixture import write_plugin

JQ = '{ name = "jq", kind = "command", install = "brew install jq" }'
NODE = '{ name = "node", kind = "command", install = "brew install node" }'
TS_MORPH = (
    '{ name = "ts-morph", kind = "node-module", install = "npm i -D ts-morph" }'
)
ESLINT = '{ name = "eslint", kind = "node-module", install = "npm install --save-dev eslint" }'
KNIP = '{ name = "knip", kind = "node-module", install = "npm install --save-dev knip" }'

NODE_LOG = "node.log"


def _needing(project_dir: Path, *entries: str) -> Path:
    (project_dir / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    declared = f"detectors = [{', '.join(entries)}]"
    write_plugin(project_dir, "python", {"config.toml": declared})
    return project_dir


def _missing(project_dir: Path) -> list[str]:
    return [detector.name for detector in plan(project_dir).missing_tools]


def test_a_plugin_that_declares_no_tools_leaves_nothing_in_the_way(
    toolless_project: Path,
) -> None:
    _needing(toolless_project)

    assert plan(toolless_project).missing_tools == ()


def test_a_command_in_the_project_s_python_bin_is_not_missing(
    toolless_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    _needing(toolless_project, JQ)
    write_stub(toolless_project / ".venv" / "bin", "jq")

    assert _missing(toolless_project) == []


def test_a_command_in_the_project_s_node_bin_is_not_missing(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, JQ)
    write_stub(toolless_project / "node_modules" / ".bin", "jq")

    assert _missing(toolless_project) == []


def test_a_command_nowhere_on_the_path_is_missing_with_the_way_to_get_it(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, JQ)

    (jq,) = plan(toolless_project).missing_tools

    assert jq.name == "jq"
    assert jq.install == "brew install jq"


def test_every_missing_command_is_named_in_the_order_its_plugin_declared_them(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, JQ)

    assert _missing(toolless_project) == ["node", "jq"]


def test_a_module_node_resolves_from_the_project_is_not_missing(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, TS_MORPH)
    write_stub(toolless_project / "node_modules" / ".bin", "node")

    assert _missing(toolless_project) == []


def test_a_module_node_cannot_resolve_is_missing(toolless_project: Path) -> None:
    _needing(toolless_project, NODE, TS_MORPH)
    write_stub(toolless_project / "node_modules" / ".bin", "node", exit_code=1)

    assert _missing(toolless_project) == ["ts-morph"]


def test_a_missing_node_answers_for_its_modules_rather_than_them(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, TS_MORPH)

    assert _missing(toolless_project) == ["node"]


def test_a_module_whose_plugin_never_declared_node_is_missing_on_its_own(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, TS_MORPH)

    assert _missing(toolless_project) == ["ts-morph"]


def test_a_node_that_never_answers_is_not_waited_on(
    toolless_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _needing(toolless_project, NODE, TS_MORPH)
    write_wedged_tool(toolless_project / "node_modules" / ".bin", "node")
    monkeypatch.setattr(missing_tools, "NODE_RESOLVE_TIMEOUT_SECONDS", 0.1)

    assert _missing(toolless_project) == ["ts-morph"]


def test_node_is_asked_to_resolve_the_module_from_the_project_itself(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, TS_MORPH)
    bin_dir = toolless_project / "node_modules" / ".bin"
    write_recording_tool(bin_dir, "node", NODE_LOG)

    plan(toolless_project)

    asked, asked_in = (bin_dir / NODE_LOG).read_text(encoding="utf-8").splitlines()
    assert 'require.resolve("ts-morph")' in asked
    assert Path(asked_in).resolve() == toolless_project.resolve()


def test_eslint_and_knip_resolve_as_node_modules_not_commands(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, ESLINT, KNIP)
    write_stub(toolless_project / "node_modules" / ".bin", "node")

    assert _missing(toolless_project) == []


def test_eslint_and_knip_missing_are_named_with_their_npm_install(
    toolless_project: Path,
) -> None:
    _needing(toolless_project, NODE, ESLINT, KNIP)
    write_stub(toolless_project / "node_modules" / ".bin", "node", exit_code=1)

    missing = plan(toolless_project).missing_tools

    assert [(d.name, d.install) for d in missing] == [
        ("eslint", "npm install --save-dev eslint"),
        ("knip", "npm install --save-dev knip"),
    ]
