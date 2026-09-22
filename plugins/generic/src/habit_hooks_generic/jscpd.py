"""Run jscpd against a temp report and print ``duplicated-code`` findings.

Whose config is in play is a judgement, not data (#125), so this stays a
program until the framework owns the policy (#171).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

JSCPD_CONFIG = ".jscpd.json"
PACKAGE_JSON = "package.json"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("jscpd")
    parser.add_argument("--fallback-config", required=True)
    return parser.parse_args(argv)


def manifest_of(project: Path) -> dict:
    """``package.json``'s contents, or nothing — a typo in a file this
    sensor only peeks at must not fail the run.
    """
    manifest = project / PACKAGE_JSON
    if not manifest.is_file():
        return {}
    try:
        content = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return content if isinstance(content, dict) else {}


def project_configures_jscpd(project: Path) -> bool:
    """Whether jscpd's own discovery finds a config of the project's: a
    ``.jscpd.json``, or a ``jscpd`` key in ``package.json`` — those two only.
    """
    if (project / JSCPD_CONFIG).is_file():
        return True
    return bool(manifest_of(project).get("jscpd"))


def scan_paths(config: str) -> list[str]:
    return json.loads(Path(config).read_text(encoding="utf-8"))["path"]


def config_arguments(fallback: str, project: Path) -> list[str]:
    """Ours is named only when the project has none (#125); its ``path``
    then travels as positionals, because jscpd resolves a config's relative
    ``path`` against the config file's directory, where ``src`` names
    nothing the project owns.
    """
    if project_configures_jscpd(project):
        return []
    return ["--config", fallback, *scan_paths(fallback)]


def run_jscpd(
    jscpd: str, arguments: list[str], output: Path
) -> subprocess.CompletedProcess[str]:

    return subprocess.run(
        [jscpd, "--reporters", "json", "--output", str(output), *arguments],
        capture_output=True,
        encoding="utf-8",
        errors="replace",  # habit_hooks/sensors/spawn.py's policy
    )


def occurrence(side: dict) -> dict:
    return {
        "key": side["name"],
        "details": {
            "file": side["name"],
            "startLine": side["start"],
            "endLine": side["end"],
            "source": "jscpd:duplication",
        },
    }


def clone_finding(clone: dict) -> dict:
    return {
        "smell": "duplicated-code",
        "details": {"lines": clone["lines"], "tokens": clone["tokens"]},
        "issues": [occurrence(clone["firstFile"]), occurrence(clone["secondFile"])],
    }


def findings(report: Path) -> list[dict]:
    if not report.is_file():
        return []
    clones = json.loads(report.read_text(encoding="utf-8"))["duplicates"]
    return [clone_finding(clone) for clone in clones]


def main(argv: list[str] | None = None) -> int:
    """Print the findings, or fail the way the tool did: a report is read
    regardless of the exit code (a crossed threshold is a result, not a
    failure), and no report with a non-zero exit is a complaint, not a
    clean run.
    """
    args = parse_args(argv if argv is not None else sys.argv[1:])
    arguments = config_arguments(args.fallback_config, Path.cwd())
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        result = run_jscpd(args.jscpd, arguments, output)
        report = output / "jscpd-report.json"
        if result.returncode != 0 and not report.is_file():
            sys.stderr.write(result.stderr or result.stdout)
            return 1
        print(json.dumps(findings(report)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
