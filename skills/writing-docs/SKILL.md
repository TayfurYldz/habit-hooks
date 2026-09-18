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
- Answers "what do I do", never "how did we decide". Rationale lives in PRs, commit messages and tests.
- Contribution sections state acceptance criteria ("name the smell by the problem it creates, not the tool"), not the reasoning behind them.

**Examples are the message**
- The executable example carries the meaning; prose between examples only supplies concepts and context the example can't show. A paragraph that re-explains what the example demonstrates gets deleted.
- Examples run as written — the spec harness enforces it, which is why examples are the safest device: they can't rot, prose can.
- `*.spec.md` files are documentation first, tests as a side effect. Trimming prose around cases is a docs change; deleting or editing cases changes test coverage and goes through normal test review, not a docs cut.

**Stays true**
- Contains nothing code can answer. State inventories — which tool maps to which smell, which plugins ship which sensors — go stale the release after they're written; link to where the truth lives instead of copying it.
- Each fact stated once. Cross-reference instead of restating; duplicated explanations drift apart.

**Length**
- Every sentence changes what the reader does or understands. First cut: history, edge-case essays, "deliberate exception" narratives.
- One sitting per doc. A doc that needs a table of contents wants to be two docs.

**Boundaries**
- Core docs are plugin-agnostic, same rule as the core code (see AGENTS.md). Per-plugin detail lives in the plugin.
- Concepts defined before first use. "Sensor", "mapper", "smell" mean the same thing in every doc.

## Cutting an existing doc

1. Delete every sentence whose absence changes nothing the reader does or understands.
2. Delete state inventories code already answers; link to the truth instead.
3. Move per-plugin detail to the plugin.
4. If two distinct readers or jobs remain, split into two docs.
5. Keep: reference tables the reader looks up, acceptance criteria, executable examples.

Check: read only the examples — does the doc still teach its job? Then read the prose; anything the examples already said is gone.

## Writing a new doc

- Start from an executable example that does the job end to end; add prose only where a concept needs naming before the next example.
- Reference data is a table, not sentences.
- Cross-reference other docs with a link, never a summary.
