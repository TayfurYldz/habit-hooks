from __future__ import annotations

from pathlib import Path

import pytest

from habit_hooks.cli import ConfigError
from plugin_fixture import loader_for, write_plugin


def test_a_transformer_missing_its_recipe_is_named_a_transformer(
    tmp_path: Path,
) -> None:
    write_plugin(
        tmp_path,
        "fixt",
        {"config.toml": "sensors = []", "transformers/t.toml": 'files = ["src/**"]'},
    )

    with pytest.raises(ConfigError) as refusal:
        loader_for(tmp_path).resolve_part(["fixt"], "transformers", "t")

    assert str(refusal.value).startswith("transformer 't' spells neither")
