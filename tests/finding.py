from __future__ import annotations


def an_issue(key: str, *, file: str | None = None, **details: object) -> dict:
    issue_details = {**details}
    issue_details["file"] = key if file is None else file
    return {"key": key, "details": issue_details}


def a_finding(
    smell: str = "oversized-file",
    issues: list[dict] | None = None,
    *,
    details: dict | None = None,
    **extra: object,
) -> dict:
    return {
        "smell": smell,
        "details": details or {},
        "issues": issues or [],
        **extra,
    }
