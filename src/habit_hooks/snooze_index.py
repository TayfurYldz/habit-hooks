"""The checked-in snooze index: load it safely, save it atomically.

Split from ``snooze.py`` so the index file I/O — parsing a JSON file a human
edits, and replacing it without tearing under concurrent hook runs — lives apart
from the transform and its CLI.

An entry is a key and the content approved for each file it covers. An
entry that records nothing stays a bare key, so an index written before that
keeps loading and a project migrates one ``--snooze`` at a time.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

INDEX_PATH = Path(".habit-hooks") / "snooze.json"

# The files an entry was approved against, each mapped to the content it held
# then. Empty for an entry written before that field existed, and for one whose anchor is no
# file to read.
Anchors = dict[str, str]

# What `load_index` hands the rest of the tool: every snoozed key, with what it
# was approved against.
Index = dict[str, Anchors]


class SnoozeError(Exception):
    """A malformed snooze index — a checked-in file a human edits, so it fails by
    name rather than as a traceback or, worse, a silent misread."""


def load_index(project_dir: Path) -> Index:
    path = project_dir / INDEX_PATH
    if not path.exists():
        return {}
    return _parse_index(path)


def _parse_index(path: Path) -> Index:
    """The index is a JSON list of entries: a bare key, or that key with the
    content approved for each file it covers. Anything else fails by name.

    Left untyped, ``null`` iterated as ``None``, a bare ``"src/a.py"`` iterated
    per character, and ``{"key": "reason"}`` survived only to be flattened to a
    bare list on the next ``--snooze`` — each a silent way to mean nothing.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnoozeError(f"{path}: not valid JSON ({exc})") from exc
    if not isinstance(data, list):
        raise SnoozeError(
            f"{path}: expected a JSON list of snoozed entries, got {_describe(data)}"
        )
    return dict(_entry(path, item) for item in data)


def _entry(path: Path, item: object) -> tuple[str, Anchors]:
    """One entry as a mapping pair: a bare key, or that key with its anchors.

    A key beside a field the index has no meaning for is refused rather than
    read and dropped on the next write — the silent flattening above, in the
    shape it takes now that an entry can be an object.
    """
    if isinstance(item, str):
        return item, {}
    if (
        isinstance(item, dict)
        and isinstance(item.get("key"), str)
        and _is_anchors(item.get("anchors", {}))
        and not set(item) - {"key", "anchors"}
    ):
        return item["key"], item.get("anchors", {})
    raise SnoozeError(
        f"{path}: expected each entry to be a snoozed key, or an object with "
        f'"key" and an optional "anchors", got {_describe(item)}'
    )


def _is_anchors(anchors: object) -> bool:
    return isinstance(anchors, dict) and all(
        isinstance(anchor, str) and isinstance(content, str)
        for anchor, content in anchors.items()
    )


def _describe(data: object) -> str:
    if isinstance(data, list):
        return "a list with a malformed entry"
    return {dict: "an object", str: "a bare string", type(None): "null"}.get(
        type(data), type(data).__name__
    )


def save_index(entries: Index, project_dir: Path) -> None:
    path = project_dir / INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    written = [_written(key, entries[key]) for key in sorted(entries)]
    _replace_atomically(path, json.dumps(written) + "\n")


def _written(key: str, anchors: Anchors) -> str | dict:
    """An entry recording nothing stays the bare key it always was, so an index
    nothing has approved into keeps the shape its project knows. Anchors are
    sorted along with the keys, so a file written on one line still reviews as a
    stable diff."""
    if not anchors:
        return key
    return {"key": key, "anchors": dict(sorted(anchors.items()))}


def _replace_atomically(path: Path, content: str) -> None:
    """Write a sibling temp file, then ``os.replace`` it over ``path``.

    Two concurrent hook runs that read-modify-write the index otherwise tear it;
    the rename is atomic on POSIX, so a reader sees the old file or the whole new
    one. The pid keeps the two writers' temp files apart.
    """
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
