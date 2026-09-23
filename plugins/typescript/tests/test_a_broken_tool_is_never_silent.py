from __future__ import annotations

from pathlib import Path

from project_tool_probe import a_project_whose_tool, ask_the_seam, judge

SAYS_NOTHING = "process.exit(2);\n"
COMPLAINS = 'process.stderr.write("knip.json: line 3 is nonsense\\n");\nprocess.exit(2);\n'

A_SPAWN_THAT_DIED = {
    "status": None,
    "signal": "SIGTERM",
    "error": {"message": "spawnSync /usr/local/bin/node ENOBUFS"},
    "stdout": '[{"filePath":"/p/src/a.ts","mess',
    "stderr": "",
}

A_SPAWN_THAT_NEVER_STARTED = {
    "status": None,
    "signal": None,
    "error": {"message": "spawnSync /usr/local/bin/node E2BIG"},
    "stdout": None,
    "stderr": None,
}

A_SPAWN_THAT_DIED_AFTER_SPEAKING = {
    **A_SPAWN_THAT_DIED,
    "stderr": "Invalid configuration: 'entry' must be an array\n",
}


def _broke_at(tmp_path: Path, tool: str, exit_code: int) -> bool:
    project = a_project_whose_tool(tmp_path, tool, f"process.exit({exit_code});\n")
    return ask_the_seam(project, tool)["broke"]


def test_a_tool_that_failed_without_a_word_is_named_along_with_its_exit(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "wordless", SAYS_NOTHING)

    answer = ask_the_seam(project, "wordless")

    assert answer["broke"] is True
    assert answer["complaint"] == "wordless: exited 2 without a word of its own\n"


def test_a_tool_that_diagnosed_itself_is_quoted_in_its_own_words(
    tmp_path: Path,
) -> None:
    project = a_project_whose_tool(tmp_path, "knip", COMPLAINS)

    answer = ask_the_seam(project, "knip")

    assert answer["complaint"] == "knip.json: line 3 is nonsense\n"


def test_the_words_a_tool_got_out_outrank_the_spawns_own_error(
    tmp_path: Path,
) -> None:
    answer = judge(tmp_path, "knip", A_SPAWN_THAT_DIED_AFTER_SPEAKING)

    assert answer["broke"] is True
    assert answer["complaint"] == A_SPAWN_THAT_DIED_AFTER_SPEAKING["stderr"]


def test_a_spawn_that_died_without_words_names_the_tool_not_the_runtime(
    tmp_path: Path,
) -> None:
    answer = judge(tmp_path, "noisy", A_SPAWN_THAT_DIED)

    assert answer["broke"] is True
    assert answer["complaint"].startswith("noisy: ")
    assert "ENOBUFS" in answer["complaint"]


def test_a_tool_nobody_installed_is_named_once_in_the_shells_own_phrase(
    tmp_path: Path,
) -> None:
    project = tmp_path / "bare"
    project.mkdir()
    (project / "package.json").write_text('{"name": "demo"}', encoding="utf-8")

    answer = ask_the_seam(project, "eslint")

    assert answer["complaint"] == "eslint: command not found\n"


def test_a_findings_exit_is_not_breakage(tmp_path: Path) -> None:
    assert _broke_at(tmp_path, "clean", 0) is False
    assert _broke_at(tmp_path, "reporting", 1) is False
    assert _broke_at(tmp_path, "broken", 2) is True


def test_a_spawn_that_never_started_is_answered_rather_than_read(
    tmp_path: Path,
) -> None:
    answer = judge(tmp_path, "eslint", A_SPAWN_THAT_NEVER_STARTED)

    assert answer["broke"] is True
    assert answer["complaint"].startswith("eslint: ")
    assert "E2BIG" in answer["complaint"]
