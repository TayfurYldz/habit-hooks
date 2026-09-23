
from __future__ import annotations

from pathlib import Path

from . import git_listing


def files_in(project_dir: Path) -> list[str]:
    return sorted(_files_git_keeps(project_dir) or _files_on_disk(project_dir))


def _files_git_keeps(project_dir: Path) -> list[str]:
    if git_listing.ignores_directory(project_dir):
        return []
    return git_listing.project_files(project_dir)


def _files_on_disk(project_dir: Path) -> list[str]:
    return [
        path.relative_to(project_dir).as_posix()
        for path in project_dir.rglob("*")
        if path.is_file()
    ]
