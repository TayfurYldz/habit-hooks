
from __future__ import annotations

import os
import shutil
from pathlib import Path, PurePath

from . import host_platform


def project_relative(raw: str, project_dir: Path) -> str | None:
    absolute = os.path.normpath(os.path.join(project_dir, raw))
    return _under(absolute, str(project_dir)) or _under(
        os.path.realpath(absolute), os.path.realpath(project_dir)
    )


def venv_bin_dir(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts" if host_platform.is_windows() else "bin")


def venv_executable(venv_dir: Path, name: str) -> Path:
    suffix = ".exe" if host_platform.is_windows() else ""
    return venv_bin_dir(venv_dir) / f"{name}{suffix}"


def tool_search_path(project_dir: Path) -> str:
    node = project_dir / "node_modules" / ".bin"
    venv = venv_bin_dir(project_dir / ".venv")
    return os.pathsep.join([str(node), str(venv), os.environ.get("PATH", "")])


def tool_executable(
    name: str, project_dir: Path, search_paths: tuple[str, ...] = ()
) -> str | None:
    named = [str(project_dir / relative) for relative in search_paths]
    search = os.pathsep.join([*named, tool_search_path(project_dir)])
    found = shutil.which(name, path=search)
    return None if found is None else os.path.abspath(found)


def _under(target: str, root: str) -> str | None:
    relative = os.path.relpath(target, root)
    outside = relative == os.pardir or relative.startswith(os.pardir + os.sep)
    return None if outside or relative == os.curdir else PurePath(relative).as_posix()
