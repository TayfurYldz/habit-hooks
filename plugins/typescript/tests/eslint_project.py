from __future__ import annotations

import json
import os
import subprocess
import tomllib
from pathlib import Path

PLUGIN = Path(__file__).parents[1]
PACKAGE = PLUGIN / "src" / "habit_hooks_typescript"
SENSORS = PACKAGE / "sensors"
SHIPPED_CONFIG = PACKAGE / "eslint.config.mjs"
ESLINT = PLUGIN / "node_modules" / "eslint" / "bin" / "eslint.js"

MANIFEST = '{ "name": "demo", "version": "0.0.0" }\n'

REPOSITORY_TS = """export interface Repository {
  save(item: string): void;
  find(id: string): string;
}

export function total(prices: number[]): number {
  const unusedTax = 0.2;
  return prices.length;
}
"""
UNUSED_LOCAL_LINE = 7


def project(tmp_path: Path) -> Path:
    created = tmp_path / "demo"
    (created / "src").mkdir(parents=True)
    (created / "package.json").write_text(MANIFEST, encoding="utf-8")
    (created / "node_modules").symlink_to(PLUGIN / "node_modules")
    (created / "src" / "repository.ts").write_text(REPOSITORY_TS, encoding="utf-8")
    return created


def run(project: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    path = f"{project / 'node_modules' / '.bin'}{os.pathsep}{os.environ['PATH']}"
    return subprocess.run(
        argv,
        cwd=project,
        env={**os.environ, "PATH": path},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def report(
    project: Path,
    files: tuple[str, ...] = ("src/repository.ts",),
    config: Path = SHIPPED_CONFIG,
) -> str:
    result = run(
        project,
        [
            "node",
            str(ESLINT),
            "-f",
            "json",
            "--no-warn-ignored",
            "--config",
            str(config),
            *files,
        ],
    )
    assert result.stdout, result.stderr
    return result.stdout


def messages(project: Path, config: Path) -> list[dict]:
    return json.loads(report(project, config=config))[0]["messages"]


def sensor_argv(
    files: tuple[str, ...] = ("src/repository.ts",),
    args: tuple[str, ...] = (),
) -> list[str]:
    config = tomllib.loads((PACKAGE / "config.toml").read_text(encoding="utf-8"))
    entry = next(e for e in config["sensors"] if e.get("name") == "eslint")
    argv = [entry["tool"], *entry["args"]]
    lists = {"${args}": list(args), "${files}": list(files)}
    return [
        argument
        for element in argv
        for argument in lists.get(element, [element.replace("${dir}", str(PACKAGE))])
    ]


def sensor_run(
    project: Path,
    files: tuple[str, ...] = ("src/repository.ts",),
    args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    return run(project, sensor_argv(files, args))


def sensor_findings(
    project: Path,
    files: tuple[str, ...] = ("src/repository.ts",),
    args: tuple[str, ...] = (),
) -> list[dict]:
    result = sensor_run(project, files, args)
    assert result.stdout, result.stderr
    return json.loads(result.stdout)
