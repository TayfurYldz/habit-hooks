
from __future__ import annotations

from pathlib import Path

from installed_env import require_tool, run_and_collect_findings
from installed_projects import (
    JAVA_SOURCE,
    PHP_SOURCE,
    PYTHON_SOURCE,
    RUBY_SOURCE,
    TYPESCRIPT_SOURCE,
    java_project,
    php_project,
    python_project,
    ruby_project,
    typescript_project,
)


def _sole_issue(findings: list[dict], smell: str) -> dict:
    assert [finding["smell"] for finding in findings] == [smell], findings
    issues = findings[0]["issues"]
    assert len(issues) == 1, issues
    return issues[0]


def test_installed_php_plugin_locates_its_bundled_phar(
    installed_habit_sensors: Path, tmp_path: Path
) -> None:
    require_tool("php")
    project = php_project(tmp_path)

    findings = run_and_collect_findings(installed_habit_sensors, project)

    by_smell = {finding["smell"]: finding for finding in findings}
    assert by_smell.keys() == {"too-many-parameters", "unused-variable"}
    for finding in findings:
        assert finding["language"] == "php"
        issue = finding["issues"][0]
        assert Path(issue["key"]).name == PHP_SOURCE
        assert issue["details"]["source"].startswith("phpmd:")


def test_installed_java_plugin_locates_its_bundled_ruleset(
    installed_habit_sensors: Path, tmp_path: Path
) -> None:
    require_tool("pmd")
    project = java_project(tmp_path)

    findings = run_and_collect_findings(installed_habit_sensors, project)

    by_smell = {finding["smell"]: finding for finding in findings}
    assert by_smell.keys() == {
        "deep-nesting",
        "too-many-parameters",
        "unused-import",
        "unused-variable",
    }
    assert (
        by_smell["deep-nesting"]["issues"][0]["details"]["source"]
        == "pmd:AvoidDeeplyNestedIfStmts"
    )
    for finding in findings:
        assert finding["language"] == "java"
        issue = finding["issues"][0]
        assert Path(issue["key"]).name == JAVA_SOURCE
        assert issue["details"]["source"].startswith("pmd:")


def test_installed_typescript_plugin_resolves_ts_morph_from_the_project(
    installed_habit_sensors: Path, tmp_path: Path
) -> None:
    require_tool("node")
    project = typescript_project(tmp_path)

    issue = _sole_issue(
        run_and_collect_findings(installed_habit_sensors, project),
        "non-essential-comment",
    )

    assert issue["key"] == TYPESCRIPT_SOURCE
    assert issue["details"]["file"] == TYPESCRIPT_SOURCE
    assert issue["details"]["source"] == "comment:non-essential"


def test_installed_ruby_plugin_runs_its_rubocop_pipeline(
    installed_habit_sensors: Path, tmp_path: Path
) -> None:
    require_tool("rubocop")
    project = ruby_project(tmp_path)

    findings = run_and_collect_findings(installed_habit_sensors, project)

    by_smell = {finding["smell"]: finding for finding in findings}
    assert by_smell.keys() == {"too-many-parameters", "unused-variable"}
    for finding in findings:
        assert finding["language"] == "ruby"
        issue = finding["issues"][0]
        assert Path(issue["key"]).name == RUBY_SOURCE
        assert issue["details"]["source"].startswith("rubocop:")


def test_installed_python_plugin_runs_its_ruff_pipeline(
    installed_habit_sensors: Path, tmp_path: Path
) -> None:
    require_tool("ruff")
    project = python_project(tmp_path)

    issue = _sole_issue(
        run_and_collect_findings(installed_habit_sensors, project),
        "unused-variable",
    )

    assert issue["key"] == PYTHON_SOURCE
    assert issue["details"]["source"] == "ruff:F841"
