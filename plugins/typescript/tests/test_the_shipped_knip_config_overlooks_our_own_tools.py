from __future__ import annotations

import json
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).parents[1]
PACKAGE = PLUGIN / "src" / "habit_hooks_typescript"
SENSOR = PACKAGE / "sensors" / "knip.cjs"
SHIPPED_CONFIG = PACKAGE / "knip.json"

TOOLS_HABIT_HOOKS_REQUIRES = tuple(
    json.loads(SHIPPED_CONFIG.read_text(encoding="utf-8"))["ignoreDependencies"]
)

THE_PROJECTS_OWN_DEAD_WEIGHT = "left-pad"

KNIPS_OWN = ("knip", "typescript")

ENTRY = 'import { usedInProduction } from "./helper";\nexport const app = usedInProduction();\n'
HELPER = (
    "export function usedInProduction(): number {\n  return 1;\n}\n\n"
    "export function usedOnlyByTests(): number {\n  return 2;\n}\n"
)
TEST = 'import { usedOnlyByTests } from "../src/helper";\n\nusedOnlyByTests();\n'

THEIR_OWN_CONFIG = json.dumps(
    {"entry": ["src/index.ts!"], "project": ["src/**/*.ts!"]}
)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir(parents=True)
    declared = [*TOOLS_HABIT_HOOKS_REQUIRES, *KNIPS_OWN, THE_PROJECTS_OWN_DEAD_WEIGHT]
    (project / "package.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "version": "0.0.0",
                "devDependencies": {name: "*" for name in sorted(declared)},
            }
        ),
        encoding="utf-8",
    )
    (project / "src" / "index.ts").write_text(ENTRY, encoding="utf-8")
    (project / "src" / "helper.ts").write_text(HELPER, encoding="utf-8")
    (project / "tests" / "helper.test.ts").write_text(TEST, encoding="utf-8")
    (project / "node_modules").symlink_to(PLUGIN / "node_modules")
    return project


def _findings(project: Path) -> list[dict]:
    result = subprocess.run(
        ["node", str(SENSOR)],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _keys_of(findings: list[dict], smell: str) -> set[str]:
    return {
        issue["key"]
        for finding in findings
        if finding["smell"] == smell
        for issue in finding["issues"]
    }


def test_the_tools_habit_hooks_asked_for_are_never_the_projects_dead_weight(
    tmp_path: Path,
) -> None:
    reported = _keys_of(_findings(_project(tmp_path)), "unused-dependency")

    assert reported.isdisjoint(TOOLS_HABIT_HOOKS_REQUIRES), reported


def test_a_dependency_the_project_itself_stopped_using_is_still_reported(
    tmp_path: Path,
) -> None:
    reported = _keys_of(_findings(_project(tmp_path)), "unused-dependency")

    assert reported == {THE_PROJECTS_OWN_DEAD_WEIGHT}


def test_a_project_that_wrote_its_own_config_gets_its_own_answer(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    (project / "knip.json").write_text(THEIR_OWN_CONFIG, encoding="utf-8")

    reported = _keys_of(_findings(project), "unused-dependency")

    assert reported.issuperset(TOOLS_HABIT_HOOKS_REQUIRES), reported


def test_the_gated_production_pass_still_runs_under_the_shipped_config(
    tmp_path: Path,
) -> None:
    findings = _findings(_project(tmp_path))

    assert _keys_of(findings, "test-only-dead-code") == {"usedOnlyByTests"}
