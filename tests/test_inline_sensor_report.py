"""The report path an inline sensor's tool is handed, and reading it back.

``report = true`` buys a tool that answers in a report rather than stdout: the
framework hands it a fresh path through ``${report}`` and reads back the one
report it left. Tools split into two families over what a handed-over path is
for — some write a file at it (pmd's ``--report``), some make it a directory
and put a named report inside it (jscpd's ``--output``) — so the path is handed
over empty and both find nothing in their way. Nothing at all is a run that
never delivered: a tool that answers in a report writes one even when it finds
nothing, so a missing report is a failed run, never a clean one (the #139
class, where a jscpd that wrote nothing read as clean).
"""

from __future__ import annotations

import json
from pathlib import Path

from plugin_fixture import loader_for, write_plugin, write_project_config

from habit_hooks.scope import Scope
from habit_hooks.sensors.execution import Execution

MADE_UP = {"violations": [
    {"where": "src/a.py", "rule": "MAGIC-1", "note": "too magic"},
    {"where": "src/b.py", "rule": "MAGIC-1", "note": "also magic"},
]}
GROUPING = (
    '.violations | group_by(.rule) | map({smell: "made-up-smell", details: {}, '
    'issues: map({key: .where, details: {file: .where, message: .note}})})'
)
FINDING = {
    "smell": "made-up-smell",
    "details": {},
    "issues": [
        {"key": "src/a.py", "details": {"file": "src/a.py", "message": "too magic"}},
        {"key": "src/b.py", "details": {"file": "src/b.py", "message": "also magic"}},
    ],
}


def inline_run(project: Path, entry: str, files: dict[str, str]):
    write_project_config(project, 'plugins = ["fixt"]')
    write_plugin(project, "fixt", {"config.toml": f"sensors = [{entry}]", **files})
    sensor = loader_for(project).load_plugin("fixt").sensors[0]
    return Execution(
        project_dir=project, scope=Scope(files=["src/a.py"])
    ).run_sensors([sensor])


def report_entry(body: str, extra: str) -> tuple[str, dict[str, str]]:
    """The entry TOML and plugin files for a fake tool running ``body``."""
    return (
        '{ tool = "${python}", name = "lint", '
        'args = ["${dir}/tool.py", "${report}"]'
        f"{extra} }}",
        {"tool.py": body},
    )


def test_a_report_file_is_handed_to_the_tool_and_read_back(tmp_path: Path) -> None:
    body = (
        "import json, pathlib, sys\n"
        f"pathlib.Path(sys.argv[1]).write_text({json.dumps(MADE_UP)!r})\n"
    )
    entry, files = report_entry(body, ', transform = "map.jq", report = true')

    run = inline_run(tmp_path, entry, {**files, "map.jq": GROUPING})

    assert run.findings == [FINDING]
    assert run.notices == []


def test_a_report_directory_is_read_as_the_one_file_inside_it(
    tmp_path: Path,
) -> None:
    body = (
        "import json, pathlib, sys\n"
        "report = pathlib.Path(sys.argv[1])\n"
        "report.mkdir()\n"
        f"(report / 'jscpd-report.json').write_text({json.dumps(MADE_UP)!r})\n"
    )
    entry, files = report_entry(body, ', transform = "map.jq", report = true')

    run = inline_run(tmp_path, entry, {**files, "map.jq": GROUPING})

    assert run.findings == [FINDING]
    assert run.notices == []


def test_a_tool_that_writes_no_report_fails_the_run(tmp_path: Path) -> None:
    entry, files = report_entry(
        "print('scanned, honestly')\n", ', success_exit_codes = [0, 1], report = true'
    )

    run = inline_run(tmp_path, entry, files)

    assert run.findings == []
    assert "wrote no report" in run.notices[0]


def test_a_report_directory_of_several_files_fails_the_run(tmp_path: Path) -> None:
    body = (
        "import pathlib, sys\n"
        "report = pathlib.Path(sys.argv[1])\n"
        "report.mkdir()\n"
        "(report / 'one.json').write_text('[]')\n"
        "(report / 'two.json').write_text('[]')\n"
    )
    entry, files = report_entry(body, ", report = true")

    run = inline_run(tmp_path, entry, files)

    assert run.findings == []
    assert "2 files in its report directory" in run.notices[0]
