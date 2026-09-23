from __future__ import annotations

import json
import subprocess
from pathlib import Path

from node_tool_stub import install

SENSOR = (
    Path(__file__).parents[1]
    / "src/habit_hooks_typescript/sensors/eslint.cjs"
)

ESLINT = "eslint"


def _message(rule: str | None, line: int | None = 3, **extra: object) -> dict:
    message = {"ruleId": rule, "message": "something to fix", "severity": 2, **extra}
    if line is not None:
        message |= {"line": line, "column": 1}
    return message


def _report(*files: tuple[str, list[dict]]) -> str:
    return json.dumps(
        [{"filePath": path, "messages": messages} for path, messages in files]
    )


def _findings(tmp_path: Path, report: str) -> list[dict]:
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
    return json.loads(result.stdout)


def test_a_rule_named_after_a_javascript_builtin_is_still_just_a_rule(
    tmp_path: Path,
) -> None:
    report = _report(("/p/src/a.ts", [_message("constructor")]))

    findings = _findings(tmp_path, report)

    assert [finding["smell"] for finding in findings] == ["constructor"]


def test_a_message_with_no_position_reports_the_absence_rather_than_hiding_it(
    tmp_path: Path,
) -> None:
    report = _report(("/p/src/a.ts", [_message("eqeqeq", line=None)]))

    findings = _findings(tmp_path, report)

    details = findings[0]["issues"][0]["details"]
    assert details["line"] is None
    assert details["column"] is None


def test_findings_arrive_in_smell_order(tmp_path: Path) -> None:
    report = _report(
        ("/p/src/a.ts", [_message("no-var"), _message("eqeqeq")]),
        ("/p/src/b.ts", [_message("max-params")]),
    )

    findings = _findings(tmp_path, report)

    assert [finding["smell"] for finding in findings] == [
        "loose-equality",
        "too-many-parameters",
        "var-declaration",
    ]


def test_one_smell_gathers_every_file_that_shows_it(tmp_path: Path) -> None:
    report = _report(
        ("/p/src/a.ts", [_message("no-var", line=1), _message("no-var", line=9)]),
        ("/p/src/b.ts", [_message("no-var", line=4)]),
    )

    findings = _findings(tmp_path, report)

    assert len(findings) == 1
    assert [issue["key"] for issue in findings[0]["issues"]] == [
        "/p/src/a.ts",
        "/p/src/a.ts",
        "/p/src/b.ts",
    ]
    assert [issue["details"]["line"] for issue in findings[0]["issues"]] == [1, 9, 4]


def test_a_message_about_a_file_rather_than_a_rule_is_not_a_smell(
    tmp_path: Path,
) -> None:
    report = _report(
        ("/p/src/a.ts", [_message(None), _message("eqeqeq")]),
    )

    findings = _findings(tmp_path, report)

    assert [finding["smell"] for finding in findings] == ["loose-equality"]


def test_a_fatal_message_is_the_parse_error_it_has_no_rule_for(tmp_path: Path) -> None:
    report = _report(("/p/src/a.ts", [_message(None, fatal=True)]))

    findings = _findings(tmp_path, report)

    assert [finding["smell"] for finding in findings] == ["parse-error"]
    assert findings[0]["issues"][0]["details"]["source"] == "eslint:fatal"
