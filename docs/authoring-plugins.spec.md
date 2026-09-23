# Authoring plugins

A plugin is a small installable package: a `config.toml` saying what it contributes, each sensor spelled inline in that config, one jq file per wrapped tool, and — optionally — guides and scenarios. This page is the whole manual; the moving parts are in [architecture.md](architecture.md), the finding shape in [sensor-interface.spec.md](sensor-interface.spec.md), the config keys in [config.md](config.md).

## A plugin is an installable package

- Distribution `habit-hooks-<name>` (what you `pip install`), import package `habit_hooks_<name>`, everything shipped as package data. A plugin does not need to live in this repo — the core finds it through the `habit_hooks.plugins` entry-point group.

```
habit-hooks-<name>/
  pyproject.toml
  src/habit_hooks_<name>/
    __init__.py            # may be empty
    config.toml            # language, files, sensors, detectors
    scenarios/             # approved outputs, one directory per sensor
    guides/                # per-smell coaching (optional)
```

```toml
# pyproject.toml — the entry point is the only requirement beyond packaging
[project.entry-points."habit_hooks.plugins"]
lua = "habit_hooks_lua"
```

`config.toml` declares the language the plugin speaks and the tools it reaches for; every key is in [config.md](config.md).

```toml
# src/habit_hooks_lua/config.toml
language = "lua"
files = ["**/*.lua"]
sensors = [{ tool = "some-linter", args = ["--json", "${files}"], transform = "some-linter.jq" }]
detectors = [{ name = "some-linter", kind = "command", install = "brew install some-linter" }]
```

- `detectors` names each external tool, how to find it (`command` on PATH, `node-module` read by node), and the install command a consumer is handed when it is missing. Declaring is a statement, not a dependency.
- A sensor naming a tool no plugin declares is refused as the config loads; a declared tool that is not installed is the ordinary missing-tool notice.
- `search_paths` adds project directories ahead of PATH (a language's own `bin`).

## A sensor is one inline table

One shape for every sensor — an entry in the plugin's `sensors` list:

| Field | | Meaning |
|-------|----------|---------|
| `tool` | required | the tool's name (a declared detector, resolved to the file this project runs) or a shipped program: `"${dir}/helper.py"` |
| `args` | | the argument list. `${files}` is the scoped files, each glob-escaped so a filename is a name, never a pattern; `${files:comma}` is the same files as one comma-joined argument, for a tool whose own format takes them that way (phpmd's phar — a filename containing a comma cannot survive that format, and that is the tool's limitation, not a workaround); `${dir}`, `${python}`, `${detector:<name>}` and `${config}` substitute inside an element; `${args}` is where a project's `[sensors.<name>]` args override lands — spell it and the override becomes arguments there (a shipped default for it lives in the program, not the recipe) |
| `success_exit_codes` | optional | default `[0]`. Most linters exit `1` to say "I found things" — declare `[0, 1]` and the findings are trusted alongside it |
| `transform` | optional | a jq program beside the config; absent → the tool's stdout is already findings JSON |
| `report` | optional | the framework hands the tool a fresh file for `${report}` and reads it back — for tools that write reports instead of printing. A missing report is a failed run, never a clean one |
| `files` | optional | narrows the run's scope for this sensor alone |
| `name` | optional | the sensor's name; defaults to `tool`, required when the tool is a placeholder or path |

The framework owns everything around the tool: resolving it, judging the exit code, timeouts, Windows shims. Output that is not JSON, a transform that does not answer one findings array, or a finding outside the contract — each is the sensor's own failed run, carrying the tool's last words. Never a silent clean.

### A sensor end to end

A stub linter (any executable printing JSON will do — here a shell script) mapped to findings by a jq program, run exactly as a consumer's project runs it.

📄.habit-hooks/config.toml
```toml
plugins = ["demo"]
```

📄.habit-hooks/demo/config.toml
```toml
files = ["**/*.todo"]
sensors = [{ tool = "stub-lint", args = ["${files}"], transform = "map.jq", success_exit_codes = [0, 1] }]
detectors = [{ name = "stub-lint", kind = "command", install = "chmod +x tools/stub-lint", search_paths = ["tools"] }]
```

📄.habit-hooks/demo/map.jq
```jq
map({smell: .rule, details: {}, issues: [{key: .file, details: {file: .file, line: .line, message: .message}}]})
```

📄tools/stub-lint
```sh
#!/bin/sh
out="["
first=yes
for file in "$@"; do
  [ "$first" = yes ] || out="$out,"
  first=
  out="$out{\"file\":\"$file\",\"line\":2,\"rule\":\"STUB-1\",\"message\":\"stub violation\"}"
done
printf '%s]\n' "$out"
exit 1
```

📄src/app.todo
```text
write the real adapter
```

```bash
chmod +x tools/stub-lint && habit-sensors --all
```

🖥️ ✅
```text
[{"smell": "STUB-1", "details": {}, "issues": [{"key": "src/app.todo", "details": {"file": "src/app.todo", "line": 2, "message": "stub violation"}}]}]
```

## The transform is jq

`transform` names a jq program shipped beside the config. Its contract:

- **stdin** (as jq input): the tool's stdout, parsed as JSON.
- **stdout**: exactly one findings array — `[{smell, details, issues: [{key, details}]}]`, one finding per smell, one `issues` entry per occurrence, `key` being what snoozing acts on (usually the file path).
- The result is validated against the findings contract; any miss — a program that errors, answers nothing, or answers a non-array — is the sensor's failed run, never a silent clean one.

jq is the whole mapping language: what a tool's output means is the plugin's to say, and it is said in one small file a tool's format change edits.

## Smells are an open vocabulary

Map the codes you know to catalogue smells ([smell-vocabulary.md](smell-vocabulary.md)) and pass the rest through under their own name — `smell: .rule` above, not a lookup table with a default of "drop". An unmapped code becoming a finding of its own name is caught by `uncoached`, which the project tunes ([config.md](config.md)); a dropped code is a clean run nobody ran.

## Scenarios: approve what your sensor finds

Each sensor may ship an approved-output scenario — the drift gate for everything above:

```
scenarios/<sensor>/
  sample/          the sample codebase; it is the run's scope
  approved.json    the findings the sensor must produce over sample/ — findings
                   JSON only, never guide strings
  scenario.toml    optional: tool = "<name>" — a machine without the tool skips
                   the scenario (visibly, in pytest -rs); a machine with it never does
```

- The scenario runs the sensor through the plugin's own config, exactly as a run does. The gate is `tests/test_approved_scenarios.py`; ship `scenarios/` as package data so it reaches the installed plugin.
- To regenerate after a deliberate change: put `[]` in `approved.json`, run the gate, and copy the "this run" side of the diff it prints.

## Guides and transformers

- `guides/<smell>.md` is a Jinja2 template rendered against the whole finding; write one only where the language needs its own wording, else the generic or `uncoached` guide serves. Keep prompts short and outcome-focused.
- Script guides run through `[runners]` (extension → command, [config.md](config.md)).
- A transformer receives the whole findings array on stdin and prints a new one; it must pass through every finding it does not handle ([architecture.md](architecture.md)).

## The legacy sensor form is going away

`sensors/<name>.toml` spec files with `command`/`argv` are the pre-inline form and pending removal — do not start a new one. A migration is mechanical: the argv becomes `tool` + `args`, the jq pipeline beside the script becomes the `transform`.
