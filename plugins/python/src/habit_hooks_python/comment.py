from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

COMMENT_MINIMUM = 10
DOCSTRING_MINIMUM = 15
EXEMPT_PREFIXES = ("#!", "# type:", "# noqa", "# pylint:", "# -*-")


def comment_issues(source: str, file: str) -> list[dict]:
    issues = []
    for number, line in enumerate(source.splitlines(), 1):
        text = line.strip()
        if not text.startswith("#") or text.startswith(EXEMPT_PREFIXES):
            continue
        if len(text) >= COMMENT_MINIMUM:
            issues.append(occurrence(file, number, text))
    return issues


DOCSTRING_NODES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def docstring_issues(source: str, file: str) -> list[dict]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    issues = []
    for node in ast.walk(tree):
        if not isinstance(node, DOCSTRING_NODES):
            continue
        docstring = ast.get_docstring(node)
        if docstring and len(docstring.strip()) >= DOCSTRING_MINIMUM:
            issues.append(occurrence(file, node.body[0].lineno, docstring))
    return issues


def occurrence(file: str, line: int, text: str) -> dict:
    message = " ".join(text.split())
    return {
        "key": file,
        "details": {
            "file": file,
            "line": line,
            "message": message[:50],
            "source": "comment",
        },
    }


def findings(files: list[str]) -> list[dict]:
    issues = []
    for name in files:
        source = Path(name).read_text(encoding="utf-8", errors="replace")
        issues.extend(comment_issues(source, name))
        issues.extend(docstring_issues(source, name))
    if not issues:
        return []
    return [{"smell": "non-essential-comment", "details": {}, "issues": issues}]


def main() -> int:
    print(json.dumps(findings(sys.argv[1:])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
