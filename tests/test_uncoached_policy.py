
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks import mapper
from habit_hooks.catalogue import INCOMPLETE_RUN
from plugin_fixture import write_plugin, write_project_config

UNCOACHED_SMELL = "mystery-rule"
CATALOGUED_SMELL = "oversized-file"


def _finding(smell: str) -> dict:
    return {
        "smell": smell,
        "details": {},
        "issues": [{"key": "src/a.py", "details": {"file": "src/a.py"}}],
    }


def _project(tmp_path: Path, config: str) -> Path:
    write_plugin(tmp_path, "fixt", {"config.toml": "sensors = []"})
    write_project_config(tmp_path, f'plugins = ["fixt"]\n{config}')
    return tmp_path


def _run(tmp_path: Path, config: str, smell: str = UNCOACHED_SMELL) -> int:
    return mapper.run([_finding(smell)], _project(tmp_path, config))


def test_by_default_an_uncoached_smell_coaches_but_stays_green(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(tmp_path, "")

    assert code == 0
    assert UNCOACHED_SMELL in capsys.readouterr().out


def test_suggest_is_the_default_spelled_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(tmp_path, 'uncoached = "suggest"')

    assert code == 0
    assert UNCOACHED_SMELL in capsys.readouterr().out


def test_enforce_restores_the_blocking_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(tmp_path, 'uncoached = "enforce"')

    assert code == 1
    assert UNCOACHED_SMELL in capsys.readouterr().out


def test_ignore_drops_the_finding_entirely(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run(tmp_path, 'uncoached = "ignore"')

    out = capsys.readouterr().out
    assert code == 0
    assert UNCOACHED_SMELL not in out


_CATALOGUED_CASES = [
    (policy, smell)
    for policy in ("suggest", "ignore", "enforce")
    for smell in (CATALOGUED_SMELL, INCOMPLETE_RUN)
]


@pytest.mark.parametrize("case", _CATALOGUED_CASES, ids=str)
def test_a_catalogued_smell_is_out_of_the_policys_reach(
    case: tuple[str, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    policy, smell = case

    code = _run(tmp_path, f'uncoached = "{policy}"', smell)

    assert code == 1
    assert smell in capsys.readouterr().out


def _declaring(policy: str, severity: str) -> str:
    return f'uncoached = "{policy}"\n[smells.{UNCOACHED_SMELL}]\nseverity = "{severity}"'


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (_declaring("suggest", "enforced"), 1),
        (_declaring("enforce", "suggested"), 0),
        (_declaring("ignore", "enforced"), 1),
    ],
)
def test_a_declared_severity_wins_over_the_policy(
    config: str, expected: int, tmp_path: Path
) -> None:
    assert _run(tmp_path, config) == expected
