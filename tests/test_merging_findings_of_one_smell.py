
from __future__ import annotations

from habit_hooks.merged_findings import merged

ONE_GUIDE = "guides/the-one.md"


def _same_guide(finding: dict) -> str:
    return ONE_GUIDE


def _guide_of_its_language(finding: dict) -> str:
    return f"{finding.get('language')}/{finding['smell']}.md"


def _finding(smell: str, issues: list[dict], **rest: object) -> dict:
    return {"smell": smell, "details": {}, "issues": issues, **rest}


def _at(file: str, **details: object) -> dict:
    return {"key": file, "details": {"file": file, **details}}


def test_no_findings_merge_into_no_findings() -> None:
    assert merged([], _same_guide) == []


def test_one_finding_comes_back_as_it_was() -> None:
    finding = _finding("oversized-file", [_at("src/a.py")], language="python")

    assert merged([finding], _same_guide) == [finding]


def test_merging_leaves_the_findings_it_was_handed_alone() -> None:
    finding = _finding("oversized-file", [_at("src/a.py")])

    merged([finding, _finding("oversized-file", [_at("src/b.py")])], _same_guide)

    assert finding["issues"] == [_at("src/a.py")]


def test_a_smell_arriving_three_times_is_one_finding() -> None:
    findings = [_finding("duplicated-code", [_at(f"src/{n}.py")]) for n in "abc"]

    assert len(merged(findings, _same_guide)) == 1


def test_issues_keep_the_order_they_arrived_in() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py"), _at("src/b.py")]),
        _finding("oversized-file", [_at("src/c.py")]),
    ]

    issues = merged(findings, _same_guide)[0]["issues"]

    assert [issue["key"] for issue in issues] == ["src/a.py", "src/b.py", "src/c.py"]


def test_one_smell_coached_by_two_plugins_stays_two_findings() -> None:
    findings = [
        _finding("high-complexity", [_at("src/a.py", line=12)], language="python"),
        _finding("high-complexity", [_at("src/b.ts", line=40)], language="typescript"),
    ]

    assert len(merged(findings, _guide_of_its_language)) == 2


def test_two_smells_sharing_one_guide_keep_their_own_banners() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py")]),
        _finding("high-complexity", [_at("src/a.py")]),
    ]

    assert [f["smell"] for f in merged(findings, _same_guide)] == [
        "oversized-file",
        "high-complexity",
    ]


def test_a_fact_only_one_finding_stated_survives() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py")]),
        {
            "smell": "oversized-file",
            "details": {"maxAllowed": 200},
            "issues": [_at("src/b.py")],
        },
    ]

    assert merged(findings, _same_guide)[0]["details"] == {"maxAllowed": 200}


def test_a_fact_two_findings_disagree_about_is_dropped() -> None:
    findings = [
        {"smell": "duplicated-code", "details": {"lines": 21}, "issues": []},
        {"smell": "duplicated-code", "details": {"lines": 40}, "issues": []},
    ]

    assert merged(findings, _same_guide)[0]["details"] == {}


def test_a_language_the_first_finding_did_not_carry_is_taken_from_the_next() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.ts")]),
        _finding("oversized-file", [_at("src/b.ts")], language="typescript"),
    ]

    assert merged(findings, _same_guide)[0]["language"] == "typescript"


def test_the_first_finding_to_name_a_top_level_value_keeps_it() -> None:
    findings = [
        _finding("oversized-file", [_at("src/a.py")], language="python"),
        _finding("oversized-file", [_at("src/b.ts")], language="typescript"),
    ]

    assert merged(findings, _same_guide)[0]["language"] == "python"


def test_a_fact_restated_after_a_contradiction_stays_dropped() -> None:
    findings = [
        {"smell": "duplicated-code", "details": {"lines": 21}, "issues": []},
        {"smell": "duplicated-code", "details": {"lines": 40}, "issues": []},
        {"smell": "duplicated-code", "details": {"lines": 21}, "issues": []},
    ]

    assert merged(findings, _same_guide)[0]["details"] == {}
