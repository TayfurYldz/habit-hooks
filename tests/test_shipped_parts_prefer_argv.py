
from __future__ import annotations

from pathlib import Path

from habit_hooks.config_schema import read_toml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _shipped_part_specs() -> list[Path]:
    patterns = (
        "plugins/*/src/*/sensors/*.toml",
        "src/habit_hooks/sensors/*.toml",
        "src/habit_hooks/transformers/*.toml",
    )
    return sorted(path for pattern in patterns for path in REPO_ROOT.glob(pattern))


def test_every_shipped_part_spells_argv() -> None:
    specs = _shipped_part_specs()
    assert len(specs) == 3, specs  # a part added here must be judged too

    shell_recipes = [path for path in specs if "argv" not in read_toml(path)]

    assert shell_recipes == []
