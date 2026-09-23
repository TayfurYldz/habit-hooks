# habit-hooks-ruby

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its Ruby plugin — the piece that knows Ruby, RuboCop and how RuboCop's cops map onto those coaching guides.

## What it does

The plugin enables `habit-sensors` over a Ruby project. RuboCop runs against your project's own `.rubocop.yml`, and each offence is rewritten into a structural code smell from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md) — for example `too-many-parameters`, `oversized-function`, `high-complexity`, `unused-variable`. A cop with no mapping passes through under its own name rather than disappearing, and a tool that crashes fails the run rather than reporting clean.

## Requirements

- Python 3.11+
- [RuboCop](https://rubocop.org/) on `PATH`, or the project's own binstub at `bin/rubocop` (found and preferred, so a bundle with extension gems keeps working).

## Installation

The plugin ships as an extra of the core package:

```bash
pip install "habit-hooks[ruby]"
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["ruby", "generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
