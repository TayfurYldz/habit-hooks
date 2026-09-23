
from __future__ import annotations

from pathlib import Path

import pytest
from platform_probe import A_SHELL_TO_RUN_IT_WITH, off_windows

from sensor_notice import only_notice, script_notice, sensor_notice

from habit_hooks.sensors.model import Part


@A_SHELL_TO_RUN_IT_WITH
def test_a_sensor_whose_tool_is_not_installed_names_the_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    notice = sensor_notice(tmp_path, "no-such-tool-here --json ${files}")

    assert notice == (
        "habit-sensors: sensor 'probe' needs the 'no-such-tool-here' command, "
        "which is not installed — install it, or disable the sensor with "
        "[sensors.probe] disabled = true"
    )


@A_SHELL_TO_RUN_IT_WITH
def test_a_tool_missing_from_inside_a_pipeline_is_named_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    off_windows(monkeypatch)
    pipeline = "set -o pipefail\nno-such-tool-here | jq ."

    assert "needs the 'no-such-tool-here' command" in sensor_notice(tmp_path, pipeline)


def test_a_sensor_that_broke_some_other_way_still_quotes_itself_back(
    tmp_path: Path,
) -> None:
    notice = script_notice(
        tmp_path,
        "import sys\n"
        "print('cannot reach registry', file=sys.stderr)\n"
        "sys.exit(1)\n",
    )

    assert notice.startswith("habit-sensors: sensor 'probe' failed:")
    assert "cannot reach registry" in notice


def test_an_argv_sensor_names_its_missing_tool_in_the_very_same_words(
    tmp_path: Path,
) -> None:
    part = Part(
        name="probe", directory=tmp_path, argv=["no-such-tool-here", "--json"]
    )

    assert only_notice(part) == (
        "habit-sensors: sensor 'probe' needs the 'no-such-tool-here' command, "
        "which is not installed — install it, or disable the sensor with "
        "[sensors.probe] disabled = true"
    )


def test_a_spawn_refused_for_another_reason_is_not_called_a_missing_tool(
    tmp_path: Path,
) -> None:
    part = Part(name="probe", directory=tmp_path, argv=["printf", "[]"])

    notice = only_notice(part, tmp_path / "deleted")

    assert "needs the" not in notice
    assert notice.startswith("habit-sensors: sensor 'probe' could not run: printf '[]'")

