from __future__ import annotations

from pathlib import Path

RULESET_LOCATIONS = (
    "src/main/resources/pmd/ruleset.xml",
    "pmd/ruleset.xml",
    "ruleset.xml",
    "pmd.xml",
)

RULESET_OPTIONS = ("--rulesets", "-R")
ATTACHED_RULESET_PREFIXES = ("--rulesets=", "-R=", "-R")


def ruleset_of(argv: list[str], project: Path) -> tuple[Path, list[str]]:
    for i, token in enumerate(argv):
        if token in RULESET_OPTIONS and i + 1 < len(argv):
            return Path(argv[i + 1]), [*argv[:i], *argv[i + 2 :]]
        for prefix in ATTACHED_RULESET_PREFIXES:
            if token.startswith(prefix) and len(token) > len(prefix):
                return Path(token[len(prefix) :]), [*argv[:i], *argv[i + 1 :]]
    for name in RULESET_LOCATIONS:
        if (project / name).is_file():
            return project / name, argv
    return Path(__file__).with_name("pmd-ruleset.xml"), argv
