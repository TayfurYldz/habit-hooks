
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

FINDINGS = [
    {
        "smell": "left-todo",
        "details": {},
        "issues": [
            {
                "key": "src/notes.txt",
                "details": {
                    "file": "src/notes.txt",
                    "line": 3,
                    "message": "a TODO left behind",
                },
            }
        ],
    }
]
PLUGIN_TOML = (
    "sensors = [{ tool = 'stub-lint', args = ['${files}'], "
    "files = ['**/*.txt'], transform = 'map.jq' }]\n"
    "detectors = [{ name = 'stub-lint', kind = 'command', "
    "install = 'shipped inside the scenario sample', search_paths = ['bin'] }]\n"
)
TRANSFORM = (
    'map({smell: "left-todo", details: {}, issues: '
    '[{key: .file, details: {file: .file, line: .line, message: .message}}]})'
)
_POSIX_STUB = """#!/bin/sh
printf '['
first=yes
for file in "$@"; do
  [ "$first" = yes ] || printf ','
  first=no
  printf '{"file":"%s","line":3,"rule":"T-1","message":"a TODO left behind"}' "$file"
done
printf ']\\n'
"""
_WINDOWS_STUB = (
    "import json, sys\n"
    'print(json.dumps([{"file": file, "line": 3, "rule": "T-1", '
    '"message": "a TODO left behind"} for file in sys.argv[1:]]))\n'
)


def exemplar_scenario(project: Path) -> Path:
    plugin = project / ".habit-hooks" / "exemplar"
    _write(plugin / "config.toml", PLUGIN_TOML)
    _write(plugin / "map.jq", TRANSFORM + "\n")
    scenario = plugin / "scenarios" / "stub-lint"
    _write(scenario / "sample/src/notes.txt", "first\nsecond\na TODO left behind\n")
    _write(scenario / "approved.json", json.dumps(FINDINGS, indent=2) + "\n")
    _write(scenario / "scenario.toml", "tool = 'stub-lint'\n")
    _write_stub_tool(scenario / "sample" / "bin")
    return scenario


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_stub_tool(bin_dir: Path) -> None:
    if os.name == "nt":
        helper = bin_dir / "_stub_lint.py"
        _write(helper, _WINDOWS_STUB)
        _write(
            bin_dir / "stub-lint.cmd",
            f'@echo off\r\n"{sys.executable}" "{helper}" %*\r\n',
        )
        return
    _write(bin_dir / "stub-lint", _POSIX_STUB)
    tool = bin_dir / "stub-lint"
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
