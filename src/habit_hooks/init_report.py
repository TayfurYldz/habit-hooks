
from __future__ import annotations

from .initialise import Plan
from .recommend import LANGUAGE_SIGNALS

AUTHORING_GUIDE = (
    "https://github.com/habit-hooks/habit-hooks"
    "/blob/main/docs/authoring-plugins.spec.md"
)


def _and_joined(items: tuple[str, ...]) -> str:
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


SHIPPED_LANGUAGES = _and_joined(tuple(signal.language for signal in LANGUAGE_SIGNALS))

LANGUAGE = "<your language>"

AGENT_PROMPT = (
    f"Write a habit-hooks plugin for {LANGUAGE}. Read",
    f"  {AUTHORING_GUIDE}",
    "first — it is the end-to-end manual and it runs top to bottom. Follow it",
    f"to build an installable habit-hooks-{LANGUAGE} package with a sensor that",
    f"finds one real structural smell in {LANGUAGE} and a guide that coaches",
    "the fix, then install it and enable it in .habit-hooks/config.toml.",
)


def _detected(planned: Plan) -> str:
    if not planned.languages:
        return "Detected: no language habit-hooks has a plugin for."
    return f"Detected: {', '.join(planned.languages)}."


def _listed(plugins: tuple[str, ...]) -> str:
    return ", ".join(plugins) or "no plugins"


def _configuration(planned: Plan) -> str:
    if planned.already_configured:
        return (
            f"Already configured: .habit-hooks/config.toml enables "
            f"{_listed(planned.plugins)}. Left as it is."
        )
    return f"Wrote .habit-hooks/config.toml, enabling {_listed(planned.plugins)}."


def _plugins_block(planned: Plan) -> list[str]:
    if not planned.uninstalled_plugins:
        return []
    return [
        "",
        "Plugins not installed — nothing runs without them: "
        + ", ".join(planned.uninstalled_plugins),
        *(f"  {command}" for command in planned.plugin_installs),
    ]


def _tools_block(planned: Plan) -> list[str]:
    if not planned.missing_tools:
        return []
    width = max(len(detector.name) for detector in planned.missing_tools)
    return [
        "",
        "Tools this machine has not got:",
        *(
            f"  {detector.name.ljust(width)}   {detector.install}"
            for detector in planned.missing_tools
        ),
    ]


def _closing(planned: Plan) -> list[str]:
    if not planned.installs:
        return ["", "Nothing missing — run `habit-hooks` to see what it finds."]
    if planned.uninstalled_plugins:
        return [
            "",
            "Install these, then run `habit-hooks init` again: a plugin declares",
            "tools of its own, which cannot be looked for until it is installed.",
        ]
    return ["", "Install these, then run `habit-hooks`."]


def _new_plugin_block(planned: Plan) -> list[str]:
    if not planned.needs_a_new_plugin:
        return []
    return [
        "",
        f"habit-hooks ships plugins for {SHIPPED_LANGUAGES}. For anything else the",
        f"plugin is one to write — hand this to your coding agent, with {LANGUAGE}",
        "filled in:",
        "",
        *(f"  {line}" for line in AGENT_PROMPT),
    ]


def report(planned: Plan) -> list[str]:
    return [
        _detected(planned),
        _configuration(planned),
        *_plugins_block(planned),
        *_tools_block(planned),
        *_new_plugin_block(planned),
        *_closing(planned),
    ]
