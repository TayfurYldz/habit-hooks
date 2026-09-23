from __future__ import annotations

from collections.abc import Callable

import pytest


def refusal_from(load: Callable[[], object]) -> str:
    with pytest.raises(SystemExit) as failure:
        load()
    return str(failure.value)
