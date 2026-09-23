
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from ..project_paths import project_relative
from .model import SensorError

def malformed(sensor: str, described: str, *, contract: bool = False) -> SensorError:
    message = f"sensor {sensor!r} emitted {described}"
    if contract:
        message += ", which the findings contract has no shape for"
    return SensorError(message)


def anchored(findings: list[dict], project_dir: Path, sensor: str) -> list[dict]:
    return [_anchored_finding(finding, project_dir, sensor) for finding in findings]


def aliasing_notices(findings: list[dict], sensor: str) -> list[str]:
    files_by_key: defaultdict[str, set[str]] = defaultdict(set)
    for issue in _issues(findings):
        file = _reported_file(issue, sensor)
        if file is not None and "key" in issue:
            files_by_key[issue["key"]].add(file)
    return [
        _alias_notice(sensor, key, files)
        for key, files in sorted(files_by_key.items())
        if len(files) > 1 and key in files
    ]


def _alias_notice(sensor: str, key: str, files: set[str]) -> str:
    return (
        f"sensor {sensor!r} keys {len(files)} files as {key!r} "
        f"({', '.join(sorted(files))}) — snoozing it would exempt them all"
    )


def _anchored_finding(finding: dict, project_dir: Path, sensor: str) -> dict:
    issues = finding.get("issues")
    if not issues:
        return finding
    if not isinstance(issues, list):
        raise malformed(sensor, "a finding whose 'issues' is not a list", contract=False)
    return {
        **finding,
        "issues": [_anchored_issue(issue, project_dir, sensor) for issue in issues],
    }


def _anchored_issue(issue: dict, project_dir: Path, sensor: str) -> dict:
    if not isinstance(issue, dict):
        raise malformed(sensor, "an issue that is not an object", contract=False)
    reported = _reported_file(issue, sensor)
    if reported is None:
        return issue
    file = project_relative(reported, project_dir)
    if file is None:
        raise SensorError(
            f"sensor {sensor!r} reported a path outside the project: {reported!r}"
        )
    anchored_issue = {**issue, "details": {**issue["details"], "file": file}}
    key = issue.get("key")
    if isinstance(key, str):
        anchored_issue["key"] = project_relative(key, project_dir) or key
    return anchored_issue



def _issues(findings: list[dict]) -> Iterator[dict]:
    return (issue for finding in findings for issue in finding.get("issues", []))


def _reported_file(issue: dict, sensor: str) -> str | None:
    details = issue.get("details", {})
    if not isinstance(details, dict):
        raise malformed(sensor, "an issue whose 'details' is not an object", contract=False)
    file = details.get("file")
    return file if isinstance(file, str) and file else None
