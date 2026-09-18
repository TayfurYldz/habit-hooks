"""A project with files, an index and findings on stdin, shared by the snooze
tests: the same small situation — a file on disk, a finding anchored to it, and
the real CLI — without copies drifting apart."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from habit_hooks.snooze import parse_args, run


def a_project_with(project_dir: Path, name: str, text: str) -> Path:
    path = project_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return project_dir


def feed_stdin(monkeypatch: pytest.MonkeyPatch, findings: object) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(findings)))


def finding(key: str, file: str | None = None) -> dict:
    """One issue, anchored to ``file`` — or to its key, as a sensor may leave it."""
    details = {"file": file} if file is not None else {}
    return {
        "smell": "oversized-file",
        "details": {"maxAllowed": 200},
        "issues": [{"key": key, "details": details}],
    }


def aliased(*files: str) -> list[dict]:
    """One key over several files — see ``anchor_file`` for when a sensor reports that."""
    return [
        {
            "smell": "unused-dependency",
            "details": {},
            "issues": [{"key": "requests", "details": {"file": f}} for f in files],
        }
    ]


def snooze(project_dir: Path, monkeypatch: pytest.MonkeyPatch, findings: list) -> None:
    feed_stdin(monkeypatch, findings)
    assert run(parse_args(["--snooze"]), project_dir) == 0
