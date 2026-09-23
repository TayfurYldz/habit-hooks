from __future__ import annotations

from pathlib import Path

from eslint_project import UNUSED_LOCAL_LINE, project, sensor_findings, sensor_run

NO_CONSOLE_CONFIG = (
    'export default [{ files: ["**/*.ts"], rules: { "no-console": "error" } }];\n'
)
CONSOLE_TS = 'console.log("shipping this by accident");\n'
UNLOADABLE_CONFIG = 'throw new Error("this project\'s own config is broken");\n'

BOTH_TS = 'if (1 == "1") { console.log("shipping this by accident"); }\n'
UNDISCOVERABLE = Path("configs") / "eslint.mjs"


def test_a_flat_config_below_the_project_is_still_the_project_s_own(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    package = consumer / "packages" / "app" / "src"
    package.mkdir(parents=True)
    (consumer / "packages" / "app" / "eslint.config.mjs").write_text(
        NO_CONSOLE_CONFIG, encoding="utf-8"
    )
    (package / "x.ts").write_text(CONSOLE_TS, encoding="utf-8")

    findings = sensor_findings(consumer, ("packages/app/src/x.ts",))

    assert [finding["smell"] for finding in findings] == ["no-console"], findings


def test_a_flat_config_above_the_project_is_still_the_project_s_own(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (tmp_path / "eslint.config.mjs").write_text(NO_CONSOLE_CONFIG, encoding="utf-8")
    (consumer / "src" / "repository.ts").write_text(CONSOLE_TS, encoding="utf-8")

    findings = sensor_findings(consumer)

    assert [finding["smell"] for finding in findings] == ["no-console"], findings


def test_a_project_that_wrote_no_config_gets_the_shipped_one(tmp_path: Path) -> None:
    findings = sensor_findings(project(tmp_path))

    assert [finding["smell"] for finding in findings] == ["unused-variable"], findings
    issue = findings[0]["issues"][0]
    assert issue["details"]["source"] == "eslint:@typescript-eslint/no-unused-vars"
    assert issue["details"]["line"] == UNUSED_LOCAL_LINE


def test_a_config_named_through_the_sensor_s_args_is_the_config_that_runs(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / UNDISCOVERABLE.parent).mkdir()
    (consumer / UNDISCOVERABLE).write_text(NO_CONSOLE_CONFIG, encoding="utf-8")
    (consumer / "src" / "repository.ts").write_text(BOTH_TS, encoding="utf-8")

    findings = sensor_findings(consumer, args=("--config", str(UNDISCOVERABLE)))

    assert [finding["smell"] for finding in findings] == ["no-console"], findings


def test_a_config_eslint_cannot_load_fails_the_run_rather_than_falling_back(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "eslint.config.mjs").write_text(UNLOADABLE_CONFIG, encoding="utf-8")

    result = sensor_run(consumer)

    assert result.returncode != 0, result.stdout
    assert "this project's own config is broken" in result.stderr, result.stderr
    assert "unused-variable" not in result.stdout, result.stdout
