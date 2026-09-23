
from __future__ import annotations

import os
import shutil


def where_the_bare_name_reaches_nothing(name: str) -> dict[str, str]:
    path = os.pathsep.join(
        entry
        for entry in os.environ["PATH"].split(os.pathsep)
        if shutil.which(name, path=entry) is None
    )
    assert shutil.which(name, path=path) is None, f"{name} is still on the path"
    return {**os.environ, "PATH": path}
