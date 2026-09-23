from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SENSOR = (
    Path(__file__).resolve().parents[1] / "src/habit_hooks_java/pmd_sensor.py"
)

FIVE_PARAMETER_METHOD_WITH_UNUSED_IMPORT = """import java.io.File;
class Billing {
    double charge(double a, double b, double c, double d, double e) {
        return a + b + c + d + e;
    }
}
"""

TWO_PARAMETER_METHOD = """class Project {
    void save(String a, String b) {
    }
}
"""

TWO_IS_TOO_MANY_RULESET = """<?xml version="1.0"?>
<ruleset name="custom" xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 https://pmd.sourceforge.io/ruleset_2_0_0.xsd">
 <description>two parameters is already too many</description>
 <rule ref="category/java/design.xml/ExcessiveParameterList">
  <properties><property name="minimum" value="2"/></properties>
 </rule>
</ruleset>
"""


def _run(cwd: Path, pmd: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SENSOR), pmd, *arguments],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def test_a_pmd_flag_in_args_reaches_pmd(tmp_path: Path, pmd: str) -> None:
    (tmp_path / "Billing.java").write_text(FIVE_PARAMETER_METHOD_WITH_UNUSED_IMPORT, encoding="utf-8")

    without_the_flag = _run(tmp_path, pmd, ["--", "Billing.java"])
    with_the_flag = _run(tmp_path, pmd, ["--minimum-priority", "3", "--", "Billing.java"])

    assert without_the_flag.returncode == 0, without_the_flag.stderr
    without_smells = {finding["smell"] for finding in json.loads(without_the_flag.stdout)}
    assert without_smells == {"too-many-parameters", "unused-import"}

    assert with_the_flag.returncode == 0, with_the_flag.stderr
    with_smells = {finding["smell"] for finding in json.loads(with_the_flag.stdout)}
    assert with_smells == {"too-many-parameters"}


def test_a_ruleset_named_in_args_is_still_honoured(tmp_path: Path, pmd: str) -> None:
    (tmp_path / "Project.java").write_text(TWO_PARAMETER_METHOD, encoding="utf-8")
    ruleset = tmp_path / "strict.xml"
    ruleset.write_text(TWO_IS_TOO_MANY_RULESET, encoding="utf-8")

    result = _run(tmp_path, pmd, ["--rulesets", str(ruleset), "--", "Project.java"])

    assert result.returncode == 0, result.stderr
    findings = json.loads(result.stdout)
    assert [finding["smell"] for finding in findings] == ["too-many-parameters"]
