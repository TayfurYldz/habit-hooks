
from __future__ import annotations

import pathspec


def matching(paths: list[str], globs: list[str]) -> list[str]:
    spec = pathspec.PathSpec.from_lines("gitignore", globs)
    return [path for path in paths if spec.match_file(path)]
