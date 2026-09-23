
from __future__ import annotations

from pathlib import Path

from plugin_fixture import loader_for, write_plugin, write_project_config

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution

RECIPE_WITH_A_SLOT = (
    'sensors = [{ tool = "${python}", name = "lint", '
    'args = ["${dir}/tool.py", "${args}", "${files}"] }]'
)
ECHOES_ITS_ARGUMENTS = (
    "import json, sys\n"
    "print(json.dumps([{'smell': 'made-up-smell', 'details': {}, "
    "'issues': [{'key': a, 'details': {}}]} for a in sys.argv[1:]]))\n"
)


def test_project_args_reach_the_tool_where_the_recipe_spells_args(
    tmp_path: Path,
) -> None:
    write_project_config(
        tmp_path,
        'plugins = ["fixt"]\n[sensors.lint]\nargs = ["--max", "7"]',
    )
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": RECIPE_WITH_A_SLOT, "tool.py": ECHOES_ITS_ARGUMENTS},
    )
    sensor = loader_for(tmp_path).load_plugin("fixt").sensors[0]

    run = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/a.py"])
    ).run_sensors([sensor])

    assert [issue["key"] for f in run.findings for issue in f["issues"]] == [
        "--max",
        "7",
        "src/a.py",
    ]
    assert run.notices == []


def test_no_override_leaves_the_slot_empty(tmp_path: Path) -> None:
    write_project_config(tmp_path, 'plugins = ["fixt"]')
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": RECIPE_WITH_A_SLOT, "tool.py": ECHOES_ITS_ARGUMENTS},
    )
    sensor = loader_for(tmp_path).load_plugin("fixt").sensors[0]

    run = Execution(
        project_dir=tmp_path, scope=Scope(files=["src/a.py"])
    ).run_sensors([sensor])

    assert [issue["key"] for f in run.findings for issue in f["issues"]] == [
        "src/a.py"
    ]
    assert run.notices == []
