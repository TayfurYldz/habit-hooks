---
name: writing-docs
description: Write or trim habit-hooks documentation under docs/. Use when creating, editing, reviewing or cutting any doc in this repo — keeps docs user-facing, short, and example-first. Exemplar of a finished cut commit f79594fd.
---

# Writing habit-hooks docs

Everything in `docs/` is user-facing: it onboards a user (install → run → interpret output → configure) or a contributor extending the system. Short, extremely clear, executable examples as the main communication device.

The finished-cut exemplar: `git show f79594fd` — `docs/smell-vocabulary.md` went from 211 lines to 13. What survived: the catalogue table, severity semantics, how to propose a smell. What went: per-plugin translation tables, design rationale, edge-case essays.

## Properties of a doc

**Audience and purpose**
- One doc, one reader, one job — user onboarding or contributor extension. A doc serving both does neither well.
- Answers "what do I do", never "how did we decide". Rationale lives in PRs, commit messages and tests; mechanism walk-throughs live with the doc that owns them (architecture.md for the pipeline).
- Contribution sections state acceptance criteria ("name the smell by the problem it creates, not the tool"), not the reasoning behind them.

**Examples are the message**
- The executable example carries the meaning; prose between examples only supplies concepts and context the example can't show. A paragraph that re-explains what the example demonstrates gets deleted.
- Examples run as written — the spec harness enforces it, which is why examples are the safest device: they can't rot, prose can.
- `*.spec.md` files are documentation first, tests as a side effect. Trimming prose around cases is a docs change; deleting or editing cases changes test coverage and goes through normal test review, not a docs cut.

**Stays true**
- Contains nothing code can answer. State inventories — which tool maps to which smell, which plugins ship which sensors — go stale the release after they're written; link to where the truth lives instead of copying it.
- Each fact stated once. Cross-reference instead of restating; duplicated explanations drift apart.

**Length**
- Every sentence carries a fact the reader acts on. First cut: history, edge-case essays, "deliberate exception" narratives.
- Lead with the organising fact as a definition, in the fewest words. Never advertise what the doc lets you do — that restates the sections and reads as a sales pitch.
- One sitting per doc. A doc that needs a table of contents wants to be two docs — or its headlines to carry their promises, not an index table to carry them.

**Format**
- No hard newlines inside a paragraph; let the editor soft-wrap.

**Boundaries**
- Core docs are plugin-agnostic, same rule as the core code (see AGENTS.md). Per-plugin detail lives in the plugin.
- Concepts defined before first use. "Sensor", "mapper", "smell" mean the same thing in every doc.

## The process — writing or fixing any doc

Run these in order, before writing prose or cutting it. A doc that skips a step is why a reader bounces off it (`docs/config.md` before its 2026-09 rework: no audience, no promise, mechanism-named sections).

1. **Decide who the audience is.** One doc, one reader, one job. Signal it by talking to that reader — never announce who the doc is for, and never narrate what the reader just did ("you open this page to…").
2. **Phrase the reader's expectation on opening it** — one sentence: "I will find out how to disable a rule I don't agree with." If it takes two sentences, the doc has two jobs: split it.
3. **Make the headlines deliver on those expectations.** Name the problem being solved, never the mechanism — not the design name (`## Advanced configuration`) and not the syntax (`[smells.<name>]`): `## Silence or demote a smell`. If a headline can't carry its promise, rename the headline — don't paper over it with a task index.
4. **Make the first paragraph summarise the content and place the doc in context.** The summary itself tells the right reader they are in the right place.
5. **Write each section to deliver on the promise of its headline** — and only that promise. Deliver with executable examples; reference data is a bullet list, `- **key**: description`, never a table and never prose.

## Cutting an existing doc

Fix structure first with the process (audience → expectation → headlines → first paragraph → sections), then cut prose.

1. Delete every sentence whose absence changes nothing the reader does or understands.
2. Delete state inventories code already answers; link to the truth instead.
3. Move per-plugin detail to the plugin, and mechanism walk-throughs to the doc that owns them.
4. If two distinct readers or jobs remain, split into two docs.
5. Keep: reference tables the reader looks up, acceptance criteria, executable examples.

Check: read only the examples — does the doc still teach its job? Then read the prose; anything the examples already said is gone.

Cross-reference other docs with a link, never a summary.

## Before handing over

For every line, ask as the reader with a task in hand, not the writer who wrote it: does the user need this — and is this the one place it is said? Repeated anywhere else, or nothing the user does depends on it → delete.

Intuitive rules (precedence, who-wins) are stated once, at the end, for the reader checking their intuition — never inline at each point of possible conflict.

Examples that demonstrate a default show nothing; the default is already stated. Delete them.
