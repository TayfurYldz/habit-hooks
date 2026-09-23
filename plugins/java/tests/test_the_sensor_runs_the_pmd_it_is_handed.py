from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

from tool_lookup import where_the_bare_name_reaches_nothing

SENSOR = (
    Path(__file__).resolve().parents[1] / "src/habit_hooks_java/pmd_sensor.py"
)

FIVE_PARAMETER_METHOD = """class Billing {
    double charge(double a, double b, double c, double d, double e) {
        return a + b + c + d + e;
    }
}
"""


def test_the_pmd_it_is_handed_runs_where_the_name_reaches_nothing(
    tmp_path: Path, pmd: str
) -> None:
    (tmp_path / "Billing.java").write_text(FIVE_PARAMETER_METHOD, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SENSOR), pmd, "--", "Billing.java"],
        cwd=tmp_path,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=where_the_bare_name_reaches_nothing("pmd"),
    )

    assert result.returncode == 0, result.stderr
    assert [finding["smell"] for finding in json.loads(result.stdout)] == [
        "too-many-parameters"
    ]
