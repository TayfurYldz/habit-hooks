
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import git, repository_with_committed_file
from habit_hooks.config import Config, ScopeDefaults
from scope_probe import scoped_files


def _feature_branch_with_an_untracked_file(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    git(tmp_path, "checkout", "-q", "-b", "feature")
    (tmp_path / "new.py").write_text("VALUES = [1, 2, 3]\n", encoding="utf-8")


_PY = Config(files=["**/*.py"])


@pytest.mark.parametrize(
    ("argv", "config"),
    [
        (["--branch", "main"], _PY),
        (["--last", "1"], _PY),
        (["--since", "main"], _PY),
        ([], Config(files=["**/*.py"], scope=ScopeDefaults(autoBranchOffMain=True))),
    ],
)
def test_a_git_derived_scope_measures_an_untracked_file(
    argv: list[str], config: Config | None, tmp_path: Path
) -> None:
    _feature_branch_with_an_untracked_file(tmp_path)
    assert "new.py" in scoped_files(argv, tmp_path, config)


def test_changed_only_measures_a_staged_file(tmp_path: Path) -> None:
    committed = repository_with_committed_file(tmp_path)
    committed.write_text("VALUES = [1, 2]\n", encoding="utf-8")
    git(tmp_path, "add", "src.py")
    config = Config(files=["**/*.py"], scope=ScopeDefaults(changedOnly=True))
    assert scoped_files([], tmp_path, config) == ["src.py"]


def test_a_gitignored_untracked_file_is_not_measured(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    git(tmp_path, "checkout", "-q", "-b", "feature")
    (tmp_path / ".gitignore").write_text("build.py\n", encoding="utf-8")
    (tmp_path / "build.py").write_text("VALUES = [9]\n", encoding="utf-8")
    config = Config(files=["**/*.py"])
    assert "build.py" not in scoped_files(["--branch", "main"], tmp_path, config)
