from __future__ import annotations

import tomllib
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1] / "src" / "habit_hooks_ruby"


def test_the_exclusions_name_ruby_shapes_so_they_bind_only_ruby() -> None:
    config = tomllib.loads((PACKAGE / "config.toml").read_text(encoding="utf-8"))
    exclusions = [glob for glob in config["files"] if glob.startswith("!")]

    assert exclusions, "the plugin declares no exclusions at all"
    ruby_shapes = (".rb", ".rake", ".gemspec", "/Rakefile", "/Gemfile", "/schema.rb")
    for glob in exclusions:
        assert glob.endswith(ruby_shapes), glob
