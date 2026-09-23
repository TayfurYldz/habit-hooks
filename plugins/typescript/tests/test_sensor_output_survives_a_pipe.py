
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from node_tool_stub import install

PIPE_BUFFER_BYTES = 64 * 1024
PLUGIN = Path(__file__).parents[1]
SENSORS = PLUGIN / "src" / "habit_hooks_typescript" / "sensors"

ISSUE_COUNT = 1500


def _source_with_many_comments(tmp_path: Path) -> Path:
    source = tmp_path / "many-comments.ts"
    lines = [
        f"// a non-essential comment number {n}\nconst v{n} = {n};"
        for n in range(ISSUE_COUNT)
    ]
    source.write_text("\n".join(lines), encoding="utf-8")
    return source


def _project_whose_tool_reports_a_lot(tmp_path: Path, tool: str, report: str) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    install(project, tool, report)
    return project


def _many_eslint_messages() -> str:
    messages = [
        {
            "ruleId": "no-var",
            "message": f"unexpected var, use let or const instead ({n})",
            "severity": 2,
            "line": n,
            "column": 1,
        }
        for n in range(1, ISSUE_COUNT + 1)
    ]
    return json.dumps([{"filePath": "/p/src/big.ts", "messages": messages}])


def _many_knip_exports() -> str:
    occurrences = [
        {"name": f"neverUsed{n}", "line": n, "col": 1} for n in range(ISSUE_COUNT)
    ]
    return json.dumps(
        {"files": [], "issues": [{"file": "src/big.ts", "exports": occurrences}]}
    )


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _sole_finding(result: subprocess.CompletedProcess[str], smell: str) -> dict:
    findings = json.loads(result.stdout)
    assert [finding["smell"] for finding in findings] == [smell]
    assert len(result.stdout) > PIPE_BUFFER_BYTES, "fixture no longer crosses the buffer"
    return findings[0]


def test_comment_sensor_emits_complete_json_through_a_pipe(tmp_path: Path) -> None:
    source = _source_with_many_comments(tmp_path)

    result = _run(["node", str(SENSORS / "comment.cjs"), str(source)], PLUGIN)

    assert len(_sole_finding(result, "non-essential-comment")["issues"]) == ISSUE_COUNT


def test_eslint_sensor_emits_complete_json_through_a_pipe(tmp_path: Path) -> None:
    project = _project_whose_tool_reports_a_lot(
        tmp_path, "eslint", _many_eslint_messages()
    )

    result = _run(
        ["node", str(SENSORS / "eslint.cjs"), "--", "src/big.ts"], project
    )

    assert len(_sole_finding(result, "var-declaration")["issues"]) == ISSUE_COUNT


def test_knip_sensor_emits_complete_json_through_a_pipe(tmp_path: Path) -> None:
    project = _project_whose_tool_reports_a_lot(
        tmp_path, "knip", _many_knip_exports()
    )

    result = _run(["node", str(SENSORS / "knip.cjs")], project)

    assert len(_sole_finding(result, "unused-export")["issues"]) == ISSUE_COUNT
