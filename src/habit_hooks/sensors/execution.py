
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from ..path_globs import matching
from ..scope import Scope
from . import inline_run
from .broken_part import run_part
from .chunking import chunked_commands
from .command_text import expanded, spelled_files
from .deadline import DEFAULT_SENSOR_TIMEOUT_SECONDS
from .finding_paths import aliasing_notices, anchored
from .live_commands import LIVE_COMMANDS
from .model import Part, Run, SensorError
from .part_output import parse_findings, part_failure, sensor_crashed
from .spawn import Spawner


@dataclass(frozen=True)
class Execution:
    project_dir: Path
    scope: Scope
    config_path: Path | None = None
    timeout: float = DEFAULT_SENSOR_TIMEOUT_SECONDS

    def run_sensors(self, sensors: list[Part]) -> Run:
        scoped = [sensor for sensor in sensors if self._scoped_files(sensor)]
        if not scoped:
            return Run()
        run = Run()
        for findings, notices in self._sensor_outputs(scoped):
            run.findings.extend(findings)
            run.notices.extend(notices)
        return run

    def _sensor_outputs(self, scoped: list[Part]) -> list[tuple[list[dict], list[str]]]:
        with ThreadPoolExecutor(max_workers=len(scoped)) as pool:
            try:
                return list(pool.map(self._safe_sensor, scoped))
            except KeyboardInterrupt:
                LIVE_COMMANDS.interrupt()
                raise

    def apply_transformers(
        self, transformers: list[Part], findings: list[dict]
    ) -> tuple[list[dict], list[str]]:
        notices = []
        for transformer in transformers:
            try:
                findings = self._transform(transformer, findings)
            except SensorError as error:
                notices.append(f"habit-sensors: {error}")
        return findings, notices

    def _transform(self, transformer: Part, findings: list[dict]) -> list[dict]:
        argv = self._expand(transformer)
        payload = json.dumps(findings)
        tools = transformer.tools_that_read_its_arguments
        result = run_part(
            "transformer", transformer, lambda: self._spawner.run(argv, payload, tools=tools)
        )
        failure = part_failure("transformer", transformer, result)
        if result.returncode != 0 or not result.stdout.strip():
            raise failure
        try:
            return parse_findings(result.stdout)
        except (ValueError, json.JSONDecodeError):
            raise failure from None

    def run_sensor(self, sensor: Part) -> list[dict]:
        if sensor.inline is not None:
            return inline_run.findings_for(sensor, self)
        findings: list[dict] = []
        for argv in self._sensor_commands(sensor):
            findings.extend(self._sensor_findings(sensor, argv))
        return anchored(findings, self.project_dir, sensor.name)

    def _sensor_findings(self, sensor: Part, argv: list[str]) -> list[dict]:
        tools = sensor.tools_that_read_its_arguments
        result = run_part("sensor", sensor, lambda: self._spawner.run(argv, tools=tools))
        failure = part_failure("sensor", sensor, result)
        if sensor_crashed(result):
            raise failure
        try:
            return parse_findings(result.stdout)
        except (ValueError, json.JSONDecodeError):
            raise failure from None

    def _sensor_commands(self, sensor: Part) -> list[list[str]]:
        return chunked_commands(
            sensor, self._spelled_files(sensor), self._expander(sensor)
        )

    def _expander(self, part: Part):
        return lambda files: self._expand_files(part, files)

    def _safe_sensor(self, sensor: Part) -> tuple[list[dict], list[str]]:
        try:
            findings = self.run_sensor(sensor)
        except SensorError as error:
            return [], [f"habit-sensors: {error}"]
        return findings, [
            f"habit-sensors: {notice}"
            for notice in aliasing_notices(findings, sensor.name)
        ]

    def _expand(self, part: Part) -> list[str]:
        return self._expand_files(part, self._spelled_files(part))

    def _spelled_files(self, part: Part) -> list[str]:
        return spelled_files(part, self._scoped_files(part))

    def _expand_files(self, part: Part, files: list[str]) -> list[str]:
        return expanded(part, files, self.config_path)

    def _scoped_files(self, part: Part) -> list[str]:
        if part.files is None:
            return self.scope.files
        return matching(self.scope.files, part.files)

    @property
    def _spawner(self) -> Spawner:
        return Spawner(self.project_dir, self.timeout)
