from __future__ import annotations

import subprocess
from pathlib import Path

from eslint_project import SHIPPED_CONFIG, UNUSED_LOCAL_LINE, messages, project


def test_an_interface_method_parameter_is_not_an_unused_variable(
    tmp_path: Path,
) -> None:
    reported = messages(project(tmp_path), SHIPPED_CONFIG)

    assert [message["line"] for message in reported] == [UNUSED_LOCAL_LINE], reported


def test_the_unused_local_is_reported_by_the_typescript_rule(tmp_path: Path) -> None:
    reported = messages(project(tmp_path), SHIPPED_CONFIG)

    assert [message["ruleId"] for message in reported] == [
        "@typescript-eslint/no-unused-vars"
    ]


def test_the_config_loads_from_where_it_ships(tmp_path: Path) -> None:
    consumer = project(tmp_path)
    installed = tmp_path / "site-packages" / "habit_hooks_typescript"
    installed.mkdir(parents=True)
    shipped = installed / SHIPPED_CONFIG.name
    shipped.write_bytes(SHIPPED_CONFIG.read_bytes())

    reported = messages(consumer, shipped)

    assert [message["line"] for message in reported] == [UNUSED_LOCAL_LINE], reported


def test_a_project_without_typescript_eslint_is_told_to_install_it(
    tmp_path: Path,
) -> None:
    consumer = tmp_path / "demo"
    consumer.mkdir()

    result = subprocess.run(
        ["node", "--input-type=module", "-e", f"import({SHIPPED_CONFIG.as_uri()!r})"],
        cwd=consumer,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode != 0
    assert "npm install --save-dev @typescript-eslint/parser" in result.stderr
    assert "Cannot find module" not in result.stderr, result.stderr
