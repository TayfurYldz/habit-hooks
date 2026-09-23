
from __future__ import annotations

from pathlib import Path

from . import git_listing
from .config import Config
from .path_globs import matching
from .project_paths import project_relative

_NO_FILES = "no [files] are configured — name what to scan in .habit-hooks/config.toml"
NO_FILES_NOTICE = f"habit-sensors: {_NO_FILES}; nothing scanned"

NOTHING_MATCHED_NOTICE = (
    "habit-sensors: nothing matched [files] — check it in "
    ".habit-hooks/config.toml, and whether git ignores the paths you expected; "
    "nothing scanned"
)


def empty_scope_notices(
    named: str | None, project_dir: Path, config: Config
) -> list[str]:
    if named is not None:
        return [_named_file_notice(named, project_dir, config)]
    return [NO_FILES_NOTICE if config.files is None else NOTHING_MATCHED_NOTICE]


def submodule_notices(placed: list[str], config: Config, project_dir: Path) -> list[str]:
    if not config.files:
        return []
    picked = set(placed)
    return [
        f"habit-sensors: {path} is a submodule; its files are scanned in "
        "their own repository"
        for path in git_listing.submodule_paths(project_dir)
        if path in picked and _held_source_this_run_wanted(path, config, project_dir)
    ]


def _held_source_this_run_wanted(
    submodule: str, config: Config, project_dir: Path
) -> bool:
    held = git_listing.project_files(project_dir / submodule)
    return bool(matching([f"{submodule}/{path}" for path in held], config.files or []))


def _named_file_notice(named: str, project_dir: Path, config: Config) -> str:
    placed = project_relative(named, project_dir)
    if placed is None or not (project_dir / placed).is_file():
        reason = " is not a file in this project"
    elif config.files is None:
        reason = f": {_NO_FILES}"
    else:
        reason = " is outside [files]"
    return f"habit-sensors: --file {named!r}{reason}; nothing scanned"
