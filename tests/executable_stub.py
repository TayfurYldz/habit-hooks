
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

_ON_WINDOWS = os.name == "nt"


def write_stub(bin_dir: Path, name: str, exit_code: int = 0) -> None:
    if _ON_WINDOWS:
        _write(bin_dir, f"{name}.cmd", f"@echo off\r\nexit /b {exit_code}\r\n")
        return
    _write_posix(bin_dir, name, f"#!/bin/sh\nexit {exit_code}\n")


def write_batch_stub(bin_dir: Path, name: str) -> Path:
    tool = bin_dir / f"{name}.cmd"
    if _ON_WINDOWS:
        _write(bin_dir, tool.name, "@echo off\r\nexit /b 0\r\n")
    else:
        _write_posix(bin_dir, tool.name, "#!/bin/sh\nexit 0\n")
    return tool


def write_wedged_tool(bin_dir: Path, name: str, seconds: int = 5) -> None:
    if _ON_WINDOWS:
        _write(
            bin_dir,
            f"{name}.cmd",
            f"@echo off\r\nping -n {seconds + 1} 127.0.0.1 >nul\r\n",
        )
        return
    _write_posix(bin_dir, name, f"#!/bin/sh\nexec /bin/sleep {seconds}\n")


def write_recording_tool(bin_dir: Path, name: str, log_name: str) -> None:
    if _ON_WINDOWS:
        _write_recording_windows(bin_dir, name, log_name)
        return
    _write_posix(
        bin_dir,
        name,
        f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "${{0%/*}}/{log_name}"\n'
        f'pwd >> "${{0%/*}}/{log_name}"\n',
    )


def _write_recording_windows(bin_dir: Path, name: str, log_name: str) -> None:
    log_path = bin_dir / log_name
    helper = bin_dir / f"_{name}_recorder.py"
    _write(
        bin_dir,
        helper.name,
        "import pathlib, sys\n"
        f"log = pathlib.Path({str(log_path)!r})\n"
        "log.write_text(\n"
        "    ' '.join(sys.argv[1:]) + '\\n' + str(pathlib.Path.cwd()) + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n",
    )
    _write(
        bin_dir,
        f"{name}.cmd",
        f'@echo off\r\n"{sys.executable}" "{helper}" %*\r\n',
    )


def _write(bin_dir: Path, filename: str, body: str) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / filename).write_text(body, encoding="utf-8")


def _write_posix(bin_dir: Path, name: str, body: str) -> None:
    _write(bin_dir, name, body)
    tool = bin_dir / name
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
