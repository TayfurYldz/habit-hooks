
from __future__ import annotations

import io
import shlex
import sys
from pathlib import Path

import pytest
from plugin_fixture import write_plugin
from toml_text import toml_string

RAN = "ran.log"
PYTHON = shlex.quote(sys.executable)

FIRST = (
    f'{{ name = "wobble-one", kind = "command", '
    f'install = {toml_string(f"{PYTHON} mark.py one")} }}'
)
SECOND = (
    f'{{ name = "wobble-two", kind = "command", '
    f'install = {toml_string(f"{PYTHON} mark.py two")} }}'
)
FAILING = (
    f'{{ name = "wobble-bad", kind = "command", '
    f'install = {toml_string(f"{PYTHON} fail.py")} }}'
)


class Terminal(io.StringIO):

    def isatty(self) -> bool:
        return True


def needing(project_dir: Path, *entries: str) -> None:
    (project_dir / "mark.py").write_text(
        "import sys\n"
        f"open({RAN!r}, 'a', encoding='utf-8').write(sys.argv[1] + '\\n')\n",
        encoding="utf-8",
    )
    (project_dir / "fail.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    declared = f"detectors = [{', '.join(entries)}]"
    write_plugin(project_dir, "generic", {"config.toml": declared})


def answering(answer: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", Terminal(answer))


def ran(project_dir: Path) -> list[str]:
    log = project_dir / RAN
    return log.read_text(encoding="utf-8").split() if log.is_file() else []
