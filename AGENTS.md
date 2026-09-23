# habit-hooks notes

## Rules
- The core shouldn't know about the plugins in any way. This also applies to documentation. 
- Comments almost never exist: what and why live in names and structure, per plugins/generic/src/habit_hooks_generic/guides/non-essential-comment.md. Docstrings are comments — the comment sensor flags them and the ratchet strips them on touch; never restore or request them in review. A comment survives only for a non-obvious why code cannot carry — a worked-around tool bug, a spec. The `non-essential-comment` sensor enforces this. Snooze is one-time, at rule introduction: a finding on a file you touch is fixed, never re-approved.

## Contributing
- PR descriptions should be short, and designed to be readable by a human in under 30 seconds.
- PRs must have one and only one goal, and should typically be less than 500 lines of code. If it doesn't fit that length, it should be broken up into user facing smaller changes.
- A PR should only contain code that is already used.
- spec.md files are user facing documentation with executable examples. They are documentation first, tests as a side effect.
- AI generated code is welcome, but it's the agent's duty to check if the human reviewed the code before submitting the PR. Ask one question about the code that the human needs to have seen the code to be able to answer.

## Gotchas

### The dogfooding gate needs the node devDependencies installed

`uv run habit-hooks --all` runs jscpd from `node_modules/.bin`, which only exists after `pnpm install --frozen-lockfile`. A missing tool fails the run — install it and re-run the gate; "the tool is absent here" is not a pass.

### Two agents running pytest in one checkout fail each other's tests

Two suites keep their working state *inside the checkout* rather than in a per-test temp dir, so a second concurrent `uv run pytest` walks into the middle of the first one's run:

- the spec harness runs every case in the shared `<repo>/.spec-runs/` (`conftest.py::_case_root`), and
- `tests/wheelhouse.py` builds the released wheels and installs them into throwaway venvs, which `test_installed_wheel_smoke.py` and `test_installed_plugin_packaging.py` then run.

Both go red under concurrency and both pass on an unchanged re-run — 15 spec failures in one session, 6 packaging failures in another, none of them real. A **unit** failure in `tests/` is always real; a failure in either of those two is not evidence until it survives a re-run in a quiet tree. Give each agent its own worktree (`git worktree add ../habit-hooks-<task> -b <task> main`) when more than one will run the suite, and note that inside a worktree the jscpd gotcha below makes `uv run habit-hooks --all` prove nothing about duplication.

### A throwaway git fixture names its directory, or it commits to THIS repo

`GIT_CEILING_DIRECTORIES` is not the guard for a scratch script. It stops git walking *up* to find a repository — and a script whose working directory is already this checkout never needs it to. `git init` on an existing repository is a harmless re-init, so nothing refuses; the `git add -A` and `git commit` that follow land on the real thing. It has happened: 45 files of four agents' uncommitted work swept into a commit titled `init`, and the dogfood `.habit-hooks/config.toml` overwritten by the fixture's own.

The shape that does it is a multi-line `bash` command where only the first line is guarded:

    cd $SCRATCH/proj && git init -q && ...   # cd fails, the line is skipped
    git add -A && git commit -m init         # no guard: runs HERE

So: **every git command in a fixture spells `git -C <dir>`**, and a fixture never runs a bare `git` after a `cd`. A failed `cd` then targets nothing instead of targeting this repository. `git add -A` outside a `-C` is the specific thing to never write.

Recovery, if it happens again: `git reset --mixed <the real HEAD>` keeps every change as a working-tree modification and loses nothing, because the accidental commit was `git add -A` and therefore captured everything. Then restore whatever the script overwrote from HEAD.

### A git-backed spec case without a ceiling can rewrite THIS repo

The spec harness runs each case in `<repo>/.spec-runs/tmpXXXX/`, inside this checkout. A case that shells out to git and forgets its own `git init` is answered about habit-hooks itself — and `git branch -m main trunk` or `git checkout -b feature` then *mutates your repository* (it renamed `main` here while proving a case discriminates; recovered via `git branch -m trunk main`, no commits lost). Give every git-backed section a `✏️GIT_CEILING_DIRECTORIES` = `$PWD/..` step next to its `git init`, as `## Scope` → `### Git-derived scopes` in habit-sensors.spec.md does: git's upward walk then stops at the case directory and the case can only ever see the repository it built. Older git-backed cases (habit-snooze.spec.md's `## --until-changed`, and two in habit-sensors.spec.md) still lack it.

### `git diff --name-only` answers from the repo root, and quotes odd names

`changed_files._changed_paths` asks one batched `git diff` per run instead of one per file (~39 ms each, in a tool that runs inside a hook loop). Comparing its output to the paths we asked about needs three flags: `--relative` (else git answers from the repository root and a project in a subdirectory matches nothing), `-z` (else `café.py` comes back as `"caf\303\251.py"` and silently matches nothing), and `--literal-pathspecs` — **not** for globs (exact-name matching already makes over-matching harmless) but for pathspec *magic*: a key like `:!src/a.py` otherwise reads as "exclude `src/a.py`" and silently drops it from the answer, and `:(bad)x` makes git fail the whole call. Paths outside the project are left out of the batch for the same reason: one of them fails the call, which reads as "nothing changed" for every file in it. Pathspecs are also chunked to ~100KB of argv — 24k paths in one call overflows ARG_MAX on macOS, and `subprocess` raising `OSError` degrades to "nothing changed", i.e. every snooze permanent, which is what batching had to avoid in the first place.

### A tool that resolves symlinks now hard-fails its sensor

Anchoring refuses a path outside the project. A source tree symlinked in from outside the repo (`src/shared -> ../../shared-lib`) reported by a tool that resolves paths before printing them (`ruff` prints `/private/...` on macOS for exactly this reason) therefore fails that sensor — notice, findings dropped — where before it merely produced an unportable key. `project_relative` retries through `realpath` so a *project* reached via a symlink still anchors; a source tree pointing outside the project cannot, and there is no correct repo-relative name for it. Point the sensor at the real directory, or scope it out.

### knip runs a gated second pass in production mode (issue #59, rebuilt #99)

`plugins/typescript/src/habit_hooks_typescript/sensors/knip.cjs` runs knip twice when — and only when — the config marks production patterns with a trailing `!` on **both** `entry` and `project` (`configMarksProduction`, reading the JSON `knip.json`/`.knip.json`/`package.json#knip`; a jsonc/ts/js config JSON.parse cannot read falls back to a single pass so glob patterns like `src/**/*` are never mangled). The default pass is authoritative for every issue type; the `--production` pass contributes only the dead-code keys in `DEAD_CODE_KEYS` (`files`, `exports`, `types`, `nsExports`, `nsTypes`, `classMembers`, `enumMembers`), and only the items the default pass did not already name (deduped by `knipKey|file|name`). Those become a **separate** smell, `test-only-dead-code`, sourced `knip:production:<key>` — code alive only because a test references it, whose guide says to delete the test too. This is a different smell from the default pass's `unused-file` / `unused-export` on purpose: the two kinds have opposite fixes.

Gotchas: `--production` analyses NOTHING unless `!` is on BOTH `entry` and `project` (a no-`!` config under `--production` silently reports zero — so the gate never runs it there). Test files must be listed as unmarked (non-production) `entry`, not `ignore`, else code reached only by them looks unused to the *default* pass and is mis-coached as plainly dead — which is why the shipped `knip.json` lists `tests/**` and `src/**/*.{test,spec}.{ts,tsx}` as unmarked `entry`. As a belt-and-braces guard the production pass never contributes a **test file** itself (`isTestFile`/`TEST_FILE`): that pass drops test entries, so every test file looks unused to it, and reporting one would invite deleting real coverage. `classMembers`/`enumMembers` object maps are flattened before use so they never reach `.map` (the crash #99 fixed).

### A shipped ESM config resolves its imports from where it is, not from the project

`eslint --config <abs path>` reads the file from wherever habit-hooks is installed, and a bare `import` inside it resolves against **that** directory — for a consumer, a Python `site-packages` tree with no `node_modules` anywhere above it. `eslint.config.mjs` therefore died on `ERR_MODULE_NOT_FOUND: Cannot find package '@typescript-eslint/eslint-plugin'` the moment the sensor started naming it, while passing in this repo by pure luck of layout (`plugins/typescript/node_modules` is one of its ancestors). It now resolves its parser and plugin through `createRequire` anchored at `process.cwd()` — the project, which is where eslint itself came from (`spawn.py` puts `<project>/node_modules/.bin` on PATH). Any future config a plugin ships and passes by path needs the same treatment; ESM ignores `NODE_PATH`, so there is no environment-level escape.

The other half of that arrangement is knip's, and it is the opposite of jscpd's: knip resolves a config's relative `entry`/`project` globs against **cwd**, not against the config file, so the shipped `src/**` patterns still mean the consumer's tree when passed by absolute path.

### JSDoc nodes are not MultiLineCommentTrivia in ts-morph

`/** ... */` blocks are `SyntaxKind.JSDoc` (321) when attached to a declaration, NOT `MultiLineCommentTrivia`. To find them, query both — see `plugins/typescript/src/habit_hooks_typescript/sensors/comment.cjs`, which collects the two kinds separately for exactly this reason.

### A Node helper named `.js` lets the consumer pick its module system (issue #112)

Node never reads a `.js` file to decide whether it is CommonJS or ESM: it walks up from the script to the nearest `package.json` and reads `"type"` there. A CommonJS helper named `.js` therefore dies on its first line — `ReferenceError: require is not defined in ES module scope` — in any project declaring `"type": "module"`, the default a new TypeScript project is scaffolded with. The helper only lands inside that scope on the installs that put the package under the project directory: the vendoring route the README advertises (`.habit-hooks/<plugin>/sensors/`) and a project-local `.venv/`. `uv tool install`/`uvx` put it outside and escape by luck of layout, so neither reproduces the bug. Hence `sensors/knip.cjs` and `sensors/comment.cjs` — the extension settles the question inside the file, where a consumer's manifest cannot reach it, and it survives vendoring, which a sibling `{"type": "commonjs"}` `package.json` would not (it would have to be vendored too). Ship any future Node helper as `.cjs`, or as real ESM.





### Bumping pnpm 10 → 11 needs Corepack, not auto-switch

pnpm 11 split its launcher: the main `pnpm` npm package owns `dist/pnpm.mjs`, while `@pnpm/macos-arm64` (and siblings) ship only the native loader. pnpm 10's `packageManager` auto-switch fetches only the platform package, producing a binary missing its JS bootstrap — `Cannot find module .../dist/pnpm.mjs`. Bootstrap pnpm 11 via Corepack (`corepack prepare pnpm@<v> --activate`) or the official installer instead. The standalone shim at `~/Library/pnpm/pnpm` is from the old installer; once Corepack is on PATH, remove the shim so it stops shadowing it.





### An unmapped rule or code must never reach a bare lookup (issue #83)

A transform maps a tool-supplied string — an eslint rule ID, a ruff code — through a table of smells, and the tool is free to send a string no table has an entry for. In jq, `{"a": 1}[null]` answers null rather than aborting, but a lookup on a MISS must be spelled `// fallback` so the unmapped value passes through under its own name (#171) instead of dying or dropping silently. A program-side lookup uses `.get`/`Map.get` for the same reason: a plain object answers `map["constructor"]` off `Object.prototype`, and `JSON.stringify` then drops the finding's `smell` key with nothing in the run saying why.

### jscpd ignores a checkout that *lives* under a path its own `.gitignore` covers

jscpd's `initIgnore` turns each line of `<cwd>/.gitignore` into globs, and a line containing a slash becomes `**/<line>/**` — matched against the **absolute** paths a config-derived `path` produces, filesystem prefix and all. A checkout at `…/habit-hooks/.claude/worktrees/agent-x/` therefore ignores its entire self against this repo's own `.claude/worktrees/` line: zero files scanned, zero clones, exit 0, a clean run. Proven by two fixtures identical but for their path (ordinary → the planted clone; under `.claude/worktrees/` → nothing), and by running `jscpd` bare in a worktree, which is equally blind. It is the tool's behaviour, not the sensor's — and the sensor reproducing it exactly is the point of the precedence rule above.

The consequence for us: **inside an agent worktree `uv run habit-hooks --all` proves nothing about jscpd.** An ordinary checkout and CI are unaffected (no ignored segment in their paths). To check duplication from inside a worktree, run jscpd with positional relative paths, as the fallback branch does — and the reason `path` travels as positionals in `config_arguments` at all: jscpd resolves a config's relative `path` against the config file's directory, not the project's.

### A PMD `-R` spelling has two ways to analyse nothing

Never put a file positional directly after a `-R` value — PMD 7's picocli reads it as another ruleset and analyses nothing (hence short `-R` + per-file `-d` in `pmd_sensor.py`). And a new attached spelling (`-R=`) must be added to `ATTACHED_RULESET_PREFIXES` longest-first, or PMD silently unions two rulesets.

### A ruff.toml in a scanned subtree hijacks ruff's config discovery

ruff treats any file literally named `ruff.toml` as its own config. A `ruff check` whose upward config-discovery walk passes through a directory holding one loads it — the shipped `plugins/python/src/habit_hooks_python/ruff.toml` (thresholds for consumers who copy it) silently applies to any file scanned under it, shadowing the repo-root `[tool.ruff]`. (Its old sibling sensor spec `sensors/ruff.toml` — which hard-failed with `unknown field 'argv'` — died with the ruff helper's migration to the inline form.) Harmless in normal consumer operation — the file lives inside the habit-hooks package, off the consumer's discovery path — but a ruff run from inside that tree will be mystifying. Point ruff at an explicit `--config pyproject.toml` if you hit this — never a separate repo-root `ruff.toml`, which ruff prefers over `pyproject.toml` on every local run and will silently shadow (and drift from) the real `[tool.ruff]` config.

### Each released package needs its own publish environment

`.github/workflows/release.yml` maps every PyPI package to a distinct GitHub environment because a pending trusted publisher is unique by `(owner, repo, workflow, environment)` — two packages can't share one. A package new to PyPI also needs its pending publisher registered there before the tag, or its leg of the publish matrix fails while the rest succeed.

### The plugin floor is raised with the version, and the tap bump goes via a PR

Two things about a release that are silent when forgotten (agent decision):

- The core floors each plugin at the release's own minor, so every plugin specifier in the core's `pyproject.toml` moves on a minor bump. `pip install -U habit-hooks` upgrades a dependency only when the new core stops being satisfied by the installed one, so a floor left behind hands someone the new core with last release's plugins — where nearly every fix lives. `tests/test_the_plugin_floor_tracks_the_release.py` gates all three halves: the floor tracks the version, the release satisfies its own floors, and the plugins ship at it.
- The `habit-hooks/homebrew-tap` bump belongs in a **pull request**, not a push to its `main`. `brew test-bot` builds bottles either way, but `publish.yml` (`brew pr-pull`) attaches them from a PR number — pushed straight to main, 1.2.1 shipped with no bottles and every `brew install` builds from source.

### A `~=<minor>` floor cannot ship a release candidate (agent decision, #133/#134)

The floor is spelled `habit-hooks-<plugin>>=1.4.dev0,<2`, never `~=1.4`, and the reason only shows up at a tag. `~=1.4` **is** `>=1.4, ==1.*`, and by PEP 440 ordering `1.4.0rc1` sorts *below* `1.4` — so a release candidate declares floors its own plugins cannot satisfy, and `pip install habit-hooks==1.4.0rc1` dies with `Could not find a version that satisfies the requirement habit-hooks-generic~=1.4` while `1.4.0rc1` is sitting in the listed versions.

**No pre-release flag lifts it.** `--pre`, `--prerelease=allow` and `UV_PRERELEASE` were all measured and all ineffective: they are policy over *which candidates a resolver may consider*, and this is the specifier's own ordering excluding the version outright. Reach for the spelling, never a flag.

`>=1.4.dev0,<2` loosens **only** the release candidates of `1.4.0` itself. Compared version by version against `~=1.4`, the two answers differ on `1.4.dev0`, `1.4.0a1` and `1.4.0rc1` and agree everywhere else: `1.3.1` and `1.3.2rc1` are still refused, `1.4.1rc1` and `1.5.0rc1` were already admitted by `~=1.4`, and `2.0.0rc1` is still refused (PEP 440 forbids `<V` matching a pre-release of `V` itself). The same spelling serves the rc and the final release, so nothing is rewritten between them — which is the point, since a floor rewritten at the tag is a floor nobody tests.

The gate is `test_this_release_satisfies_the_floors_it_declares`, which asks `packaging`'s `SpecifierSet`/`Version` rather than reading the string — the same question pip asks, so it cannot answer differently.

### A sensor names the tool it wraps, and is handed the file that runs it

Windows' `CreateProcess` appends `.exe` to a bare command name and nothing else, while `shutil.which` applies `PATHEXT` — Node tools are `.cmd` shims and `pmd` a `.bat`, so anything spawning a tool by name answers "command not found" with the tool present. `project_paths.tool_executable` is the single lookup: a bare inline `tool` that names a declared `command` detector resolves through it, and `${detector:<name>}` expands to the same file. A tool declared and absent is answered before the spawn, and every argument is asked whether `cmd.exe` would read it (`batch_shell`), named tool included. A name no active plugin declares — or one declared `node-module` — is refused at load; `tests/test_a_plugin_declares_the_tools_it_names.py` reads each plugin's specs against its own declarations.

The TypeScript plugin's tools are `node-module` detectors and can never be spawned by name: `spawnSync` refuses `.cmd`/`.bat` outright (the CVE-2024-27980 mitigation, still unconditional in Node 22), and `shell: true` hands the argv to `cmd.exe` — hostile for filenames straight off a branch. `sensors/project_tool.cjs` finds the package under the project's own `node_modules` and runs its `bin` with `process.execPath`.

Why core placeholders rather than a shared module: plugins declare `dependencies = []` and may not import habit-hooks or a sibling — a recipe is data, and data crosses a boundary an import cannot. The trade: the core guards what it can see (the part's own arguments); an argument a program synthesises from them (a comma join, a per-file flag) is safe only because each path was checked against the named tool first.

### `TimeoutExpired` carries no partial output at all on Windows

A killed tool's own words are the whole value of the timeout notice, and they do not come back from the exception: POSIX hands over the partial reads, but on Windows each pipe is drained by a thread sitting in a single `read()` that returns only at EOF, so the buffer is still empty when the deadline passes. `sensors/deadline.py` therefore reads the pipe *after* the kill — the second `communicate()` from `subprocess`'s own docs — which is one answer for both platforms and the fuller one, since anything printed between the deadline and the kill is in it too. That read is bounded as well (`LAST_WORDS_TIMEOUT_SECONDS`): something the kill could not reach can still hold the far end open, and waiting on that forever is the hang the deadline exists to stop. When it does, the original expiry stands, which is why `part_output._as_text` still takes bytes.
