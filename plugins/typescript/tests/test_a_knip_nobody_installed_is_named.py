from __future__ import annotations

import subprocess
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "src/habit_hooks_typescript/sensors/knip.cjs"
)


def test_a_knip_nobody_installed_answers_the_way_a_shell_does(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "package.json").write_text('{ "name": "demo" }', encoding="utf-8")

    result = subprocess.run(
        ["node", str(SENSOR)],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode != 0
    assert result.stdout.strip() == ""
    assert result.stderr.strip() == "knip: command not found"
