"""habit-snooze: drop issues whose ``key`` is in a checked-in index.

As a transformer it reads findings on stdin and passes through everything it
does not drop. ``--snooze`` / ``--prune`` / ``--list`` maintain the index; the
transform itself only reads it.

A snooze is a record of the approved content: ``--snooze`` stores what each file
held, and an issue stays dropped only while its file still holds it. Editing the
file brings its issues back; ``--snooze`` again approves what is there now. Git
is not asked anything — see ``snooze_lapse``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cli import EXIT_TOOL_ERROR, add_version_flag, run_console
from .snooze_index import INDEX_PATH, Anchors, SnoozeError, Index, load_index, save_index
from .snooze_lapse import anchor_file, anchors_by_key, holds, renewed

__all__ = ["INDEX_PATH", "SnoozeError", "load_index", "main", "save_index"]

# The transformers that filter findings through this index. `habit-sensors
# --no-snooze` strips them so `--prune` can compare the index against a
# snooze-free view of the run instead of one snooze already emptied.
# `snooze-until-changed` is kept as a deprecated alias: what it was opt-in for
# is now the only behaviour.
SNOOZE_TRANSFORMERS = frozenset({"snooze", "snooze-until-changed"})


def transform(findings: list[dict], index: Index, project_dir: Path) -> list[dict]:
    """Drop snoozed issues, and any finding whose last issue we just dropped.

    An issue stays dropped only while the file it is anchored to still holds the
    content approved for its key in ``index``.

    A finding that arrives with no issues is passed through rather than dropped:
    nothing in it was snoozed. That keeps an empty index a true no-op, which
    matters now that snooze runs by default.
    """
    kept = []
    for finding in findings:
        issues = [
            issue for issue in finding["issues"] if not _still_snoozed(issue, index, project_dir)
        ]
        snoozed_them_all = finding["issues"] and not issues
        if not snoozed_them_all:
            kept.append({**finding, "issues": issues})
    return kept


def _still_snoozed(issue: dict, index: Index, project_dir: Path) -> bool:
    recorded = index.get(issue["key"])
    return recorded is not None and holds(recorded, anchor_file(issue), project_dir)


def read_findings() -> list[dict]:
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else []


def run(args: argparse.Namespace, project_dir: Path) -> int:
    if args.list:
        for key in load_index(project_dir):
            sys.stdout.write(key + "\n")
        return 0
    if args.snooze:
        index = load_index(project_dir)
        save_index(renewed(index, read_findings(), project_dir), project_dir)
        return 0
    if args.prune:
        return _prune(project_dir)
    return _write_transformed(project_dir)


def _prune(project_dir: Path) -> int:
    """Drop index keys the latest run no longer reports, and within a key it
    keeps, the anchors it no longer reports either.

    Never on an empty run: empty findings mean "nothing was measured", not
    "every exemption is obsolete", and emptying the index on that is the
    false-clean failure this tool exists to prevent. The run must be fed snooze-free
    (`habit-sensors --no-snooze`), else every still-violating key is missing
    from stdin and would be pruned away.
    """
    present = anchors_by_key(read_findings())
    index = load_index(project_dir)
    if index and not present:
        sys.stderr.write(
            "habit-snooze: --prune read no findings; refusing to empty a "
            "populated index. Nothing was measured — feed it a snooze-free run "
            "(`habit-sensors --no-snooze | habit-snooze --prune`). "
            "Index left unchanged.\n"
        )
        return 1
    kept = {key: _reported(index[key], present[key]) for key in index if key in present}
    save_index(kept, project_dir)
    return 0


def _reported(recorded: Anchors, anchors: set[str]) -> Anchors:
    return {anchor: content for anchor, content in recorded.items() if anchor in anchors}


def _write_transformed(project_dir: Path) -> int:
    """Drop snoozed findings whose anchor file no longer holds the approved content."""
    findings = read_findings()
    index = load_index(project_dir)
    sys.stdout.write(json.dumps(transform(findings, index, project_dir)) + "\n")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="habit-snooze")
    add_version_flag(parser)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--snooze", action="store_true")
    group.add_argument("--prune", action="store_true")
    group.add_argument("--list", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run_console("habit-snooze", _run_snooze_command, argv)


def _run_snooze_command(argv: list[str]) -> int:
    """A corrupt index is a failure of the tool itself — a checked-in file a human
    edits, not a statement about the code — so it exits 2 like a rejected config
    or an unresolvable ref. The `--prune` refusal is the other kind, a
    judgement about the run, and keeps exit 1.
    """
    try:
        return run(parse_args(argv), Path.cwd())
    except SnoozeError as error:
        sys.stderr.write(f"habit-snooze: {error}\n")
        return EXIT_TOOL_ERROR


if __name__ == "__main__":
    sys.exit(main())
