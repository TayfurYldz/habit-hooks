
from __future__ import annotations

import re
from importlib.metadata import metadata, requires

from . import resolve

CORE_DISTRIBUTION = "habit-hooks"

PLUGIN_REQUIREMENT = re.compile(rf"{CORE_DISTRIBUTION}-([a-z0-9-]+)")

EXTRA_MARKER = "extra =="


def provided_extras() -> frozenset[str]:
    return frozenset(metadata(CORE_DISTRIBUTION).get_all("Provides-Extra") or ())


def depended_on_plugins() -> frozenset[str]:
    unconditional = (
        line for line in requires(CORE_DISTRIBUTION) or () if EXTRA_MARKER not in line
    )
    named = (PLUGIN_REQUIREMENT.match(line) for line in unconditional)
    return frozenset(match.group(1) for match in named if match)


def distribution(plugin: str) -> str:
    installed = resolve.installed_plugin_distributions()
    return installed.get(plugin, f"{CORE_DISTRIBUTION}-{plugin}")
