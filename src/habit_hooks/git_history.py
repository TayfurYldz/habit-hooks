
from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

from .argv_budget import within_argument_limits
from .git_command import git, git_output, git_succeeded
from .git_listing import untracked_paths


def places_directory(project_dir: Path) -> bool:
    return git_succeeded(project_dir, "rev-parse", "--is-inside-work-tree")


def resolves(project_dir: Path, ref: str) -> str | None:
    verified = git(project_dir, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if verified is None or verified.returncode != 0:
        return None
    return verified.stdout.strip()


def forked_at(project_dir: Path, ref: str, tip: str) -> str:
    return git_output(project_dir, "merge-base", ref, "HEAD") or tip


def head_branch(project_dir: Path) -> str:
    return git_output(project_dir, "rev-parse", "--abbrev-ref", "HEAD")


def empty_tree(project_dir: Path) -> str:
    return git_output(project_dir, "hash-object", "-t", "tree", "--stdin")


def changed_paths(
    project_dir: Path, revisions: Collection[str], pathspecs: Collection[str] = ()
) -> list[str]:
    if not pathspecs:
        return _diff_names(project_dir, revisions, ())
    return [
        path
        for batch in within_argument_limits(sorted(pathspecs))
        for path in _diff_names(project_dir, revisions, batch)
    ]


def uncommitted_changes(project_dir: Path) -> list[str]:
    staged = changed_paths(project_dir, ["--cached"])
    unstaged = changed_paths(project_dir, [])
    return list(dict.fromkeys([*staged, *unstaged, *untracked_paths(project_dir)]))


def _diff_names(
    project_dir: Path, revisions: Collection[str], pathspecs: Collection[str]
) -> list[str]:
    named = git_output(
        project_dir,
        "--literal-pathspecs",
        "diff",
        "--name-only",
        "-z",
        "--relative",
        *revisions,
        "--",
        *pathspecs,
    )
    return [path for path in named.split("\0") if path]
