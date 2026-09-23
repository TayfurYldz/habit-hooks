# habit-hooks-python

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its Python plugin.

## What it does

The plugin enables `habit-sensors` over a Python project and rewrites three tools' findings into structural code smells from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md):

- **ruff** — `too-many-parameters`, `high-complexity`, `unused-variable`, `unused-import`, `swallowed-exception`. Unmapped codes pass through under their own name rather than disappearing.
- **deptry** — dependencies declared but never imported.
- **comment analysis** — comments and docstrings that narrate instead of stating a non-obvious why, coached as `non-essential-comment`.

A tool that crashes fails the run rather than reporting clean.

## Requirements

- Python 3.11+
- [ruff](https://docs.astral.sh/ruff/) and [deptry](https://github.com/fpgmaas/deptry) on `PATH` (`pip install ruff deptry`).

## Installation

The plugin ships as an extra of the core package:

```bash
pip install "habit-hooks[python]"
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["python", "generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
