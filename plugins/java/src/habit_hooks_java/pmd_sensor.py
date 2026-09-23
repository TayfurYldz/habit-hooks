from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pmd_ruleset import ruleset_of

RULE_SMELLS = {
    "AvoidDeeplyNestedIfStmts": "deep-nesting",
    "ExcessiveParameterList": "too-many-parameters",
    "CyclomaticComplexity": "high-complexity",
    "NcssCount": "oversized-function",
    "UnusedLocalVariable": "unused-variable",
    "UnusedPrivateField": "unused-class-member",
    "UnusedPrivateMethod": "unused-class-member",
    "UnnecessaryImport": "unused-import",
    "EmptyCatchBlock": "swallowed-exception",
}

METHOD_LEVEL_RULES = ("NcssCount", "CyclomaticComplexity")
METHOD_LEVEL_PREFIXES = ("The method", "The constructor")

SUCCESS_EXIT_CODES = (0, 4)


def run_pmd(pmd: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [pmd, "check", "--no-cache", "--format", "json", *arguments],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" not in argv:
        return argv, []
    index = len(argv) - 1 - argv[::-1].index("--")
    return argv[:index], argv[index + 1 :]


def violations(report: dict) -> list[dict]:
    return [
        {"file": entry["filename"], "violation": violation}
        for entry in report.get("files", [])
        for violation in entry["violations"]
    ]


def smell_of(entry: dict) -> str | None:
    violation = entry["violation"]
    rule = violation["rule"]
    if rule in METHOD_LEVEL_RULES and not violation["description"].startswith(
        METHOD_LEVEL_PREFIXES
    ):
        return None
    return RULE_SMELLS.get(rule)


def source_line(entry: dict) -> str | None:
    violation = entry["violation"]
    try:
        line = Path(entry["file"]).read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()[violation["beginline"] - 1]
    except (OSError, IndexError):
        return None
    return line.strip() or None


def issue(entry: dict, smell: str) -> dict:
    violation = entry["violation"]
    details = {
        "file": entry["file"],
        "line": violation["beginline"],
        "message": violation["description"],
        "source": "pmd:" + violation["rule"],
    }
    if smell == "unused-class-member":
        content = source_line(entry)
        if content is not None:
            details["content"] = content
    return {
        "key": entry["file"],
        "details": details,
    }


def findings(entries: list[dict]) -> list[dict]:
    by_smell: dict[str, list[dict]] = {}
    for entry in entries:
        smell = smell_of(entry)
        if smell is not None:
            by_smell.setdefault(smell, []).append(issue(entry, smell))
    return [
        {"smell": smell, "details": {}, "issues": issues}
        for smell, issues in by_smell.items()
    ]


def main() -> int:
    pmd, argv = sys.argv[1], sys.argv[2:]
    pmd_args, files = split_argv(argv)
    ruleset, remaining_args = ruleset_of(pmd_args, Path.cwd())
    file_args = [token for file in files for token in ("-d", file)]
    result = run_pmd(pmd, ["-R", str(ruleset), *remaining_args, *file_args])
    if result.returncode not in SUCCESS_EXIT_CODES:
        sys.stderr.write(processing_errors(result.stdout) or result.stderr or result.stdout)
        return 2
    print(json.dumps(findings(violations(json.loads(result.stdout)))))
    return 0


def processing_errors(stdout: str) -> str:
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        return ""
    errors = report.get("processingErrors", [])
    return "".join(f"{entry['filename']}: {entry['message']}\n" for entry in errors)


if __name__ == "__main__":
    sys.exit(main())
