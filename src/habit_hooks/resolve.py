
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from importlib.metadata import entry_points
from importlib.resources import files
from pathlib import Path

from .cli import ToolError

PLUGIN_ENTRY_POINT_GROUP = "habit_hooks.plugins"

CORE_GUIDES = Path(__file__).parent / "guides"

CORE_PACKAGE_DIR = Path(__file__).parent


@cache
def installed_plugin_dirs() -> dict[str, Path]:
    dirs: dict[str, Path] = {}
    for entry_point in entry_points(group=PLUGIN_ENTRY_POINT_GROUP):
        dirs[entry_point.name] = Path(str(files(entry_point.value)))
    return dirs


@cache
def installed_plugin_distributions() -> dict[str, str]:
    return {
        entry_point.name: entry_point.dist.name
        for entry_point in entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
        if entry_point.dist is not None
    }


@dataclass(frozen=True)
class Resolver:

    project_dir: Path
    package_dirs: dict[str, Path]

    @classmethod
    def discover(cls, project_dir: Path) -> Resolver:
        return cls(project_dir, installed_plugin_dirs())

    def plugin_dirs(self, plugin: str) -> list[Path]:
        override = self.project_dir / ".habit-hooks" / plugin
        package = self.package_dirs.get(plugin)
        return [override] if package is None else [override, package]

    def has_plugin(self, plugin: str) -> bool:
        return self.in_plugin(plugin, "config.toml") is not None

    def require_plugin(self, plugin: str) -> None:
        if self.has_plugin(plugin):
            return
        raise ToolError(
            f"habit-sensors: plugin {plugin!r} is not installed — "
            f"install it with `pip install habit-hooks-{plugin}`"
        )

    def in_plugin(self, plugin: str, relative: str) -> Path | None:
        for base in self.plugin_dirs(plugin):
            candidate = base / relative
            if candidate.is_file():
                return candidate
        return None

    def part(self, plugins: list[str], relative: str) -> Path | None:
        for plugin in plugins:
            found = self.in_plugin(plugin, relative)
            if found is not None:
                return found
        candidate = CORE_PACKAGE_DIR / relative
        return candidate if candidate.is_file() else None

    def guide(self, guide: str, plugins: list[str]) -> Path | None:
        return self.first(plugins, [guide])

    def first(self, plugins: list[str], candidates: list[str]) -> Path | None:
        for plugin in plugins:
            for base in self.plugin_dirs(plugin):
                for name in candidates:
                    candidate = base / "guides" / name
                    if candidate.is_file():
                        return candidate
        for name in candidates:
            candidate = CORE_GUIDES / name
            if candidate.is_file():
                return candidate
        return None
