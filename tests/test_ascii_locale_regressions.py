
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from plugin_fixture import write_plugin, write_project_config

ASCII_LOCALE_ENV = {
    **os.environ,
    "PYTHONUTF8": "0",
    "PYTHONCOERCECLOCALE": "0",
    "LC_ALL": "C",
}

_RUN_MAPPER = "import sys; from habit_hooks.mapper import main; sys.exit(main([]))"

_ISSUE = {"key": "src/a.py", "details": {"file": "src/a.py"}}


def _finding_for(smell: str) -> dict:
    return {"smell": smell, "details": {}, "issues": [_ISSUE]}


def _run_mapper_under_ascii_locale(
    project_dir: Path, findings: list[dict]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _RUN_MAPPER],
        cwd=project_dir,
        env=ASCII_LOCALE_ENV,
        input=json.dumps(findings),
        capture_output=True,
        encoding="utf-8",
    )


def test_a_guide_containing_non_ascii_text_is_read_correctly(tmp_path: Path) -> None:
    write_plugin(
        tmp_path,
        "fixt",
        {"guides/oversized-file.md": "Split the file — the seams are usually clear.\n"},
    )
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    result = _run_mapper_under_ascii_locale(tmp_path, [_finding_for("oversized-file")])

    assert "Split the file — the seams are usually clear." in result.stdout


def test_non_ascii_output_reaches_stdout_correctly(tmp_path: Path) -> None:
    write_plugin(
        tmp_path,
        "fixt",
        {"guides/oversized-file.md": "Split the file into smaller pieces.\n"},
    )
    write_project_config(tmp_path, 'plugins = ["fixt"]')

    result = _run_mapper_under_ascii_locale(tmp_path, [_finding_for("oversized-file")])

    assert "── oversized-file (1 issue) ──" in result.stdout
