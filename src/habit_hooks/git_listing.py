
from __future__ import annotations

from pathlib import Path

from .git_command import git_output, git_succeeded

_GITLINK_MODE = "160000 "


def ignores_directory(project_dir: Path) -> bool:
    if _is_a_repository_root(project_dir):
        return False
    return git_succeeded(
        project_dir, "check-ignore", "--no-index", "--quiet", "--", str(project_dir)
    )


def _is_a_repository_root(project_dir: Path) -> bool:
    top = git_output(project_dir, "rev-parse", "--show-toplevel")
    return bool(top) and Path(top).resolve() == project_dir.resolve()


def project_files(project_dir: Path) -> list[str]:
    return _listed_files(project_dir, "--cached", "--others")


def untracked_paths(project_dir: Path) -> list[str]:
    return _listed_files(project_dir, "--others")


def submodule_paths(project_dir: Path) -> list[str]:
    listed = git_output(project_dir, "ls-files", "--stage", "-z")
    return [
        entry.split("\t", 1)[1]
        for entry in listed.split("\0")
        if entry.startswith(_GITLINK_MODE) and "\t" in entry
    ]


def _listed_files(project_dir: Path, *selectors: str) -> list[str]:
    named = git_output(
        project_dir, "ls-files", *selectors, "--exclude-standard", "-z"
    )
    return [path for path in named.split("\0") if path]
