from __future__ import annotations

import subprocess
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "src/habit_hooks_typescript/sensors/eslint.cjs"
)


def _run(project: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(SENSOR), *argv],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{ "name": "demo" }', encoding="utf-8")
    (project / "src" / "a.ts").write_text("export const a = 1;\n", encoding="utf-8")
    return project


def test_an_eslint_nobody_installed_answers_the_way_a_shell_does(
    tmp_path: Path,
) -> None:
    result = _run(_project(tmp_path), "--", "src/a.ts")

    assert result.returncode != 0
    assert result.stdout.strip() == ""
    assert result.stderr.strip() == "eslint: command not found"


def test_a_scope_with_nothing_to_lint_never_reaches_for_eslint(tmp_path: Path) -> None:
    result = _run(_project(tmp_path), "--", "README.md")

    assert result.returncode == 0
    assert result.stdout == "[]"
    assert result.stderr == ""
