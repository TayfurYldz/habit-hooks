"""The report file an inline sensor's tool is handed, and reading it back.

``report = true`` buys a tool that answers in a report rather than stdout: the
framework hands it a fresh file through ``${report}`` and reads back what it
wrote. Nothing at all is a run that never delivered: a tool that answers in a
report writes one even when it finds nothing, so a missing report is a failed
run, never a clean one (the #139 class, where a report-writing tool that wrote
nothing read as clean).
"""

from __future__ import annotations

import json
from pathlib import Path

from test_inline_sensor_run import FINDING, GROUPING, MADE_UP, inline_run


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


def test_a_tool_that_writes_no_report_fails_the_run(tmp_path: Path) -> None:
    entry, files = report_entry(
        "print('scanned, honestly')\n", ', success_exit_codes = [0, 1], report = true'
    )

    run = inline_run(tmp_path, entry, files)

    assert run.findings == []
    assert "wrote no report" in run.notices[0]
