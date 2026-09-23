
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from finding import a_finding, an_issue
from habit_hooks.snooze import parse_args, run


def a_project_with(project_dir: Path, name: str, text: str) -> Path:
    path = project_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return project_dir


def feed_stdin(monkeypatch: pytest.MonkeyPatch, findings: object) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(findings)))


def finding(key: str, file: str | None = None) -> dict:
    return a_finding(
        details={"maxAllowed": 200}, issues=[an_issue(key, file=file)]
    )


def aliased(*files: str) -> list[dict]:
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
