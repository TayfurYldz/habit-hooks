
from __future__ import annotations

from pathlib import Path

import pytest

from git_repo import git, repository, repository_with_committed_file
from habit_hooks import git_command, git_history

_UNRESOLVABLE_HEAD = ("rev-parse", "--abbrev-ref", "HEAD")


def test_a_failing_git_answers_nothing_even_when_it_printed_something(
    tmp_path: Path,
) -> None:
    repository(tmp_path)
    printed = git_command.git(tmp_path, *_UNRESOLVABLE_HEAD)

    assert printed is not None
    assert printed.returncode != 0
    assert printed.stdout.strip() == "HEAD"  # the situation under test
    assert git_command.git_output(tmp_path, *_UNRESOLVABLE_HEAD) == ""


def test_a_repository_with_no_commits_is_on_no_branch(tmp_path: Path) -> None:
    repository(tmp_path)
    assert git_history.head_branch(tmp_path) == ""


def test_a_successful_git_answers_with_what_it_printed(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    assert git_history.head_branch(tmp_path) == "main"


def test_a_detached_head_keeps_gits_own_word_for_it(tmp_path: Path) -> None:
    repository_with_committed_file(tmp_path)
    git(tmp_path, "checkout", "-q", "--detach")
    assert git_history.head_branch(tmp_path) == "HEAD"


def test_git_that_cannot_be_run_at_all_answers_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    def no_git(*_args: object, **_options: object) -> object:
        raise OSError("git: command not found")

    monkeypatch.setattr(git_command.subprocess, "run", no_git)
    assert git_command.git(tmp_path, "status") is None
    assert git_command.git_output(tmp_path, "status") == ""
