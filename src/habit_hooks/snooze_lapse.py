
from __future__ import annotations

import hashlib
from pathlib import Path

from .snooze_index import Anchors, Index

CONTENT_ALGORITHM = "sha256"


def anchor_file(issue: dict) -> str:
    file = issue.get("details", {}).get("file")
    return file if isinstance(file, str) and file else issue["key"]


def anchors_by_key(findings: list[dict]) -> dict[str, set[str]]:
    anchors: dict[str, set[str]] = {}
    for finding in findings:
        for issue in finding["issues"]:
            anchors.setdefault(issue["key"], set()).add(anchor_file(issue))
    return anchors


def content_hash(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    digest = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return f"{CONTENT_ALGORITHM}:{digest}"


def holds(recorded: Anchors, anchor: str, project_dir: Path) -> bool:
    if not recorded:
        return True
    if anchor not in recorded:
        return False
    return recorded[anchor] == content_hash(project_dir / anchor)


def renewed(index: Index, findings: list[dict], project_dir: Path) -> Index:
    return index | {
        key: index.get(key, {}) | _recorded(anchors, project_dir)
        for key, anchors in anchors_by_key(findings).items()
    }


def _recorded(anchors: set[str], project_dir: Path) -> Anchors:
    fresh = {anchor: content_hash(project_dir / anchor) for anchor in anchors}
    return {anchor: content for anchor, content in fresh.items() if content is not None}
