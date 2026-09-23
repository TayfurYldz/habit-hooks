from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "habit_hooks_java"

FIVE_PARAMETER_METHOD = """class Billing {
    double charge(double a, double b, double c, double d, double e) {
        return a + b + c + d + e;
    }
}
"""


def _vendored_plugin(project: Path) -> Path:
    plugin = project / ".habit-hooks" / "java"
    shutil.copytree(
        PACKAGE,
        plugin,
        ignore=shutil.ignore_patterns("__pycache__", "scenarios"),
    )
    return plugin / "pmd_sensor.py"


def test_a_vendored_sensor_reports_a_smell_with_no_package_around_it(
    tmp_path: Path, pmd: str
) -> None:
    (tmp_path / "Billing.java").write_text(FIVE_PARAMETER_METHOD, encoding="utf-8")
    sensor = _vendored_plugin(tmp_path)

    result = subprocess.run(
        [sys.executable, "-S", str(sensor), pmd, "--", "Billing.java"],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)
    assert [finding["smell"] for finding in findings] == ["too-many-parameters"]
