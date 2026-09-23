
from __future__ import annotations

from habit_hooks.merged_findings import merged

ONE_GUIDE = "guides/the-one.md"


def _same_guide(finding: dict) -> str:
    return ONE_GUIDE


def _kept_issues(smell: str, issues: list[dict]) -> list[dict]:
    finding = {"smell": smell, "details": {}, "issues": issues}
    return merged([finding], _same_guide)[0]["issues"]


def test_two_java_variables_declared_on_one_line_are_two_issues() -> None:
    issues = [
        {
            "key": "src/Order.java",
            "details": {
                "file": "src/Order.java",
                "line": 12,
                "message": "Avoid unused local variables such as 'a'.",
                "source": "pmd:UnusedLocalVariable",
            },
        },
        {
            "key": "src/Order.java",
            "details": {
                "file": "src/Order.java",
                "line": 12,
                "message": "Avoid unused local variables such as 'b'.",
                "source": "pmd:UnusedLocalVariable",
            },
        },
    ]

    assert len(_kept_issues("unused-variable", issues)) == 2


def test_two_php_variables_assigned_on_one_line_are_two_issues() -> None:
    issues = [
        {
            "key": "src/Order.php",
            "details": {
                "file": "src/Order.php",
                "line": 8,
                "message": "Avoid unused local variables such as '$a'.",
                "source": "phpmd:UnusedLocalVariable",
            },
        },
        {
            "key": "src/Order.php",
            "details": {
                "file": "src/Order.php",
                "line": 8,
                "message": "Avoid unused local variables such as '$b'.",
                "source": "phpmd:UnusedLocalVariable",
            },
        },
    ]

    assert len(_kept_issues("unused-variable", issues)) == 2


def test_a_block_and_a_line_comment_on_one_line_are_two_issues() -> None:
    issues = [
        {
            "key": "src/a.ts",
            "details": {
                "file": "src/a.ts",
                "line": 4,
                "message": 'block-line comment: "/* legacy */"',
                "source": "comment:non-essential",
            },
        },
        {
            "key": "src/a.ts",
            "details": {
                "file": "src/a.ts",
                "line": 4,
                "message": 'single-line comment: "// remove me"',
                "source": "comment:non-essential",
            },
        },
    ]

    assert len(_kept_issues("non-essential-comment", issues)) == 2


def test_a_later_findings_own_repeated_place_survives_too() -> None:
    already_named = {
        "key": "src/Order.java",
        "details": {"file": "src/Order.java", "line": 5, "source": "pmd:UnusedLocalVariable"},
    }
    on_one_line = [
        {
            "key": "src/Order.java",
            "details": {"file": "src/Order.java", "line": 12, "message": "'a'"},
        },
        {
            "key": "src/Order.java",
            "details": {"file": "src/Order.java", "line": 12, "message": "'b'"},
        },
    ]
    findings = [
        {"smell": "unused-variable", "details": {}, "issues": [already_named]},
        {"smell": "unused-variable", "details": {}, "issues": on_one_line},
    ]

    assert len(merged(findings, _same_guide)[0]["issues"]) == 3
