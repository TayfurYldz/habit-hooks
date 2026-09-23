
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from plugin_layouts import outside_the_project, sensor

PLUGIN = Path(__file__).parents[1]
HELPER = "comment.cjs"

COMMONJS_MANIFEST = '{ "name": "demo", "version": "0.0.0" }\n'

SOURCE_WITH_A_COMMENT = (
    "export function used(): void {\n"
    "  // this comment restates what the code already says clearly\n"
    "}\n"
)
SOURCE_FILE = "src/helper.ts"


def project(tmp_path: Path, manifest: str = COMMONJS_MANIFEST) -> Path:
    created = _bare_project(tmp_path, manifest)
    (created / "node_modules").symlink_to(PLUGIN / "node_modules")
    return created


def project_without_ts_morph(tmp_path: Path) -> Path:
    return _bare_project(tmp_path, COMMONJS_MANIFEST)


def _bare_project(tmp_path: Path, manifest: str) -> Path:
    created = tmp_path / "demo"
    (created / "src").mkdir(parents=True)
    (created / "package.json").write_text(manifest, encoding="utf-8")
    (created / SOURCE_FILE).write_text(SOURCE_WITH_A_COMMENT, encoding="utf-8")
    return created


def installed_outside_the_project(tmp_path: Path) -> Path:
    return sensor(outside_the_project(tmp_path), HELPER)


def run(project: Path, helper: Path) -> subprocess.CompletedProcess[str]:
    path = f"{project / 'node_modules' / '.bin'}{os.pathsep}{os.environ['PATH']}"
    return subprocess.run(
        ["node", str(helper), SOURCE_FILE],
        cwd=project,
        env={**os.environ, "PATH": path},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def as_ts_morph_spells(file: Path) -> str:
    return file.resolve().as_posix()


def reported_files(result: subprocess.CompletedProcess[str]) -> list[str]:
    assert result.returncode == 0, result.stderr
    return [
        issue["key"]
        for finding in json.loads(result.stdout)
        for issue in finding["issues"]
    ]
