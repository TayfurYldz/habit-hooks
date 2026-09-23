
from __future__ import annotations

from pathlib import Path

import pytest


def project_with_no_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    machine_bin(tmp_path).mkdir()
    monkeypatch.setenv("PATH", str(machine_bin(tmp_path)))
    project = tmp_path / "project"
    project.mkdir()
    return project


def machine_bin(tmp_path: Path) -> Path:
    return tmp_path / "machine-bin"
