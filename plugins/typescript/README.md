# habit-hooks-typescript

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its TypeScript and JavaScript plugin.

## What it does

The plugin enables `habit-sensors` over a TypeScript/JavaScript project and rewrites three tools' findings into structural code smells from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md):

- **eslint** — your project's own flat config drives it; selected rules map to smells such as `oversized-function`, `too-many-parameters`, `deep-nesting`.
- **knip** — unused files, exports, dependencies and dead code, including code alive only because a test references it.
- **ts-morph analysis** — comments that narrate instead of stating a non-obvious why, coached as `non-essential-comment`.

Every wrapped tool resolves from your project's own `node_modules`, so the versions your lockfile pins are the versions that run. A tool that crashes fails the run rather than reporting clean.

## Requirements

- Python 3.11+
- Node.js, with `eslint` and `knip` installed in the project (`npm install --save-dev eslint knip`).

## Installation

The plugin ships as an extra of the core package:

```bash
pip install "habit-hooks[typescript]"
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["typescript", "generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
