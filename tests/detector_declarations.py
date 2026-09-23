
from __future__ import annotations

JSCPD = '{ name = "jscpd", kind = "command", install = "npm i -D jscpd" }'
PMD = '{ name = "pmd", kind = "command", install = "brew install pmd" }'
TS_MORPH = '{ name = "ts-morph", kind = "node-module", install = "npm i -D ts-morph" }'


def declaring(*detectors: str) -> str:
    return f"detectors = [{', '.join(detectors)}]"
