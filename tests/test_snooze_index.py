
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from habit_hooks.cli import EXIT_TOOL_ERROR
from habit_hooks.snooze import (
    INDEX_PATH,
    SnoozeError,
    load_index,
    main,
    parse_args,
    run,
    save_index,
)


def _write_index(project_dir: Path, content: str) -> Path:
    path = project_dir / INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _feed_stdin(monkeypatch: pytest.MonkeyPatch, findings: object) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(findings)))


def _finding(*keys: str) -> dict:
    return {
        "smell": "loose-equality",
        "details": {},
        "issues": [{"key": key, "details": {"file": key}} for key in keys],
    }


def test_prune_drops_a_key_that_no_longer_appears(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_index(tmp_path, json.dumps(["src/x.ts", "src/y.ts"]))
    _feed_stdin(monkeypatch, [_finding("src/x.ts")])
    assert run(parse_args(["--prune"]), tmp_path) == 0
    assert load_index(tmp_path) == {"src/x.ts": {}}


def test_prune_refuses_to_empty_a_populated_index_on_no_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_index(tmp_path, json.dumps(["src/x.ts", "src/y.ts"]))
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert run(parse_args(["--prune"]), tmp_path) == 1
    assert load_index(tmp_path) == {"src/x.ts": {}, "src/y.ts": {}}
    assert "prune" in capsys.readouterr().err.lower()


def test_prune_still_clears_an_index_it_was_asked_to_when_findings_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_index(tmp_path, json.dumps(["src/x.ts"]))
    _feed_stdin(monkeypatch, [_finding("src/other.ts")])
    assert run(parse_args(["--prune"]), tmp_path) == 0
    assert load_index(tmp_path) == {}


@pytest.mark.parametrize(
    ("content", "why"),
    [
        ("not json", "invalid JSON"),
        ("null", "JSON null"),
        ('"src/a.py"', "a bare string"),
        ('{"src/a.py": "why"}', "an object"),
    ],
)
def test_a_malformed_index_fails_by_name(
    tmp_path: Path, content: str, why: str
) -> None:
    path = _write_index(tmp_path, content)
    with pytest.raises(SnoozeError) as excinfo:
        load_index(tmp_path)
    assert str(path) in str(excinfo.value), why


@pytest.mark.parametrize("index_op", ["--list", "--snooze", "--prune"])
def test_a_corrupt_index_fails_as_a_tool_error(
    index_op: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_index(tmp_path, "not json")
    _feed_stdin(monkeypatch, [])
    monkeypatch.chdir(tmp_path)
    assert main([index_op]) == EXIT_TOOL_ERROR


def test_an_index_of_bare_keys_still_loads(tmp_path: Path) -> None:
    _write_index(tmp_path, json.dumps(["src/x.ts", "src/y.ts"]))
    assert load_index(tmp_path) == {"src/x.ts": {}, "src/y.ts": {}}


def test_an_index_mixing_both_shapes_loads(tmp_path: Path) -> None:
    recorded = {"key": "src/y.ts", "anchors": {"src/y.ts": "sha256:abc"}}
    _write_index(tmp_path, json.dumps(["src/x.ts", recorded]))
    assert load_index(tmp_path) == {
        "src/x.ts": {},
        "src/y.ts": {"src/y.ts": "sha256:abc"},
    }


def test_an_entry_with_a_field_the_index_cannot_mean_fails_by_name(tmp_path: Path) -> None:
    _write_index(tmp_path, json.dumps([{"key": "src/a.py", "reason": "we discussed it"}]))
    with pytest.raises(SnoozeError) as excinfo:
        load_index(tmp_path)
    assert "expected each entry" in str(excinfo.value)


def test_an_entry_recording_nothing_is_written_as_a_bare_key(tmp_path: Path) -> None:
    save_index({"src/x.ts": {}, "src/y.ts": {"src/y.ts": "sha256:abc"}}, tmp_path)
    assert json.loads((tmp_path / INDEX_PATH).read_text(encoding="utf-8")) == [
        "src/x.ts",
        {"key": "src/y.ts", "anchors": {"src/y.ts": "sha256:abc"}},
    ]


def test_save_index_writes_atomically_leaving_no_temp_files(tmp_path: Path) -> None:
    save_index({"src/x.ts": {}}, tmp_path)
    index_dir = tmp_path / INDEX_PATH.parent
    assert [p.name for p in index_dir.iterdir()] == ["snooze.json"]
    assert load_index(tmp_path) == {"src/x.ts": {}}


def test_list_prints_bare_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from snooze_project import a_project_with, finding, snooze

    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert run(parse_args(["--list"]), tmp_path) == 0
    assert capsys.readouterr().out == "src/x.ts\n"
