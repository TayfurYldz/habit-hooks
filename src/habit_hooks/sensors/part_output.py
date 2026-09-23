
from __future__ import annotations

import errno
import json
import re
import subprocess
from pathlib import Path

from .diagnosis import as_text, keep_both_ends
from .model import Part, SensorError

TOOL_EXIT_CODES = (0, 1)

COMMAND_NOT_FOUND = re.compile(r"(?:^|: )([^:\s]+): command not found$", re.MULTILINE)

COMMAND_NOT_FOUND_EXIT = 127


def parse_findings(stdout: str) -> list[dict]:
    text = stdout.strip()
    findings = json.loads(text) if text else []
    if not isinstance(findings, list):
        raise ValueError("output is not a findings array")
    return findings


def command_not_found(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        argv, COMMAND_NOT_FOUND_EXIT, "", f"{argv[0]}: command not found\n"
    )


def no_project_to_run_in(project_dir: Path) -> FileNotFoundError:
    return FileNotFoundError(
        errno.ENOENT, f"the project directory is gone: {project_dir}"
    )


def part_failure(
    kind: str, part: Part, result: subprocess.CompletedProcess[str]
) -> SensorError:
    missing = COMMAND_NOT_FOUND.search(result.stderr)
    if missing is not None:
        return _missing_tool(kind, part, missing[1])
    diagnosis = keep_both_ends(result.stderr.strip())
    return SensorError(
        f"{kind} {part.name!r} failed: {part.command_line}"
        + (f"\n{diagnosis}" if diagnosis else "")
    )


def _missing_tool(kind: str, part: Part, command: str) -> SensorError:
    return SensorError(
        f"{kind} {part.name!r} needs the {command!r} command, which is not "
        f"installed — install it, or {switch_off(kind, part.name)}"
    )


def switch_off(kind: str, name: str) -> str:
    if kind == "sensor":
        return f"disable the sensor with [sensors.{name}] disabled = true"
    return f"drop {name!r} from the root transformers list"


def part_timeout(
    kind: str, part: Part, expiry: subprocess.TimeoutExpired
) -> SensorError:
    diagnosis = keep_both_ends(as_text(expiry.stderr).strip())
    return SensorError(
        f"{kind} {part.name!r} timed out after {expiry.timeout:g}s: {part.command_line}"
        + (f"\n{diagnosis}" if diagnosis else "")
    )


def part_spawn_failure(kind: str, part: Part, refusal: OSError) -> SensorError:
    return SensorError(
        f"{kind} {part.name!r} could not run: {part.command_line}\n{refusal}"
    )


def sensor_crashed(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode not in TOOL_EXIT_CODES:
        return True
    return result.returncode != 0 and not result.stdout.strip()
