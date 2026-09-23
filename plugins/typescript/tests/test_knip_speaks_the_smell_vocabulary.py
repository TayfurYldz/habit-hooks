from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from node_tool_stub import install

SENSOR = (
    Path(__file__).parents[1]
    / "src"
    / "habit_hooks_typescript"
    / "sensors"
    / "knip.cjs"
)


def _findings(tmp_path: Path, report: dict) -> list[dict]:
    install(tmp_path, "knip", json.dumps(report))
    result = subprocess.run(
        ["node", str(SENSOR)],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return json.loads(result.stdout)


def _report(**keys: object) -> dict:
    return {"files": [], "issues": [{"file": "src/helper.ts", "owners": [], **keys}]}


def _occurrence(name: str) -> list[dict]:
    return [{"name": name, "line": 3, "col": 1}]


UNTRANSLATED_KEYS = ["binaries", "duplicates", "catalog", "unlisted", "unresolved"]

TRANSLATED_KEYS = [
    ("exports", "unused-export"),
    ("types", "unused-export"),
    ("nsExports", "unused-export"),
    ("nsTypes", "unused-export"),
    ("dependencies", "unused-dependency"),
]


@pytest.mark.parametrize("knip_key", UNTRANSLATED_KEYS)
def test_a_key_outside_the_vocabulary_never_reaches_the_pipe(
    knip_key: str, tmp_path: Path
) -> None:
    findings = _findings(tmp_path, _report(**{knip_key: _occurrence("thing")}))

    assert findings == []


@pytest.mark.parametrize(("knip_key", "smell"), TRANSLATED_KEYS)
def test_a_translated_key_arrives_as_its_smell(
    knip_key: str, smell: str, tmp_path: Path
) -> None:
    findings = _findings(tmp_path, _report(**{knip_key: _occurrence("neverUsed")}))

    assert [f["smell"] for f in findings] == [smell]
    assert findings[0]["issues"][0]["details"]["source"] == f"knip:{knip_key}"


def test_an_unused_enum_member_arrives_as_unused_class_member(tmp_path: Path) -> None:
    report = _report(enumMembers={"Colour": _occurrence("Green")})

    findings = _findings(tmp_path, report)

    assert [f["smell"] for f in findings] == ["unused-class-member"]
    issue = findings[0]["issues"][0]
    assert issue["key"] == "Green"
    assert issue["details"]["name"] == "Green"
    assert issue["details"]["content"] == "Green"


def test_dropping_an_untranslated_key_leaves_its_neighbours_alone(
    tmp_path: Path,
) -> None:
    report = _report(binaries=_occurrence("habit-hooks"))
    report["files"] = ["src/orphan.ts"]

    findings = _findings(tmp_path, report)

    assert [f["smell"] for f in findings] == ["unused-file"]
    assert findings[0]["issues"][0]["key"] == "src/orphan.ts"


def test_a_column_is_reported_under_the_name_the_contract_gives_it(
    tmp_path: Path,
) -> None:
    findings = _findings(
        tmp_path,
        {
            "files": [],
            "issues": [
                {
                    "file": "src/a.ts",
                    "exports": [{"name": "unused", "line": 3, "col": 14}],
                }
            ],
        },
    )

    (issue,) = findings[0]["issues"]
    assert issue["details"]["line"] == 3
    assert issue["details"]["column"] == 14
    assert "col" not in issue["details"]
