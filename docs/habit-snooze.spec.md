# habit-snooze — the snooze transformer

Snoozing is a **transformer** ([architecture.md](architecture.md)): a
`findings → findings` step that drops the issues a project has chosen to ignore
and passes everything else through. It sits at the outermost level of the run,
where it sees every finding.

What it drops is decided by a small, checked-in **index** of snoozed keys. An
issue is snoozed when its `key` is in the index. Because `key` defaults to the
filename ([sensor-interface.spec.md](sensor-interface.spec.md)), snoozing a key
snoozes a whole file's issues at once — and a sensor that wants finer control
just chooses a finer `key`. A key that is a filename is one the runner has
already anchored to the project, so an index recorded here matches on a
teammate's checkout and in CI.

Two rules cover the whole transform:

- **Drop snoozed issues, keep the rest.** Within a finding, each issue whose
  `key` is in the index is removed; the others stay.
- **A finding with no issues left is dropped.** When the last issue goes, the
  finding goes with it.

The `--snooze` / `--prune` / `--list` commands maintain the index. They are the
only things that write it; the transform itself only reads it.

A snooze records the **approved content**: `--snooze` stores, per file the key
is anchored to, the content that file held, and an issue stays dropped only
while its file still holds it. Editing the file brings its issues back, and
`--snooze` again approves what is there now — described
[below](#an-edited-file-brings-its-issues-back-until-it-is-approved-again). The
`snooze-until-changed` transformer is kept as a deprecated alias of `snooze`:
what it was the opt-in for is the only behaviour.

## An unsnoozed issue passes through

With an empty index, every finding survives untouched.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze | jq .
```

🖥️ ✅
```json
[
  {
    "smell": "loose-equality",
    "details": {
      "maxAllowed": 0
    },
    "issues": [
      {
        "key": "src/x.ts",
        "details": {
          "file": "src/x.ts",
          "line": 1
        }
      }
    ]
  }
]
```

## `--snooze` records an issue's key into the index

`--snooze` reads the findings on stdin and adds each issue's `key` to the index.
`--list` then shows what is snoozed.

An entry also records the approved content of each file the key is anchored
to — `{"key": "src/x.ts", "anchors": {"src/x.ts": "sha256:…"}}` — which is what
lets a later `--snooze`
[approve it again](#an-edited-file-brings-its-issues-back-until-it-is-approved-again). It
remembers per file, because a key does not always stand for exactly one
([sensor-interface.spec.md](sensor-interface.spec.md)). A key with nothing to
record — an anchor that is no file on disk — is written as a bare string
instead. `--list` shows the keys either way.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze --snooze && habit-snooze --list
```

🖥️ ✅
```text
src/x.ts
```

## A snoozed issue is dropped from its finding

A finding with two issues loses the snoozed one and keeps the other.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze --snooze
```

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } },
      { "key": "src/y.ts", "details": { "file": "src/y.ts", "line": 9 } }
    ]
  }
]
```

```bash
habit-snooze | jq .
```

🖥️ ✅
```json
[
  {
    "smell": "loose-equality",
    "details": {
      "maxAllowed": 0
    },
    "issues": [
      {
        "key": "src/y.ts",
        "details": {
          "file": "src/y.ts",
          "line": 9
        }
      }
    ]
  }
]
```

## A finding loses its only issue and disappears

When the snoozed key was the finding's last issue, the whole finding is dropped —
the output is an empty array, not a finding with an empty `issues` list.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze --snooze
```

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze | jq .
```

🖥️ ✅
```json
[]
```

## An entry that records nothing keeps holding

An entry written before approvals were recorded — a bare key — cannot be
contradicted, so it keeps holding however the file changes, until the next
`--snooze` records it. A project upgrading therefore never finds its existing
snoozes re-arming on their own; each one arms the first time it is approved
again.

The file here is edited after the index was written, and the issue stays
dropped.

📄src/x.ts
```ts
export const equal = (a, b) => a == b;
```

📄.habit-hooks/snooze.json
```json
["src/x.ts"]
```

```bash
printf 'export const extra = 1;\n' >> src/x.ts
```

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
[]
```

## An empty index changes nothing

Snooze runs by default ([habit-sensors.spec.md](habit-sensors.spec.md)), so a
project that has never snoozed anything must get its findings back byte for
byte. Dropping happens only where a key matched: a finding that arrives with no
issues has nothing snoozed in it and passes through, unlike one whose last issue
*was* snoozed above.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  },
  {
    "smell": "duplicated-code",
    "details": {},
    "issues": []
  }
]
```

```bash
habit-snooze | jq .
```

🖥️ ✅
```json
[
  {
    "smell": "loose-equality",
    "details": {
      "maxAllowed": 0
    },
    "issues": [
      {
        "key": "src/x.ts",
        "details": {
          "file": "src/x.ts",
          "line": 1
        }
      }
    ]
  },
  {
    "smell": "duplicated-code",
    "details": {},
    "issues": []
  }
]
```

## `--prune` reads a snooze-free view of the run

A snoozed key whose issue no longer shows up — the smell was fixed, or the file
deleted — is stale, and `--prune` drops it. But `--prune` must read the findings
**before** the snooze transformer filtered them: the default pipe has already
stripped every snoozed issue, so a naive `--prune` would see none of them and
empty the whole index (#94). The documented pipeline therefore runs
`habit-sensors --no-snooze`, so `--prune` compares the index against everything
the run still finds — snoozed or not.

These cases drive that real pipeline through a stub sensor rather than hand-fed
findings, so the bypass that hid the bug cannot come back. Discovery is opt-in
(#97), so the config names a scope; `["**"]` is every file the case writes.

📄.habit-hooks/config.toml
```toml
plugins = ["generic"]
files   = ["**"]
```

📄.habit-hooks/generic/config.toml
```toml
sensors = ["alpha"]
```

📄.habit-hooks/generic/sensors/alpha.toml
```toml
command = "cat ${dir}/alpha.json"
```

### It keeps a still-violating key and drops one that no longer appears

Two keys are snoozed, but the run only still reports `src/x.ts` (the `src/y.ts`
smell was fixed). Pruning keeps `src/x.ts` and reaps `src/y.ts`.

📄.habit-hooks/generic/sensors/alpha.json
```json
[{"smell":"loose-equality","details":{"maxAllowed":0},"issues":[{"key":"src/x.ts","details":{"file":"src/x.ts","line":1}}]}]
```

📄.habit-hooks/snooze.json
```json
["src/x.ts", "src/y.ts"]
```

```bash
habit-sensors --all --no-snooze | habit-snooze --prune && habit-snooze --list
```

🖥️ ✅
```text
src/x.ts
```

### It refuses to empty a populated index when the run measured nothing

An empty run means "nothing was measured", not "every exemption is obsolete", so
`--prune` refuses to touch a populated index and says why (the false-clean class
of #78/#84). Here the sensor reports nothing, yet the snooze survives.

📄.habit-hooks/generic/sensors/alpha.json
```json
[]
```

📄.habit-hooks/snooze.json
```json
["src/x.ts"]
```

```bash
habit-sensors --all --no-snooze | habit-snooze --prune
```

🖥️ ❌ 1

```bash
habit-snooze --list
```

🖥️ ✅
```text
src/x.ts
```

## `--list` shows the index

`--list` prints the snoozed keys, one per line, so the checked-in index is
reviewable without reading the file by hand.

⌨️
```json
[
  {
    "smell": "loose-equality",
    "details": { "maxAllowed": 0 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "line": 1 } },
      { "key": "src/y.ts", "details": { "file": "src/y.ts", "line": 9 } }
    ]
  }
]
```

```bash
habit-snooze --snooze && habit-snooze --list
```

🖥️ ✅
```text
src/x.ts
src/y.ts
```

## A corrupt index fails the tool, not the code

The index is a checked-in file people edit by hand, so a broken one is a failure
of the tool itself — not a finding about the code. It exits **2**, the code
[habit-sensors.spec.md](habit-sensors.spec.md) already uses for a rejected config
or an unresolvable base ref, and names the file and what it expected on stderr.
The `--prune` refusal above is the other kind — a judgement about the run — and
keeps exit 1.

📄.habit-hooks/snooze.json
```json
{"src/x.ts": "why"}
```

```bash
habit-snooze --list 2>&1 >/dev/null | sed 's| /.*/\.habit-hooks/| .habit-hooks/|'
```

🖥️ ❌ 2
```text
habit-snooze: .habit-hooks/snooze.json: expected a JSON list of snoozed entries, got an object
```

## An edited file brings its issues back until it is approved again

A snooze is a record of the approved content, so a snoozed issue is not dropped
unconditionally: change the file and its issue is due again, whether the edit is
committed or not. Running `--snooze` approves what is there now, and the finding
is dropped until the next edit.

Nothing here needs a git repository. The index is checked in, so whoever
changes a file approves it in the same change: file and record travel together,
and work someone else lands can never lapse a snooze on your side.

An issue is anchored to the file in its `details.file`, falling back to its
`key`. An entry that records nothing — written by an older version, or for an
anchor that is no file on disk — cannot be contradicted and keeps holding, as
[above](#an-entry-that-records-nothing-keeps-holding).

Every case below starts from the same state: two files, with `src/x.ts` approved
through the real command.

📄src/x.ts
```ts
export const equal = (a, b) => a == b;
```

📄src/other.ts
```ts
export const untouched = 1;
```

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze --snooze
```

### An approved file stays snoozed

The file is byte for byte what was approved, so the snooze still applies and its
only issue is dropped.

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
[]
```

### An edit brings the issue back

Nothing is committed here — it would make no difference. The file no longer
holds what was approved, and the issue is due again.

```bash
printf 'export const extra = 1;\n' >> src/x.ts
```

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
["src/x.ts"]
```

### `--snooze` approves what is there now

The answer is still the one given last time, so give it again: the entry records
the file as it stands, and the finding is dropped until the next edit.

```bash
printf 'export const extra = 1;\n' >> src/x.ts
```

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
["src/x.ts"]
```

```bash
habit-snooze --snooze && habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
[]
```

The next edit asks again: what was approved was that state of the file.

```bash
printf 'export const more = 2;\n' >> src/x.ts
```

⌨️
```json
[
  {
    "smell": "oversized-file",
    "details": { "maxAllowed": 200 },
    "issues": [
      { "key": "src/x.ts", "details": { "file": "src/x.ts", "lines": 251 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
["src/x.ts"]
```

### The snooze is anchored to `details.file`, not to the key

A sensor keys an issue by whatever groups it best — `deptry` by module name,
`knip` by export name ([sensor-interface.spec.md](sensor-interface.spec.md)) —
so the file to approve comes from `details.file`. The key below is a module
name, not a path on disk, and the snooze still lapses when `src/x.ts` changes.

⌨️
```json
[
  {
    "smell": "unused-dependency",
    "details": {},
    "issues": [
      { "key": "requests", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze --snooze
```

```bash
printf 'export const stale = 3;\n' >> src/x.ts
```

⌨️
```json
[
  {
    "smell": "unused-dependency",
    "details": {},
    "issues": [
      { "key": "requests", "details": { "file": "src/x.ts", "line": 1 } }
    ]
  }
]
```

```bash
habit-snooze | jq -c '[.[].issues[].key]'
```

🖥️ ✅
```json
["requests"]
```

### An anchor that is no file records nothing

A key that is not a path has nothing to record, so its entry is written bare and
keeps the behaviour it had: it holds until someone takes it out of the index.

⌨️
```json
[
  {
    "smell": "unused-dependency",
    "details": {},
    "issues": [
      { "key": "SomeExport", "details": {} }
    ]
  }
]
```

```bash
habit-snooze --snooze && jq -c 'map(if type == "object" then {key: .key, anchors: (.anchors | keys)} else . end)' .habit-hooks/snooze.json
```

🖥️ ✅
```json
["SomeExport",{"key":"src/x.ts","anchors":["src/x.ts"]}]
```

The entry for `SomeExport` records no content, so it holds whatever the run
asks of it; the approved entry keeps its recording.
