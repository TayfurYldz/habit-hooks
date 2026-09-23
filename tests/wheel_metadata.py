
from __future__ import annotations

import re
import zipfile
from email import message_from_bytes
from pathlib import Path

EXTRA_MARKER = "extra =="


def built(wheels_dir: Path) -> dict[str, str]:
    return dict(_wheel_distribution(wheel) for wheel in sorted(wheels_dir.glob("*.whl")))


def required_from_elsewhere(wheels_dir: Path) -> list[str]:
    from_here = built(wheels_dir)
    return [
        requirement
        for wheel in sorted(wheels_dir.glob("*.whl"))
        for requirement in _requires_dist(wheel)
        if EXTRA_MARKER not in requirement
        and _required_distribution(requirement) not in from_here
    ]


def _wheel_distribution(wheel: Path) -> tuple[str, str]:
    name, version, *_ = wheel.name.split("-")
    return _distribution(name), version


def _distribution(name: str) -> str:
    return name.replace("_", "-").lower()


def _requires_dist(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        metadata = next(
            entry for entry in archive.namelist() if entry.endswith(".dist-info/METADATA")
        )
        return message_from_bytes(archive.read(metadata)).get_all("Requires-Dist") or []


def _required_distribution(requirement: str) -> str:
    return _distribution(re.split(r"[\[<>=!~; ]", requirement, maxsplit=1)[0])
