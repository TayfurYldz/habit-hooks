from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "habit_hooks_java"

sys.path.insert(0, str(PACKAGE))


@pytest.fixture(scope="session")
def pmd() -> str:
    found = shutil.which("pmd")
    if found is None:
        pytest.fail("pmd is not on PATH — 'brew install pmd'")
    return found
