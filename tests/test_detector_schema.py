
from __future__ import annotations

from pathlib import Path

from detector_config import declaring, refusal_for
from plugin_fixture import write_project_config

COMPLETE = '{ name = "ruff", kind = "command", install = "pip install ruff" }'


def _detectors(tmp_path: Path, *entries: str) -> Path:
    return declaring(tmp_path, f"detectors = [{', '.join(entries)}]")


def test_a_detectors_key_that_is_not_a_list_names_the_plugin_config(
    tmp_path: Path,
) -> None:
    message = refusal_for(declaring(tmp_path, "detectors = 42"))

    assert "'detectors'" in message
    assert "the 'alpha' plugin config" in message


def test_a_bare_name_is_refused_as_an_entry_that_is_not_a_table(
    tmp_path: Path,
) -> None:
    message = refusal_for(_detectors(tmp_path, '"jq"'))
    assert "'jq'" in message
    assert "not a table" in message


def test_a_detector_missing_its_install_command_is_refused_by_name(
    tmp_path: Path,
) -> None:
    entry = '{ name = "jq", kind = "command" }'

    message = refusal_for(_detectors(tmp_path, COMPLETE, entry))

    assert (
        message == "detector 'jq' is missing key 'install' in the 'alpha' plugin config"
    )


def test_a_detector_with_no_name_is_quoted_whole(tmp_path: Path) -> None:
    entry = '{ kind = "command", install = "brew install jq" }'

    message = refusal_for(_detectors(tmp_path, COMPLETE, entry))

    assert message == (
        "detector {'kind': 'command', 'install': 'brew install jq'} "
        "is missing key 'name' in the 'alpha' plugin config"
    )


def test_an_unknown_detector_key_is_rejected_by_name(tmp_path: Path) -> None:
    entry = '{ name = "jq", kind = "command", install = "x", when = "always" }'

    assert "'when'" in refusal_for(_detectors(tmp_path, entry))


def test_an_unknown_detector_kind_is_rejected_with_the_valid_ones(
    tmp_path: Path,
) -> None:
    entry = '{ name = "jq", kind = "binary", install = "brew install jq" }'

    message = refusal_for(_detectors(tmp_path, entry))

    assert "'binary'" in message
    assert "the 'alpha' plugin config" in message
    assert "'command', 'node-module'" in message


def test_an_install_command_written_as_a_list_is_refused(tmp_path: Path) -> None:
    entry = '{ name = "jq", kind = "command", install = ["brew", "install", "jq"] }'

    message = refusal_for(_detectors(tmp_path, entry))

    assert "detector 'jq'" in message
    assert "'install'" in message
    assert "non-empty string" in message


def test_a_name_that_is_not_a_string_is_refused(tmp_path: Path) -> None:
    entry = '{ name = 1, kind = "command", install = "brew install jq" }'

    message = refusal_for(_detectors(tmp_path, entry))

    assert "'name'" in message
    assert "non-empty string" in message


def test_an_empty_install_command_is_refused_like_a_missing_one(
    tmp_path: Path,
) -> None:
    entry = '{ name = "jq", kind = "command", install = "" }'

    message = refusal_for(_detectors(tmp_path, entry))

    assert "detector 'jq'" in message
    assert "'install'" in message
    assert "non-empty string" in message


def test_a_project_may_not_declare_detectors(tmp_path: Path) -> None:
    write_project_config(tmp_path, 'detectors = [{ name = "jq", kind = "command" }]')

    message = refusal_for(tmp_path)

    assert "'detectors'" in message
    assert "the project config" in message
