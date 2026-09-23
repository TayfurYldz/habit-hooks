
from __future__ import annotations

from pathlib import Path

from platform_probe import A_MACHINE_WITH_SIGNALS, A_MACHINE_WITHOUT_SIGNALS
from project_tool_probe import a_project_whose_tool, ask_the_seam, run

PARTIAL_REPORT_BYTES = 100_000

SENSORS = Path(__file__).parents[1] / "src" / "habit_hooks_typescript" / "sensors"

KILLED_MID_REPORT = (
    'const fs = require("node:fs");\n'
    f'fs.writeSync(1, "[".padEnd({PARTIAL_REPORT_BYTES}, "x"));\n'
    'fs.writeSync(2, "  \\n");\n'
    'process.kill(process.pid, "SIGKILL");\n'
)


@A_MACHINE_WITH_SIGNALS
def test_a_tool_killed_mid_report_is_named_along_with_the_signal(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "culled", KILLED_MID_REPORT)

    answer = ask_the_seam(project, "culled")

    assert answer["printed"] == PARTIAL_REPORT_BYTES, "the fixture never flushed"
    assert (answer["status"], answer["signal"]) == (None, "SIGKILL")
    assert answer["broke"] is True
    assert answer["complaint"] == "culled: killed by SIGKILL without a word of its own\n"


@A_MACHINE_WITH_SIGNALS
def test_a_sensor_whose_tool_was_killed_says_so_by_its_signal(tmp_path: Path) -> None:
    project = a_project_whose_tool(tmp_path, "knip", KILLED_MID_REPORT)

    result = run(["node", str(SENSORS / "knip.cjs")], project)

    assert result.returncode != 0
    assert result.stderr == "knip: killed by SIGKILL without a word of its own\n"


@A_MACHINE_WITHOUT_SIGNALS
def test_a_tool_killed_mid_report_looks_exactly_like_a_findings_run(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "culled", KILLED_MID_REPORT)

    answer = ask_the_seam(project, "culled")

    assert answer["printed"] == PARTIAL_REPORT_BYTES, "the fixture never flushed"
    assert (answer["status"], answer["signal"]) == (1, None)
    assert answer["broke"] is False


@A_MACHINE_WITHOUT_SIGNALS
def test_a_sensor_whose_tool_was_killed_still_refuses_its_half_report(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "knip", KILLED_MID_REPORT)

    result = run(["node", str(SENSORS / "knip.cjs")], project)

    assert result.returncode != 0
    assert result.stderr == (
        "knip: exited 1, and what it printed is not a report this sensor can read\n"
    )
