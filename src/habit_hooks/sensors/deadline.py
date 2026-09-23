
from __future__ import annotations

import subprocess

from .live_commands import kill_command

DEFAULT_SENSOR_TIMEOUT_SECONDS = 300.0

LAST_WORDS_TIMEOUT_SECONDS = 5.0


def bounded_output(
    process: subprocess.Popen[str], stdin: str, timeout: float
) -> subprocess.CompletedProcess[str]:
    try:
        stdout, stderr = process.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired as expiry:
        kill_command(process.pid)
        raise _with_last_words(process, expiry) from None
    except KeyboardInterrupt:
        kill_command(process.pid)
        raise
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def _with_last_words(
    process: subprocess.Popen[str], expiry: subprocess.TimeoutExpired
) -> subprocess.TimeoutExpired:
    try:
        stdout, stderr = process.communicate(timeout=LAST_WORDS_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return expiry
    return subprocess.TimeoutExpired(process.args, expiry.timeout, stdout, stderr)
