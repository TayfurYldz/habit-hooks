
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1]
    / "src/habit_hooks_python/sensors/deptry_sensor.py"
)


def test_a_project_declaring_no_dependencies_is_a_clean_run(
    tmp_path: Path, deptry: str
) -> None:
    (tmp_path / "app.py").write_text("import os\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SENSOR), deptry],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "[]"
    assert result.stderr.strip() == ""


def test_deptry_still_answers_a_missing_declaration_with_that_error(
    tmp_path: Path, deptry: str
) -> None:
    (tmp_path / "app.py").write_text("import os\n", encoding="utf-8")

    result = subprocess.run(
        [deptry, "."],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    assert "DependencySpecificationNotFoundError" in result.stderr


def test_deptry_failing_another_way_still_fails_the_run(
    tmp_path: Path, deptry: str
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.0.0"\ndependencies = []\n\n'
        "[tool.deptry]\nnot_a_real_option = true\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text("import os\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SENSOR), deptry],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 2
    assert result.stdout.strip() == ""
    assert "not_a_real_option" in result.stderr
