from __future__ import annotations

from pathlib import Path

from project_tool_probe import a_project_whose_tool, run

SENSORS = Path(__file__).parents[1] / "src" / "habit_hooks_typescript" / "sensors"

FAILS_WITHOUT_A_WORD = "process.exit(2);\n"

UNREADABLE = (
    "{tool}: exited 1, and what it printed is not a report this sensor can read\n"
)

SUCCEEDS_WITHOUT_A_WORD = "process.exit(0);\n"

PRINTS_HALF_A_REPORT = (
    'const fs = require("node:fs");\n'
    'fs.writeSync(1, \'[{"filePath":"/p/src/a.ts","messa\');\n'
    "process.exit(1);\n"
)


def test_the_eslint_sensor_says_which_tool_failed(tmp_path: Path) -> None:
    project = a_project_whose_tool(tmp_path, "eslint", FAILS_WITHOUT_A_WORD)

    result = run(["node", str(SENSORS / "eslint.cjs"), "--", "src/a.ts"], project)

    assert result.returncode != 0
    assert result.stderr == "eslint: exited 2 without a word of its own\n"


def test_the_knip_sensor_says_which_tool_failed(tmp_path: Path) -> None:
    project = a_project_whose_tool(tmp_path, "knip", FAILS_WITHOUT_A_WORD)

    result = run(["node", str(SENSORS / "knip.cjs")], project)

    assert result.returncode != 0
    assert result.stderr == "knip: exited 2 without a word of its own\n"


def test_a_knip_that_reported_nothing_at_all_is_a_diagnosis_not_a_traceback(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "knip", SUCCEEDS_WITHOUT_A_WORD)

    result = run(["node", str(SENSORS / "knip.cjs")], project)

    assert result.returncode != 0
    assert result.stderr == "knip: exited 0 without a word of its own\n"


def test_an_eslint_that_reported_nothing_at_all_is_a_diagnosis_not_a_traceback(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "eslint", SUCCEEDS_WITHOUT_A_WORD)

    result = run(["node", str(SENSORS / "eslint.cjs"), "--", "src/a.ts"], project)

    assert result.returncode != 0
    assert result.stderr == "eslint: exited 0 without a word of its own\n"


def test_a_knip_whose_report_was_cut_short_is_a_diagnosis_not_a_traceback(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "knip", PRINTS_HALF_A_REPORT)

    result = run(["node", str(SENSORS / "knip.cjs")], project)

    assert result.returncode != 0
    assert result.stderr == UNREADABLE.format(tool="knip")


def test_an_eslint_whose_report_was_cut_short_is_a_diagnosis_not_a_traceback(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "eslint", PRINTS_HALF_A_REPORT)

    result = run(["node", str(SENSORS / "eslint.cjs"), "--", "src/a.ts"], project)

    assert result.returncode != 0
    assert result.stderr == UNREADABLE.format(tool="eslint")
