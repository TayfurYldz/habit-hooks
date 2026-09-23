from __future__ import annotations

import json
from pathlib import Path

ARGV_LOG = "argv.log"
REPORT = "report.json"

RECORDER = """const fs = require("node:fs");
const path = require("node:path");
const installed = path.join(__dirname, "..");
fs.appendFileSync(
  path.join(installed, "{log}"),
  `${{process.argv.join("\\t")}}\\n`,
);
process.stdout.write(fs.readFileSync(path.join(installed, "{report}"), "utf8"));
"""


def install_script(project: Path, tool: str, cli: str) -> Path:
    package = project / "node_modules" / tool
    (package / "bin").mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({"name": tool, "version": "0.0.0", "bin": {tool: f"bin/{tool}.js"}}),
        encoding="utf-8",
    )
    (package / "bin" / f"{tool}.js").write_text(cli, encoding="utf-8")
    return package


def install(project: Path, tool: str, prints: str) -> Path:
    package = install_script(project, tool, RECORDER.format(log=ARGV_LOG, report=REPORT))
    (package / REPORT).write_text(prints, encoding="utf-8")
    return package


def entry_script(project: Path, tool: str) -> Path:
    return project / "node_modules" / tool / "bin" / f"{tool}.js"


def spawns(project: Path, tool: str) -> list[list[str]]:
    log = project / "node_modules" / tool / ARGV_LOG
    if not log.is_file():
        return []
    return [line.split("\t") for line in log.read_text(encoding="utf-8").splitlines()]
