
from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks.snooze import load_index, parse_args, run
from habit_hooks.snooze_lapse import anchor_file, content_hash, renewed
from snooze_project import a_project_with, aliased, feed_stdin, finding, snooze


def test_snooze_records_the_anchor_files_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert load_index(tmp_path) == {
        "src/x.ts": {"src/x.ts": content_hash(tmp_path / "src/x.ts")}
    }


def test_an_edit_changes_the_recorded_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    snooze(tmp_path, monkeypatch, [finding("SomeExportedName")])
    assert load_index(tmp_path) == {"SomeExportedName": {}}


@pytest.mark.parametrize("file", [None, 5, ""], ids=["null", "a number", "empty"])
def test_a_details_file_that_is_no_path_falls_back_to_the_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, file: object
) -> None:
    issue = {"key": "k", "details": {"file": file}}
    assert anchor_file(issue) == "k"

    snooze(tmp_path, monkeypatch, [{"smell": "s", "details": {}, "issues": [issue]}])
    assert load_index(tmp_path) == {"k": {}}


def test_an_unreadable_anchor_keeps_what_was_recorded_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    recorded = load_index(tmp_path)["src/x.ts"]

    (tmp_path / "src/x.ts").unlink()
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert load_index(tmp_path)["src/x.ts"] == recorded


def test_the_recorded_content_ignores_a_crlf_line_ending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    crlf = a_project_with(tmp_path / "crlf", "x.ts", "const a = 1;\r\nconst b = 2;\r\n")
    lf = a_project_with(tmp_path / "lf", "x.ts", "const a = 1;\nconst b = 2;\n")

    snooze(crlf, monkeypatch, [finding("x.ts", "x.ts")])
    snooze(lf, monkeypatch, [finding("x.ts", "x.ts")])

    assert load_index(crlf) == load_index(lf)


def test_a_lone_carriage_return_is_content_and_not_a_line_ending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cr = a_project_with(tmp_path / "cr", "x.ts", "const a = 1;\rconst b = 2;\r")
    lf = a_project_with(tmp_path / "lf", "x.ts", "const a = 1;\nconst b = 2;\n")

    snooze(cr, monkeypatch, [finding("x.ts", "x.ts")])
    snooze(lf, monkeypatch, [finding("x.ts", "x.ts")])

    assert load_index(cr) != load_index(lf)


def test_a_key_reported_under_several_files_records_each_of_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")

    snooze(tmp_path, monkeypatch, aliased("src/a.py", "src/b.py"))

    assert load_index(tmp_path) == {
        "requests": {
            "src/a.py": content_hash(tmp_path / "src/a.py"),
            "src/b.py": content_hash(tmp_path / "src/b.py"),
        }
    }


def test_an_anchor_the_run_does_not_report_keeps_what_it_recorded(tmp_path: Path) -> None:
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")
    both = renewed({}, aliased("src/a.py", "src/b.py"), tmp_path)

    assert renewed(both, aliased("src/a.py"), tmp_path) == both


def test_prune_keeps_the_recordings_of_a_key_it_keeps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/x.ts", "export const a = 1;\n")
    snooze(tmp_path, monkeypatch, [finding("src/x.ts", "src/x.ts")])
    recorded = load_index(tmp_path)["src/x.ts"]

    feed_stdin(monkeypatch, [finding("src/x.ts", "src/x.ts")])
    assert run(parse_args(["--prune"]), tmp_path) == 0
    assert load_index(tmp_path) == {"src/x.ts": recorded}


def test_prune_drops_an_anchor_the_run_no_longer_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a_project_with(tmp_path, "src/a.py", "import requests\n")
    a_project_with(tmp_path, "src/b.py", "import requests\nrequests.get()\n")
    snooze(tmp_path, monkeypatch, aliased("src/a.py", "src/b.py"))

    feed_stdin(monkeypatch, aliased("src/b.py"))
    assert run(parse_args(["--prune"]), tmp_path) == 0
    assert load_index(tmp_path) == {
        "requests": {"src/b.py": content_hash(tmp_path / "src/b.py")}
    }
