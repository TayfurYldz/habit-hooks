from __future__ import annotations

import json
from pathlib import Path

import pytest
from knip_project import SHIPPED_CONFIG, passes, project

KNIP_CONFIG_LOCATIONS = [
    "knip.json",
    "knip.jsonc",
    ".knip.json",
    ".knip.jsonc",
    "knip.ts",
    "knip.js",
    "knip.config.ts",
    "knip.config.js",
]

MARKED = '{"entry": ["src/cli.ts!"], "project": ["src/**/*.ts!"]}'
UNMARKED = '{"entry": ["src/cli.ts"], "project": ["src/**/*.ts"]}'


def test_the_shipped_config_is_named_when_the_project_wrote_none(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)

    first, *_ = passes(consumer)

    assert "--config" in first, first
    assert first[first.index("--config") + 1] == str(SHIPPED_CONFIG)


@pytest.mark.parametrize("location", KNIP_CONFIG_LOCATIONS)
def test_a_config_the_project_wrote_is_left_for_knip_to_find(
    location: str, tmp_path: Path
) -> None:
    consumer = project(tmp_path)
    (consumer / location).write_text(UNMARKED, encoding="utf-8")

    first, *_ = passes(consumer)

    assert "--config" not in first, first


def test_a_knip_key_in_the_manifest_is_a_config_the_project_wrote(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "package.json").write_text(
        json.dumps({"name": "demo", "knip": json.loads(UNMARKED)}), encoding="utf-8"
    )

    first, *_ = passes(consumer)

    assert "--config" not in first, first


def test_the_gate_reads_the_shipped_markers_when_ours_is_in_force(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)

    spawned = passes(consumer)

    assert len(spawned) == 2, spawned
    assert "--production" in spawned[1]
    assert spawned[1][spawned[1].index("--config") + 1] == str(SHIPPED_CONFIG)


def test_a_project_config_without_markers_runs_no_production_pass(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "knip.json").write_text(UNMARKED, encoding="utf-8")

    assert len(passes(consumer)) == 1


def test_a_project_config_with_markers_still_gates_the_production_pass(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)
    (consumer / "knip.json").write_text(MARKED, encoding="utf-8")

    spawned = passes(consumer)

    assert len(spawned) == 2, spawned
    assert "--config" not in spawned[1], spawned[1]


def test_the_sensor_s_args_reach_knip(tmp_path: Path) -> None:
    consumer = project(tmp_path)

    first, *_ = passes(consumer, ("--exclude", "files"))

    assert first[first.index("--exclude") + 1] == "files", first


def test_a_config_named_through_the_args_is_the_one_in_force(tmp_path: Path) -> None:
    consumer = project(tmp_path)
    (consumer / "custom.json").write_text(MARKED, encoding="utf-8")

    first, *_ = passes(consumer, ("--config", "custom.json"))

    assert str(SHIPPED_CONFIG) not in first, first
    assert first[first.index("--config") + 1] == "custom.json", first


def test_a_config_flag_with_nothing_after_it_is_knip_s_error_to_report(
    tmp_path: Path,
) -> None:
    consumer = project(tmp_path)

    first, *_ = passes(consumer, ("--config",))

    assert first[first.index("--config") + 1] == str(SHIPPED_CONFIG), first
    assert first[-1] == "--config", first


def test_the_gate_reads_the_config_the_args_named(tmp_path: Path) -> None:
    consumer = project(tmp_path)
    (consumer / "custom.json").write_text(UNMARKED, encoding="utf-8")

    assert len(passes(consumer, ("--config", "custom.json"))) == 1
