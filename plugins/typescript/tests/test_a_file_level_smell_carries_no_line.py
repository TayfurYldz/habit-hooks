from __future__ import annotations

import json
import subprocess
from pathlib import Path

from node_tool_stub import install

SENSOR = Path(__file__).parents[1] / "src/habit_hooks_typescript/sensors/eslint.cjs"

ESLINT = "eslint"


def _report(rule: str | None, **extra: object) -> str:
    message = {
        "ruleId": rule,
        "message": "something to fix",
        "severity": 2,
        "line": 201,
        "column": 1,
        **extra,
    }
    return json.dumps([{"filePath": "/p/src/a.ts", "messages": [message]}])


def _details(tmp_path: Path, report: str) -> dict:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    install(project, ESLINT, report)
    result = subprocess.run(
        ["node", str(SENSOR), "--", "src/a.ts"],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(result.stdout)[0]["issues"][0]["details"]


def test_an_oversized_file_names_no_line_and_no_column(tmp_path: Path) -> None:
    details = _details(tmp_path, _report("max-lines"))

    assert details["line"] is None
    assert details["column"] is None


def test_an_oversized_file_still_carries_the_message_eslint_wrote(
    tmp_path: Path,
) -> None:
    details = _details(tmp_path, _report("max-lines"))

    assert details["message"] == "something to fix"
    assert details["source"] == "eslint:max-lines"


def test_a_line_level_smell_keeps_the_position_it_was_given(tmp_path: Path) -> None:
    details = _details(tmp_path, _report("eqeqeq"))

    assert details["line"] == 201
    assert details["column"] == 1


def test_a_parse_error_keeps_where_parsing_failed(tmp_path: Path) -> None:
    details = _details(tmp_path, _report(None, fatal=True))

    assert details["line"] == 201
