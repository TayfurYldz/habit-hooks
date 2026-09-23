
from __future__ import annotations

from pathlib import Path

import pytest
from pmd_ruleset import ruleset_of

BUNDLED = "pmd-ruleset.xml"
THEIRS = "mine.xml"


@pytest.mark.parametrize(
    "args",
    [
        ["--rulesets", THEIRS],
        ["--rulesets=" + THEIRS],
        ["-R", THEIRS],
        ["-R=" + THEIRS],
        ["-R" + THEIRS],
    ],
    ids=["--rulesets X", "--rulesets=X", "-R X", "-R=X", "-RX"],
)
def test_a_ruleset_named_in_args_is_the_one_pmd_gets(args: list[str]) -> None:
    ruleset, remaining = ruleset_of(args, Path("/nowhere"))

    assert ruleset == Path(THEIRS)
    assert remaining == []


def test_the_flags_around_a_ruleset_still_reach_pmd() -> None:
    ruleset, remaining = ruleset_of(
        ["--aux-classpath", "lib.jar", "-R=" + THEIRS, "--no-progress"],
        Path("/nowhere"),
    )

    assert ruleset == Path(THEIRS)
    assert remaining == ["--aux-classpath", "lib.jar", "--no-progress"]


def test_a_project_naming_none_gets_the_bundled_ruleset(tmp_path: Path) -> None:
    ruleset, remaining = ruleset_of(["--no-progress"], tmp_path)

    assert ruleset.name == BUNDLED
    assert remaining == ["--no-progress"]


def test_a_conventional_ruleset_beats_the_bundled_one(tmp_path: Path) -> None:
    theirs = tmp_path / "pmd" / "ruleset.xml"
    theirs.parent.mkdir()
    theirs.write_text("<ruleset/>", encoding="utf-8")

    assert ruleset_of([], tmp_path) == (theirs, [])


def test_a_ruleset_option_with_nothing_after_it_is_left_for_pmd_to_refuse(
    tmp_path: Path,
) -> None:
    ruleset, remaining = ruleset_of(["-R"], tmp_path)

    assert ruleset.name == BUNDLED
    assert remaining == ["-R"]
