
from __future__ import annotations

from pathlib import Path

import pytest
from habit_hooks import mapper
from finding import a_finding, an_issue
from plugin_fixture import write_plugin, write_project_config

OVERSIZED_FILE_GUIDE = "Split the file along its seams."
OVERSIZED_FUNCTION_GUIDE = "Extract the steps this function names."
LISTING = "{% for issue in issues %}{{ issue.details.file }}\n{% endfor %}"


PYTHON_COMPLEXITY_GUIDE = "Split the branches this Python function is holding."
GENERIC_COMPLEXITY_GUIDE = "Split the branches this function is holding."


def _project(tmp_path: Path) -> Path:
    write_plugin(
        tmp_path,
        "gen",
        {
            "config.toml": "sensors = []",
            "guides/oversized-file.md": f"{OVERSIZED_FILE_GUIDE}\n\n{LISTING}",
            "guides/oversized-function.md": f"{OVERSIZED_FUNCTION_GUIDE}\n\n{LISTING}",
            "guides/high-complexity.md": f"{GENERIC_COMPLEXITY_GUIDE}\n\n{LISTING}",
        },
    )
    write_plugin(
        tmp_path,
        "py",
        {
            "config.toml": 'language = "python"\nsensors = []',
            "guides/high-complexity.md": f"{PYTHON_COMPLEXITY_GUIDE}\n\n{LISTING}",
        },
    )
    write_project_config(tmp_path, 'plugins = ["gen", "py"]')
    return tmp_path


def test_two_sensors_reporting_one_smell_print_its_guide_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from_eslint = a_finding(
        "oversized-file",
        [an_issue("src/big.ts", message="File has too many lines", source="eslint:max-lines")],
    )
    from_line_count = a_finding(
        "oversized-file", [an_issue("src/big.ts", lines=260, source="line-count")]
    )

    mapper.run([from_eslint, from_line_count], _project(tmp_path))

    assert capsys.readouterr().out.count(OVERSIZED_FILE_GUIDE) == 1


def test_one_file_two_sensors_saw_is_one_issue_to_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from_eslint = a_finding("oversized-file", [an_issue("src/big.ts", line=None)])
    from_line_count = a_finding("oversized-file", [an_issue("src/big.ts", lines=260)])

    mapper.run([from_eslint, from_line_count], _project(tmp_path))

    out = capsys.readouterr().out
    assert out.count("── oversized-file (1 issue) ──") == 1
    assert "(2 issues)" not in out


def test_every_oversized_function_in_one_file_is_still_its_own_issue(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    issues = [an_issue("src/big.ts", line=line) for line in (3, 40, 80, 120, 160, 200, 240)]

    mapper.run([a_finding("oversized-function", issues)], _project(tmp_path))

    assert "── oversized-function (7 issues) ──" in capsys.readouterr().out


def test_different_smells_keep_their_own_blocks_in_arrival_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = [
        a_finding("oversized-function", [an_issue("src/a.ts", line=3)]),
        a_finding("oversized-file", [an_issue("src/b.ts")]),
    ]

    mapper.run(findings, _project(tmp_path))

    out = capsys.readouterr().out
    assert out.index("oversized-function") < out.index("oversized-file")


def test_one_smell_two_plugins_coach_differently_stays_two_blocks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = [
        a_finding("high-complexity", [an_issue("src/a.py", line=12)], language="python"),
        a_finding("high-complexity", [an_issue("src/b.ts", line=40)], language="typescript"),
    ]

    mapper.run(findings, _project(tmp_path))

    out = capsys.readouterr().out
    assert out.count("── high-complexity (1 issue) ──") == 2
    assert PYTHON_COMPLEXITY_GUIDE in out
    assert GENERIC_COMPLEXITY_GUIDE in out


def test_each_file_is_listed_under_the_guide_that_coaches_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings = [
        a_finding("high-complexity", [an_issue("src/a.py", line=12)], language="python"),
        a_finding("high-complexity", [an_issue("src/b.ts", line=40)], language="typescript"),
    ]

    mapper.run(findings, _project(tmp_path))

    python_block, generic_block = capsys.readouterr().out.split(GENERIC_COMPLEXITY_GUIDE)
    assert "src/a.py" in python_block
    assert "src/b.ts" in generic_block
    assert "src/b.ts" not in python_block
