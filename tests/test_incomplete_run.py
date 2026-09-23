
from __future__ import annotations

from habit_hooks.catalogue import INCOMPLETE_RUN
from habit_hooks.sensors import incomplete_run_finding


def test_each_notice_becomes_a_coachable_issue() -> None:
    notices = [
        "habit-sensors: sensor 'comment' failed: boom",
        "habit-sensors: transformer 'snooze' failed: exit 1",
    ]

    finding = incomplete_run_finding(notices)

    assert finding["smell"] == INCOMPLETE_RUN
    assert [issue["details"]["content"] for issue in finding["issues"]] == notices
    assert [issue["key"] for issue in finding["issues"]] == notices


def test_no_notices_yields_no_issues() -> None:
    finding = incomplete_run_finding([])

    assert finding["smell"] == INCOMPLETE_RUN
    assert finding["issues"] == []
