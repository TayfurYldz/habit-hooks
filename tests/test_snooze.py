"""Unit tests for the snooze command: the transform, what `--snooze` records,
and what keeps an issue dropped.

The executable spec ([habit-snooze.spec.md]) covers the command end to end;
these pin the pieces a spec case cannot show directly. The index file itself,
and the commands that maintain it, live in ``test_snooze_index.py``.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from habit_hooks import sensors
from habit_hooks import snooze_lapse
from habit_hooks.snooze import load_index, parse_args, run, transform
from habit_hooks.snooze_lapse import anchor_file, holds

_FINDING = {
    "smell": "oversized-file",
    "details": {"maxAllowed": 200},
    "issues": [
        {"key": "src/x.ts", "details": {"file": "src/x.ts"}},
        {"key": "requests", "details": {"file": "src/y.py"}},
    ],
}


def a_project_with(project_dir: Path, name: str, text: str) -> Path:
    path = project_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return project_dir


def feed_stdin(monkeypatch: pytest.MonkeyPatch, findings: object) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(findings)))


def finding(key: str, file: str | None = None) -> dict:
    details = {"file": file} if file is not None else {}
    return {
        "smell": "oversized-file",
        "details": {"maxAllowed": 200},
        "issues": [{"key": key, "details": details}],
    }


def aliased(*files: str) -> list[dict]:
    """One key over several files — see ``anchor_file`` for when a sensor reports that."""
    return [
        {
            "smell": "unused-dependency",
            "details": {},
            "issues": [{"key": "requests", "details": {"file": f}} for f in files],
        }
    ]


def snooze(project_dir: Path, monkeypatch: pytest.MonkeyPatch, findings: list) -> None:
    feed_stdin(monkeypatch, findings)
    assert run(parse_args(["--snooze"]), project_dir) == 0


# --- the transform ---


def test_anchor_prefers_the_details_file() -> None:
    issue = {"key": "requests", "details": {"file": "src/y.py"}}
    assert anchor_file(issue) == "src/y.py"


def test_anchor_falls_back_to_the_key_without_a_file() -> None:
    assert anchor_file({"key": "src/x.ts", "details": {"line": 3}}) == "src/x.ts"


def test_anchor_falls_back_to_the_key_without_details() -> None:
    assert anchor_file({"key": "src/x.ts"}) == "src/x.ts"


def test_an_entry_recording_nothing_drops_every_snoozed_issue(tmp_path: Path) -> None:
    kept = transform([_FINDING], {"src/x.ts": {}, "requests": {}}, tmp_path)
    assert kept == []


def test_a_changed_file_resurfaces_only_its_own_issue(tmp_path: Path) -> None:
    """The file was approved at one content and now holds another, so its issue
    is due again — while a key still holding its approved content stays dropped."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src/y.py").write_text("import requests\n", encoding="utf-8")
    index = {"src/x.ts": {"src/x.ts": "sha256:lapsed"}, "requests": {}}
    kept = transform([_FINDING], index, tmp_path)
    assert [issue["key"] for issue in kept[0]["issues"]] == ["src/x.ts"]


def test_an_issue_whose_key_is_not_snoozed_is_never_dropped(tmp_path: Path) -> None:
    kept = transform([_FINDING], {}, tmp_path)
    assert [issue["key"] for issue in kept[0]["issues"]] == ["src/x.ts", "requests"]


def test_a_finding_without_issues_passes_through(tmp_path: Path) -> None:
    empty = {"smell": "duplicated-code", "details": {}, "issues": []}
    assert transform([empty], {"src/x.ts": {}}, tmp_path) == [empty]


def test_file_run_bypasses_the_snooze_transformer(tmp_path: Path) -> None:
    """`--file` asks for one file's full picture, so its snooze exemption — a
    statement about the backlog, not that file — is stripped from the run (#55)."""
    config = sensors._configure(sensors.parse_args(["--file", "src/x.ts"]), tmp_path)
    assert "snooze" not in config.transformers


def test_all_run_keeps_the_snooze_transformer(tmp_path: Path) -> None:
    """The bypass is `--file` only: `--all` still filters through the index."""
    config = sensors._configure(sensors.parse_args(["--all"]), tmp_path)
    assert config.transformers == ["snooze"]


def test_file_run_keeps_a_projects_non_snooze_transformer(tmp_path: Path) -> None:
    """Only snoozing is bypassed — a project's unrelated transformer still runs,
    so `--file` does not silently drop a step it never asked about (#55)."""
    config_dir = tmp_path / ".habit-hooks"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text('transformers = ["snooze", "squash"]\n', encoding="utf-8")
    config = sensors._configure(sensors.parse_args(["--file", "src/x.ts"]), tmp_path)
    assert config.transformers == ["squash"]


# --- what --snooze records ---


def test_snooze_records_the_anchor_files_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert load_index(tmp_path) == {
        "src/x.ts": {"src/x.ts": snooze_lapse.content_hash(tmp_path / "src/x.ts")}
    }


def test_an_edit_changes_the_recorded_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole point of recording it: a later edit is a different answer."""
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    before = load_index(tmp_path)["src/x.ts"]

    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\nexport const b = 2;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert load_index(tmp_path)["src/x.ts"] != before


def test_snoozing_again_replaces_the_entry_rather_than_adding_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    a_project_with(tmp_path, "src/x.ts", "export const a = 2;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert list(load_index(tmp_path)) == ["src/x.ts"]


def test_an_anchor_that_is_no_file_records_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sensor may key by module or export name; there is nothing to record,
    and the entry keeps the behaviour it had rather than failing the run."""
    snooze(tmp_path, monkeypatch, [finding("SomeExportedName")])
    assert load_index(tmp_path) == {"SomeExportedName": {}}


@pytest.mark.parametrize("file", [None, 5, ""], ids=["null", "a number", "empty"])
def test_a_details_file_that_is_no_path_falls_back_to_the_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, file: object
) -> None:
    """`sensors.finding_paths` reads a `file` that is not a non-empty string as
    absent, so one reaches here; recording opens the anchor as a path, and
    reading it any other way turns a tolerated finding into a traceback."""
    issue = {"key": "k", "details": {"file": file}}
    assert anchor_file(issue) == "k"

    snooze(tmp_path, monkeypatch, [{"smell": "s", "details": {}, "issues": [issue]}])
    assert load_index(tmp_path) == {"k": {}}


def test_an_unreadable_anchor_keeps_what_was_recorded_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file briefly unreadable is not an answer. Replacing an approval with
    nothing would lapse it on the next run for a reason nobody chose."""
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    recorded = load_index(tmp_path)["src/x.ts"]

    (tmp_path / "src/x.ts").unlink()
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert load_index(tmp_path)["src/x.ts"] == recorded


def test_the_recorded_content_ignores_a_crlf_line_ending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`snooze.json` is checked in and shared; hashing raw bytes would lapse a
    Windows developer's approval the moment Linux CI read it."""
    crlf = a_project_with(tmp_path / "crlf", "x.ts", "const a = 1;\r\nconst b = 2;\r\n")
    lf = a_project_with(tmp_path / "lf", "x.ts", "const a = 1;\nconst b = 2;\n")

    snooze(crlf, monkeypatch, [finding("x.ts", "x.ts")])
    snooze(lf, monkeypatch, [finding("x.ts", "x.ts")])

    assert load_index(crlf) == load_index(lf)


def test_a_lone_carriage_return_is_content_and_not_a_line_ending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rule forgives a line ending, not any byte resembling one: forgiving a
    lone `\\r` would forgive an edit every checkout agrees is an edit."""
    cr = a_project_with(tmp_path / "cr", "x.ts", "const a = 1;\rconst b = 2;\r")
    lf = a_project_with(tmp_path / "lf", "x.ts", "const a = 1;\nconst b = 2;\n")

    snooze(cr, monkeypatch, [finding("x.ts", "x.ts")])
    snooze(lf, monkeypatch, [finding("x.ts", "x.ts")])

    assert load_index(cr) != load_index(lf)


def test_a_key_reported_under_several_files_records_each_of_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A key is not always one file. One content could only describe one of
    them, and which one would come down to the order the sensor listed them in."""
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")

    snooze(tmp_path, monkeypatch, aliased("src/a.py", "src/b.py"))

    assert load_index(tmp_path) == {
        "requests": {
            "src/a.py": snooze_lapse.content_hash(tmp_path / "src/a.py"),
            "src/b.py": snooze_lapse.content_hash(tmp_path / "src/b.py"),
        }
    }


def test_an_anchor_the_run_does_not_report_keeps_what_it_recorded(tmp_path: Path) -> None:
    """A run narrowed to one file measures nothing about the others an entry
    covers, and a snooze must not lapse because of a question nobody asked.
    `--prune` is where an anchor that is really gone is dropped."""
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")
    both = snooze_lapse.renewed({}, aliased("src/a.py", "src/b.py"), tmp_path)

    assert snooze_lapse.renewed(both, aliased("src/a.py"), tmp_path) == both


def test_list_prints_bare_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--list` shows what is snoozed, not the bookkeeping that decides for how
    long."""
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert run(parse_args(["--list"]), tmp_path) == 0
    assert capsys.readouterr().out == "src/x.ts\n"


# --- which snoozes a recorded content covers ---


def test_an_entry_that_records_nothing_holds_without_reading_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every hook run asks this, so it must not hash a file to learn that an
    entry written before recording has nothing to compare."""
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    monkeypatch.setattr(
        snooze_lapse,
        "content_hash",
        lambda path: pytest.fail(f"hashed {path} with nothing recorded"),
    )
    assert holds({}, "src/x.ts", tmp_path)


def test_an_approval_covers_only_the_file_it_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run reports one key through two files and only one was approved, so
    only that one is spared."""
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")
    snooze(tmp_path, monkeypatch, aliased("src/b.py"))

    index = load_index(tmp_path)
    assert holds(index["requests"], "src/b.py", tmp_path)
    assert not holds(index["requests"], "src/a.py", tmp_path)


def test_a_file_that_only_now_reports_a_key_is_not_covered_by_another(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The entry was approved while one file reported the key. A second file
    picking the smell up later is new debt, and surfacing it is the point."""
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    snooze(tmp_path, monkeypatch, aliased("src/a.py"))

    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")
    index = load_index(tmp_path)
    assert holds(index["requests"], "src/a.py", tmp_path)
    assert not holds(index["requests"], "src/b.py", tmp_path)
