
from __future__ import annotations

from pathlib import Path

from sensor_notice import script_notice

import pytest

from habit_hooks.sensors import diagnosis
from habit_hooks.sensors.diagnosis import (
    DIAGNOSIS_LINE_LIMIT,
    DIAGNOSIS_LINE_LENGTH_LIMIT,
    keep_both_ends,
)


def test_a_sensor_at_the_truncation_boundary_is_still_quoted_whole(
    tmp_path: Path,
) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        "for i in range(1, 22):\n"
        "    print(f'line {i}', file=sys.stderr)\n"
        "sys.exit(1)\n",
    )
    lines = notice.splitlines()

    assert "line 1" in lines
    assert "line 21" in lines
    assert "omitted" not in notice


def test_a_sensor_one_line_past_the_boundary_finally_elides(tmp_path: Path) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        "for i in range(1, 23):\n"
        "    print(f'line {i}', file=sys.stderr)\n"
        "sys.exit(1)\n",
    )
    lines = notice.splitlines()

    assert "line 1" in lines
    assert "line 11" not in lines
    assert "line 22" in lines
    assert "... 2 lines omitted ..." in lines


def test_a_sensor_whose_last_line_carries_the_diagnosis_still_quotes_it(
    tmp_path: Path,
) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        "for i in range(1, 25):\n"
        '    print(f"noise {i}", file=sys.stderr)\n'
        'raise RuntimeError("boom: the real reason")\n',
    )

    assert "boom: the real reason" in notice


def test_a_sensor_that_says_it_all_on_one_line_is_still_cut_down(
    tmp_path: Path,
) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        "print('S' * 2_000_000 + 'THE REAL COMPLAINT', file=sys.stderr)\n"
        "sys.exit(1)\n",
    )

    assert len(notice) < 10_000, f"notice carried {len(notice)} characters"
    assert "THE REAL COMPLAINT" in notice, "the end of the line is the punchline"
    assert "omitted" in notice, "and it says the middle was dropped"


def test_a_line_exactly_at_its_budget_is_quoted_whole(tmp_path: Path) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        f"print('S' * {DIAGNOSIS_LINE_LENGTH_LIMIT}, file=sys.stderr)\n"
        "sys.exit(1)\n",
    )

    assert "S" * DIAGNOSIS_LINE_LENGTH_LIMIT in notice
    assert "omitted" not in notice


def test_cutting_a_line_never_makes_it_longer() -> None:
    over = range(DIAGNOSIS_LINE_LENGTH_LIMIT, DIAGNOSIS_LINE_LENGTH_LIMIT + 100)

    for length in over:
        quoted = keep_both_ends("x" * length)
        assert len(quoted) <= length, f"{length} characters came back as {len(quoted)}"


def test_a_line_far_past_its_budget_keeps_both_of_its_ends() -> None:
    quoted = keep_both_ends("HEAD" + "x" * 5_000 + "TAIL")

    assert quoted.startswith("HEAD")
    assert quoted.endswith("TAIL")
    assert "characters omitted" in quoted
    assert len(quoted) < 1_100


def test_only_the_lines_that_survive_are_cut_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cut = diagnosis._both_ends_of
    seen = []
    monkeypatch.setattr(
        diagnosis, "_both_ends_of", lambda line: seen.append(line) or cut(line)
    )

    diagnosis.keep_both_ends("\n".join("x" * 2_000 for _ in range(10_000)))

    assert len(seen) <= DIAGNOSIS_LINE_LIMIT + 1, f"cut {len(seen)} lines down"
