from __future__ import annotations

import json
import subprocess
from pathlib import Path

from node_tool_stub import install, spawns

PLUGIN = Path(__file__).parents[1]
PACKAGE = PLUGIN / "src" / "habit_hooks_typescript"
SENSOR = PACKAGE / "sensors" / "knip.cjs"
SHIPPED_CONFIG = PACKAGE / "knip.json"

KNIP = "knip"
EMPTY_REPORT = {"files": [], "issues": []}


def project(tmp_path: Path) -> Path:
    created = tmp_path / "demo"
    created.mkdir()
    (created / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    install(created, KNIP, json.dumps(EMPTY_REPORT))
    return created


def passes(project: Path, args: tuple[str, ...] = ()) -> list[list[str]]:
    subprocess.run(
        ["node", str(SENSOR), *args],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [spawn[2:] for spawn in spawns(project, KNIP)]
