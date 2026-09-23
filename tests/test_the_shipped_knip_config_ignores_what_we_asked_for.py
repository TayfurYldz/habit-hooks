
from __future__ import annotations

import json
import re
from pathlib import Path

from habit_hooks.config_schema import read_toml

REPO_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT = REPO_ROOT / "plugins" / "typescript" / "src" / "habit_hooks_typescript"
SHIPPED_KNIP_CONFIG = TYPESCRIPT / "knip.json"
SHIPPED_ESLINT_CONFIG = TYPESCRIPT / "eslint.config.mjs"

NPM_INSTALL = "npm install"

NODE_MODULE = "node-module"

REQUIRED_PACKAGE = re.compile(r'required\(\s*"([^"]+)"\s*\)')

KNIP_EXCLUDES_ITSELF = "knip"


def _packages_a_plugin_asks_for(config: Path) -> set[str]:
    return {
        detector["name"]
        for detector in read_toml(config).get("detectors", [])
        if detector.get("kind") == NODE_MODULE
        or detector.get("install", "").startswith(NPM_INSTALL)
    }


def _our_footprint_in_a_project() -> set[str]:
    configs = sorted(REPO_ROOT.glob("plugins/*/src/habit_hooks_*/config.toml"))
    assert configs, "no shipped plugin configs found — the glob has gone stale"

    declared = set().union(*(_packages_a_plugin_asks_for(one) for one in configs))
    required = set(
        REQUIRED_PACKAGE.findall(SHIPPED_ESLINT_CONFIG.read_text(encoding="utf-8"))
    )
    assert required, "the shipped eslint config named nothing — the pattern has gone stale"
    return (declared | required) - {KNIP_EXCLUDES_ITSELF}


def test_the_shipped_config_overlooks_our_footprint_and_only_our_footprint() -> None:
    shipped = json.loads(SHIPPED_KNIP_CONFIG.read_text(encoding="utf-8"))

    assert sorted(shipped["ignoreDependencies"]) == sorted(_our_footprint_in_a_project())
