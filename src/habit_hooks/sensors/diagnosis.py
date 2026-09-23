
from __future__ import annotations

DIAGNOSIS_LINE_LIMIT = 20

DIAGNOSIS_LINE_LENGTH_LIMIT = 1_000


def as_text(output: str | bytes | None) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output or ""


def keep_both_ends(diagnosis: str) -> str:
    lines = diagnosis.splitlines()
    kept = [_both_ends_of(line) for line in _the_lines_worth_keeping(lines)]
    return diagnosis if kept == lines else "\n".join(kept)


def _the_lines_worth_keeping(lines: list[str]) -> list[str]:
    head = DIAGNOSIS_LINE_LIMIT // 2
    tail = DIAGNOSIS_LINE_LIMIT - head
    omitted = len(lines) - head - tail
    excerpt = [*lines[:head], f"... {omitted} lines omitted ...", *lines[-tail:]]
    return excerpt if len(excerpt) < len(lines) else lines


def _both_ends_of(line: str) -> str:
    head = DIAGNOSIS_LINE_LENGTH_LIMIT // 2
    tail = DIAGNOSIS_LINE_LENGTH_LIMIT - head
    omitted = len(line) - head - tail
    excerpt = f"{line[:head]}... {omitted} characters omitted ...{line[-tail:]}"
    return excerpt if len(excerpt) < len(line) else line
