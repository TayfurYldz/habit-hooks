
from __future__ import annotations

from pathlib import Path

from .parser import SpecCase
from .steps import Context


def execute(test: SpecCase, workdir: Path, repo_root: Path) -> None:
    context = Context(workdir, repo_root)
    for step in test.steps:
        step.apply(context)
    context.check_default_exit()
