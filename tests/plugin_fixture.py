
from __future__ import annotations

from pathlib import Path

from habit_hooks.config import load_config
from habit_hooks.resolve import Resolver
from habit_hooks.sensors.loader import PluginLoader
from habit_hooks.sensors.model import Part


def write_project_config(project_dir: Path, body: str) -> None:
    path = project_dir / ".habit-hooks" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def write_plugin(project_dir: Path, name: str, files: dict[str, str]) -> None:
    base = project_dir / ".habit-hooks" / name
    for relative, contents in files.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def loader_for(project_dir: Path) -> PluginLoader:
    config = load_config(project_dir)
    return PluginLoader(Resolver.discover(project_dir), config)


def one_transformer(project_dir: Path, recipe: str, plugin_toml: str = "") -> Part:
    write_project_config(project_dir, 'plugins = ["fixt"]')
    write_plugin(
        project_dir,
        "fixt",
        {"config.toml": f"sensors = []\n{plugin_toml}", "transformers/t.toml": recipe},
    )
    return loader_for(project_dir).resolve_part(["fixt"], "transformers", "t")


def one_sensor(project_dir: Path, sensor_toml: str, plugin_toml: str = "") -> Part:
    write_project_config(project_dir, 'plugins = ["fixt"]')
    write_plugin(
        project_dir,
        "fixt",
        {
            "config.toml": f'sensors = ["s"]\n{plugin_toml}',
            "sensors/s.toml": sensor_toml,
        },
    )
    return loader_for(project_dir).load_plugin("fixt").sensors[0]
