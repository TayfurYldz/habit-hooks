
from __future__ import annotations

from habit_hooks.merged_findings import merged

ONE_GUIDE = "guides/the-one.md"


def _same_guide(finding: dict) -> str:
    return ONE_GUIDE


def _finding(smell: str, issues: list[dict], **rest: object) -> dict:
    return {"smell": smell, "details": {}, "issues": issues, **rest}


def _at(file: str, **details: object) -> dict:
    return {"key": file, "details": {"file": file, **details}}


def test_two_sensors_naming_one_place_leave_one_issue() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py", source="eslint:max-lines")]),
        _finding("oversized-file", [_at("src/a.py", lines=260, source="line-count")]),
    ]

    assert merged(findings, _same_guide)[0]["issues"] == [
        _at("src/a.py", source="eslint:max-lines")
    ]


def test_a_line_nobody_stated_is_absent_rather_than_a_value() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py", line=None, column=None)]),
        _finding("oversized-file", [_at("src/a.py")]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 1


def test_one_key_found_in_two_files_is_two_issues() -> None:
    findings = [
        _finding("unused-export", [{"key": "default", "details": {"file": "src/a.ts"}}]),
        _finding("unused-export", [{"key": "default", "details": {"file": "src/b.ts"}}]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 2


def test_two_clones_starting_in_different_places_are_two_duplications() -> None:
    findings = [
        _finding("duplicated-code", [_at("src/a.py", startLine=10, endLine=30)]),
        _finding("duplicated-code", [_at("src/a.py", startLine=100, endLine=30)]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 2


def test_two_clones_of_different_lengths_are_two_duplications() -> None:
    findings = [
        _finding("duplicated-code", [_at("src/a.py", startLine=10, endLine=30)]),
        _finding("duplicated-code", [_at("src/a.py", startLine=10, endLine=90)]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 2


def test_two_findings_on_one_line_at_different_columns_are_two_issues() -> None:
    findings = [
        _finding("explicit-any", [_at("src/a.ts", line=5, column=11)]),
        _finding("explicit-any", [_at("src/a.ts", line=5, column=30)]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 2


def test_an_issue_that_states_no_details_at_all_still_reports() -> None:
    findings = [
        _finding("unused-dependency", [{"key": "requests"}]),
        _finding("unused-dependency", [{"key": "urllib3"}]),
    ]

    assert [issue["key"] for issue in merged(findings, _same_guide)[0]["issues"]] == [
        "requests",
        "urllib3",
    ]


def test_two_places_in_one_file_are_two_issues() -> None:
    findings = [
        _finding("high-complexity", [_at("src/a.py", line=12)]),
        _finding("high-complexity", [_at("src/a.py", line=88)]),
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 2


def test_a_third_finding_is_weighed_against_the_second_as_well_as_the_first() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py", source="eslint:max-lines")]),
        _finding("oversized-file", [_at("src/b.py", source="line-count")]),
        _finding("oversized-file", [_at("src/b.py", source="ours")]),
    ]

    issues = merged(findings, _same_guide)[0]["issues"]

    assert [issue["key"] for issue in issues] == ["src/a.py", "src/b.py"]
