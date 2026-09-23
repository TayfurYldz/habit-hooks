# habit-hooks-php

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its PHP plugin.

## What it does

The plugin enables `habit-sensors` over a PHP project and rewrites [PHPMD](https://phpmd.org/) findings into structural code smells from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md) — for example `too-many-parameters`, `high-complexity`, `unused-variable`, with the `codesize` and `unusedcode` rulesets. A rule with no mapping passes through under its own name rather than disappearing, and a tool that crashes fails the run rather than reporting clean.

PHPMD ships inside the plugin as a `.phar`, so only PHP itself must be on the machine.

## Requirements

- Python 3.11+
- [PHP](https://www.php.net/) on `PATH` (`php`).

## Installation

The plugin ships as an extra of the core package:

```bash
pip install "habit-hooks[php]"
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["php", "generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
