
from __future__ import annotations

from typing import Callable, Hashable

SETTLED_BY_THE_MERGE = ("smell", "details", "issues")

PLACE_FIELDS = ("file", "line", "column", "startLine", "endLine")


def merged(
    findings: list[dict], guide_of: Callable[[dict], Hashable]
) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for finding in findings:
        groups.setdefault((finding["smell"], guide_of(finding)), []).append(finding)
    return [_one_finding(group) for group in groups.values()]


def _one_finding(group: list[dict]) -> dict:
    finding = dict(group[0])
    for later in group[1:]:
        for name, value in later.items():
            if name not in SETTLED_BY_THE_MERGE and finding.get(name) is None:
                finding[name] = value
    finding["details"] = _agreed_facts(group)
    finding["issues"] = _issues_across(group)
    return finding


def _agreed_facts(group: list[dict]) -> dict:
    agreed: dict = {}
    contradicted: set = set()
    for finding in group:
        for name, fact in (finding.get("details") or {}).items():
            if name in contradicted:
                continue
            if name not in agreed:
                agreed[name] = fact
            elif agreed[name] != fact:
                del agreed[name]
                contradicted.add(name)
    return agreed


def _issues_across(group: list[dict]) -> list[dict]:
    issues = list(group[0].get("issues") or [])
    seen = {_observation(issue) for issue in issues}
    for later in group[1:]:
        own = later.get("issues") or []
        issues.extend(issue for issue in own if _observation(issue) not in seen)
        seen.update(_observation(issue) for issue in own)
    return issues


def _observation(issue: dict) -> tuple:
    details = issue.get("details") or {}
    return (issue.get("key"), *(details.get(field) for field in PLACE_FIELDS))
