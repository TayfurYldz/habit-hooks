# habit-hooks-java

[Habit Hooks](https://github.com/habit-hooks/habit-hooks) turns best-practice coding advice into AI habits: it runs your linters, then replaces each raw rule violation with a short coaching guide an AI coding agent can act on. This package is its Java plugin.

## What it does

The plugin enables `habit-sensors` over a Java project and rewrites [PMD](https://pmd.github.io/) findings into structural code smells from the [canonical vocabulary](https://github.com/habit-hooks/habit-hooks/blob/main/docs/smell-vocabulary.md) — for example `too-many-parameters`, `oversized-function`, `high-complexity`, `unused-variable`. A rule with no mapping passes through under its own name rather than disappearing, and a tool that crashes fails the run rather than reporting clean.

The plugin owns PMD's ruleset choice, so the same structural bar applies to every project it runs on.

## Requirements

- Python 3.11+
- Java, and [PMD](https://pmd.github.io/) available as `pmd` on `PATH`.

## Installation

The plugin ships as an extra of the core package:

```bash
pip install "habit-hooks[java]"
```

Then list it in `.habit-hooks/config.toml` at the repo root:

```toml
plugins = ["java", "generic"]
```

The full walk-through — init, running, snoozing, CI — is in the [core README](https://github.com/habit-hooks/habit-hooks#readme).
