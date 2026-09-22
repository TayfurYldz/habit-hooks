"""The ``${files:comma}`` placeholder: one joined argument, still chunked."""

from __future__ import annotations

import pytest
from pathlib import Path
from platform_probe import on_windows

from test_argv_parts import _argv

from habit_hooks.sensors.chunking import chunked_commands
from habit_hooks.sensors.model import Part


def test_a_comma_joined_file_list_is_one_argument(tmp_path: Path) -> None:
    """``${files:comma}`` is the one sanctioned joined spelling: a tool whose
    own format takes the files as one comma-separated list (phpmd's phar) gets
    exactly that — zero files honestly join to the empty string, one file is
    itself, many are joined — and unlike ``${files}`` it may sit inside a
    larger element, because the join is the point of the spelling."""
    part = Part(name="phpmd", directory=tmp_path, argv=["phpmd", "${files:comma}", "json"])
    flag = Part(name="probe", directory=tmp_path, argv=["probe", "--paths=${files:comma}"])

    assert _argv(part, []) == ["phpmd", "", "json"]
    assert _argv(part, ["src/a.php"]) == ["phpmd", "src/a.php", "json"]
    assert _argv(part, ["src/a.php", "src/b.php"]) == [
        "phpmd",
        "src/a.php,src/b.php",
        "json",
    ]
    assert _argv(flag, ["src/a.php", "src/b.php"]) == [
        "probe",
        "--paths=src/a.php,src/b.php",
    ]


def test_a_filename_with_placeholder_text_reaches_a_joined_list_intact(
    tmp_path: Path,
) -> None:
    """The join is spliced last: a scope filename is data, never re-read as
    a recipe, however placeholder-shaped its name."""
    part = Part(name="phpmd", directory=tmp_path, argv=["phpmd", "${files:comma}"])

    assert _argv(part, ["evil${dir}x.php", "b.php"]) == [
        "phpmd",
        "evil${dir}x.php,b.php",
    ]


def test_a_comma_joined_list_is_chunked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One argument or many, a scope-sized list still has to fit one spawn."""
    on_windows(monkeypatch)
    part = Part(name="phpmd", directory=tmp_path, argv=["phpmd", "${files:comma}"])

    argvs = chunked_commands(part, ["a" * 15_000, "b" * 6_000], lambda files: _argv(part, files))

    assert len(argvs) == 2
