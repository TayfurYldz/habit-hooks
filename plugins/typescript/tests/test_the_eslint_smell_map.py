from __future__ import annotations

from pathlib import Path

from eslint_project import SHIPPED_CONFIG, project, sensor_findings

MANY_PARAMETERS_TS = """export function buildOrder(
  a: string, b: string, c: string, d: string,
): string {
  return a + b + c + d;
}
"""

TYPESCRIPT_MAX_PARAMS_CONFIG = """import parser from "@typescript-eslint/parser";
import plugin from "@typescript-eslint/eslint-plugin";

export default [
  {
    files: ["**/*.ts"],
    languageOptions: { parser },
    plugins: { "@typescript-eslint": plugin },
    rules: { "@typescript-eslint/max-params": ["error", { max: 3 }] },
  },
];
"""


def test_the_typescript_rule_arrives_as_the_unused_variable_smell(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "eslint.config.mjs").write_bytes(SHIPPED_CONFIG.read_bytes())

    findings = sensor_findings(consumer)

    assert [finding["smell"] for finding in findings] == ["unused-variable"], findings
    assert findings[0]["issues"][0]["details"]["source"] == (
        "eslint:@typescript-eslint/no-unused-vars"
    )


def test_the_typescript_max_params_rule_arrives_as_too_many_parameters(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "eslint.config.mjs").write_text(
        TYPESCRIPT_MAX_PARAMS_CONFIG, encoding="utf-8"
    )
    (consumer / "src" / "repository.ts").write_text(
        MANY_PARAMETERS_TS, encoding="utf-8"
    )

    findings = sensor_findings(consumer)

    assert [finding["smell"] for finding in findings] == [
        "too-many-parameters"
    ], findings
    assert findings[0]["issues"][0]["details"]["source"] == (
        "eslint:@typescript-eslint/max-params"
    )
