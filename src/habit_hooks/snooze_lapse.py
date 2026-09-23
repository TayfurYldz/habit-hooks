"""What a snooze holds against, and what approving records.

A snooze holds while each file it covers still holds the content that was
approved with it. Git is never asked: the index is checked in, so whoever
changes a file re-approves it in the same change, and file and record travel
together.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .snooze_index import Anchors, Index

CONTENT_ALGORITHM = "sha256"


def anchor_file(issue: dict) -> str:
    """The file an issue's snooze is anchored to: its ``details.file``, else its key.

    A sensor keys an issue by whatever groups it best — ``deptry`` by module,
    ``knip`` by export — so the file to record and to compare comes from the
    details bag. A ``file`` that is not a non-empty string reads as absent, the
    same reading ``sensors.finding_paths._reported_file`` gives it.
    """
    file = issue.get("details", {}).get("file")
    return file if isinstance(file, str) and file else issue["key"]


def anchors_by_key(findings: list[dict]) -> dict[str, set[str]]:
    """Every key the run reports, with the files it reports that key under."""
    anchors: dict[str, set[str]] = {}
    for finding in findings:
        for issue in finding["issues"]:
            anchors.setdefault(issue["key"], set()).add(anchor_file(issue))
    return anchors


def content_hash(path: Path) -> str | None:
    """The digest of ``path``'s content, or ``None`` when it is no file to read.

    ``\\r\\n`` is normalised away so a digest written on a CRLF checkout matches
    on an LF one — the index is checked in and shared. An unreadable path
    records nothing rather than failing the run.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    digest = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return f"{CONTENT_ALGORITHM}:{digest}"


def holds(recorded: Anchors, anchor: str, project_dir: Path) -> bool:
    """Whether ``anchor`` still holds the content approved for it.

    An entry recording nothing cannot be contradicted, so it holds — that is an
    index written before recording, and the reason an upgrade re-arms nothing.
    Within an entry that does record, an anchor with no recording is new debt:
    the key was approved through other files, and this one was judged by nobody.
    """
    if not recorded:
        return True
    if anchor not in recorded:
        return False
    return recorded[anchor] == content_hash(project_dir / anchor)


def renewed(index: Index, findings: list[dict], project_dir: Path) -> Index:
    """``index``, with every reported key recording its anchors as they stand.

    This is what ``--snooze`` does: approve what it is fed, overwriting what the
    entry recorded before. An anchor the run does not report is left alone —
    this run measured nothing about it.
    """
    return index | {
        key: index.get(key, {}) | _recorded(anchors, project_dir)
        for key, anchors in anchors_by_key(findings).items()
    }


def _recorded(anchors: set[str], project_dir: Path) -> Anchors:
    """The content each anchor holds now, skipping the ones that are no file:
    a file briefly unreadable is not an answer, so it keeps what it had."""
    fresh = {anchor: content_hash(project_dir / anchor) for anchor in anchors}
    return {anchor: content for anchor, content in fresh.items() if content is not None}
