# habit-hooks-generic

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its language-agnostic plugin — the checks that work on any source tree, whatever the language.

## What it does

The plugin enables `habit-sensors` over any files you name and rewrites them into structural code smells from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md):

- **jscpd** — copy-pasted duplication, coached as `duplicated-code`.
- **line count** — files and functions past a size budget, coached as `oversized-file` / `oversized-function`.

A tool that crashes fails the run rather than reporting clean.

## Requirements

- Python 3.11+
- [jscpd](https://github.com/kucherenko/jscpd) (`npm install -g jscpd`). The line-count check needs nothing beyond Python.

## Installation

This plugin is a core dependency of [habit-hooks](https://github.com/habit-hooks/habit-hooks) and needs no extra:

```bash
pip install habit-hooks
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
